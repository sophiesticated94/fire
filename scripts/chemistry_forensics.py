"""Independent float64 BE for diagnosis only; never supplies a GPU accepted state.

The algebraic temperature row enforces total enthalpy. Species rows use the
same normalized-Y extension as WGSL. Finite differences are independent of AD.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cantera as ct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOL = np.r_[1e-3, np.full(53, 1e-12)]
RTOL = 1e-5
SPECIES = json.loads((ROOT/'src/gpu/chemistry/data/mechanism.json').read_text())['species']
RADICALS = np.array([SPECIES.index(s)+1 for s in ['H', 'O', 'OH', 'HO2', 'CH3']])


class BackwardEuler:
    def __init__(self):
        if ct.__version__ != '3.2.0':
            raise ValueError('Cantera 3.2.0 required')
        mechanism=ROOT/'src/gpu/chemistry/data/gri30.yaml'
        if hashlib.sha256(mechanism.read_bytes()).hexdigest()!=json.loads((ROOT/'src/gpu/chemistry/data/provenance.json').read_text())['sha256']:
            raise ValueError('Pinned GRI30 YAML integrity mismatch')
        self.gas = ct.Solution(str(ROOT/'src/gpu/chemistry/data/gri30.yaml'))

    def evaluate(self, state):
        self.gas.TPY = state[0], ct.one_atm, state[1:]
        return np.r_[self.gas.enthalpy_mass,
                     self.gas.net_production_rates*self.gas.molecular_weights/self.gas.density]

    def jacobian(self, state, factor=1.):
        state = np.array(state, dtype=float)
        f0 = self.evaluate(state)
        jac = np.empty((54, 54))
        for col in range(54):
            h = factor*(1e-3 if col == 0 else max(1e-13, abs(state[col])*1e-4))
            plus = state.copy(); plus[col] += h
            if col == 0 or state[col] >= h:
                minus = state.copy(); minus[col] -= h
                jac[:, col] = (self.evaluate(plus)-self.evaluate(minus))/(2*h)
            else:
                twice = state.copy(); twice[col] += 2*h
                jac[:, col] = (-3*f0+4*self.evaluate(plus)-self.evaluate(twice))/(2*h)
        return jac

    def residual(self, state, base, dt, target):
        f = self.evaluate(state)
        r = state-base-dt*f
        r[0] = f[0]-target
        scale = TOL+RTOL*np.maximum(abs(state), abs(base))
        scale[0] = max(1., self.gas.cp_mass*scale[0])
        return r, scale

    def step(self, base, dt, target=None, fd_factor=1.):
        base = np.asarray(base, dtype=float)
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError('dt must be positive')
        target = self.evaluate(base)[0] if target is None else target
        state = base.copy()
        history = []
        for iteration in range(40):
            r, scale = self.residual(state, base, dt, target)
            norm = float(np.sqrt(np.mean((r/scale)**2)))
            if norm <= 1e-4:
                return dict(state=state.tolist(), norm=norm, history=history, dt=dt,
                            targetEnthalpy=float(target))
            df = self.jacobian(state, fd_factor)
            jac = np.eye(54)-dt*df
            jac[0] = df[0]
            unknown_scale = TOL+RTOL*np.maximum(abs(state), abs(base))
            scaled = jac*unknown_scale[None, :]/scale[:, None]
            delta = np.linalg.solve(scaled, -r/scale)*unknown_scale
            alpha = 1.
            negative = delta[1:] < 0
            if np.any(negative):
                # Small negative roundoff is permitted only within the GPU
                # positivity budget, then measured and clipped explicitly.
                bounds = (state[1:][negative]+1e-16)/(-delta[1:][negative])
                alpha = min(alpha, float(np.min(bounds))*.99)
            accepted = False
            for damping in range(24):
                trial = state+alpha*delta
                correction = float(np.max(np.maximum(-trial[1:], 0)/(TOL[1:]+RTOL*abs(state[1:]))))
                if 300 <= trial[0] <= 3000 and correction <= .1:
                    trial[1:] = np.maximum(trial[1:], 0)
                    rr, ss = self.residual(trial, base, dt, target)
                    trial_norm = float(np.sqrt(np.mean((rr/ss)**2)))
                    if trial_norm < norm:
                        accepted = True; break
                alpha *= .5
            history.append(dict(iteration=iteration, norm=norm, alpha=alpha,
                                damping=damping, positivityCorrection=correction))
            if not accepted:
                raise ArithmeticError(f'Float64 BE damping failed, norm={norm}')
            state = trial
        raise ArithmeticError('Float64 BE Newton limit')

    def doubled(self, base, dt, target=None):
        target = self.evaluate(base)[0] if target is None else target
        full = self.step(base, dt, target)
        first = self.step(base, dt/2, target)
        second = self.step(first['state'], dt/2, target)
        a, b = np.array(full['state']), np.array(second['state'])
        error = float(np.max(abs(a-b)/(TOL+RTOL*np.maximum(abs(a), abs(b)))))
        return dict(full=full, firstHalf=first, secondHalf=second,
                    estimator=error, accepted=error <= 1.)


def weighted(state, ref, initial_temperature):
    state, ref = np.asarray(state), np.asarray(ref)
    return dict(temperature=float(abs(state[0]-ref[0])/max(1., .005*abs(ref[0]-initial_temperature))),
                species=float(np.max(abs(state[1:]-ref[1:])/np.maximum(1e-4, .02*abs(ref[1:])))),
                radicals=float(np.max(abs(state[RADICALS]-ref[RADICALS])/(1e-12+.05*abs(ref[RADICALS])))))


def trace_records(data):
    """Read bounded chunks; verify file integrity without one giant JSON string."""
    if 'records' in data:
        yield from data['records']; return
    for entry in data['traceFiles']:
        raw = Path(entry['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Trace chunk integrity mismatch')
        envelope=json.loads(raw)
        marker=b'"payload":'
        payload=raw[raw.index(marker)+len(marker):-1]
        if envelope.get('schema')!=1 or hashlib.sha256(payload).hexdigest()!=envelope.get('sha256'):
            raise ValueError('Trace chunk envelope integrity mismatch')
        chunk = envelope['payload']
        if chunk['dropped']:
            raise ValueError('Trace is truncated')
        yield from chunk['records']


def paired_records(data):
    previous = None
    expected = 0
    for rec in trace_records(data):
        if rec['sequence'] != expected:
            raise ValueError('Trace is truncated, duplicated or reordered')
        expected += 1
        if previous is not None:
            yield previous, rec['control'][14] > previous['control'][14]
        previous = rec
    if previous is not None:
        yield previous, False


def network(initial):
    gas = ct.Solution(str(ROOT/'src/gpu/chemistry/data/gri30.yaml'))
    gas.TPY = initial[0], ct.one_atm, initial[1:]
    reactor = ct.IdealGasConstPressureReactor(gas, clone=True)
    net = ct.ReactorNet([reactor]); net.rtol = 1e-10; net.atol = 1e-20
    return net, reactor


def analyze(data, max_probes=12):
    """Audit every converged substep; expensive FD/BE replay is bounded."""
    be = BackwardEuler()
    original = np.array(data['initial'], dtype=float)
    initial = np.array(data['gpuInitial'], dtype=float)
    if not np.array_equal(initial, original.astype(np.float32).astype(float)):
        raise ValueError('GPU initial readback differs from uploaded float32 state')
    initial_audit = dict(original=original.tolist(), float32=initial.tolist(),
                         difference=(initial-original).tolist(), sumY=float(initial[1:].sum()),
                         enthalpyOriginal=float(be.evaluate(original)[0]),
                         enthalpyFloat32=float(be.evaluate(initial)[0]))
    nets = [network(original), network(initial)]
    observations, converged = [], []
    accepted_events=0
    for rec, actually_accepted in paired_records(data):
        accepted_events+=int(actually_accepted)
        c = rec['control']; phase = int(c[8])
        if phase not in (1, 3) or c[19] != 1:
            continue
        state = np.array(rec['state']); base = np.array(rec['work'][54:108])
        f = np.array(rec['rhs']); dt = c[2]
        scales = TOL+RTOL*np.maximum(abs(state), abs(base))
        residual = state-base-dt*f; residual[0] = f[0]-c[3]
        scales[0] = max(1., abs(rec['enthalpyDerivative'])*scales[0])
        gpu_norm = float(np.sqrt(np.mean((residual/scales)**2)))
        if gpu_norm > .1 or (phase == 3 and c[22] > .1) or np.any(state[1:] < 0):
            continue
        if phase == 1 and rec['linear'][1] > 0:
            continue
        converged.append((rec, gpu_norm))
        # Only the second half-step can become an accepted physical state.
        if c[9] != 2 or not actually_accepted:
            continue
        full = np.array(rec['work'][162:216])
        estimator = float(np.max(abs(state-full)/(TOL+RTOL*np.maximum(abs(state), abs(full)))))
        if estimator > 1:
            continue
        time = c[0]-c[27]+dt*2
        refs = []
        for net, reactor in nets:
            net.advance(time); refs.append(np.r_[reactor.T, reactor.phase.Y])
        item = dict(sequence=rec['sequence'], time=time, dt=dt*2, gpuNorm=gpu_norm,
                    estimator=estimator, state=state.tolist(), reference=refs[0].tolist(),
                    roundedReference=refs[1].tolist(), metrics=weighted(state, refs[0], original[0]),
                    initialRoundingEffect=weighted(refs[1], refs[0], original[0]))
        reference_source=be.evaluate(state)
        source_errors=abs(f[1:]-reference_source[1:])/np.maximum(abs(reference_source[1:]),1e-8)
        worst=int(np.argmax(source_errors))
        item.update(rhsWeighted=float(source_errors[worst]),rhsWorstSpecies=SPECIES[worst])
        observations.append(item)
    first = next((s for s in observations if max(s['metrics'].values()) > 1), None)
    first_source=next((s for s in observations if s['rhsWeighted']>.001),None)
    # Deterministic selection across the window, including the first failure.
    selected = set(np.linspace(0, max(0, len(converged)-1), min(max_probes, len(converged)), dtype=int).tolist())
    if first:
        selected.add(next(i for i, (r, _) in enumerate(converged) if r['sequence'] == first['sequence']))
    probes = []
    for index in sorted(selected):
        rec, gpu_norm = converged[index]; c = rec['control']
        state = np.array(rec['state']); base = np.array(rec['work'][54:108]); dt = c[2]
        reference_rhs = be.evaluate(state)
        r, scale = be.residual(state, base, dt, c[3])
        result = dict(sequence=rec['sequence'], time=c[0]-c[27], substep=int(c[9]), dt=dt,
                      base=base.tolist(), gpuState=state.tolist(), targetEnthalpy=c[3], gpuNorm=gpu_norm,
                      independentNorm=float(np.sqrt(np.mean((r/scale)**2))),
                      rhsDifference=(np.array(rec['rhs'])-reference_rhs).tolist())
        try:
            exact = be.step(base, dt, c[3])
            sensitivity = be.step(base, dt, c[3], fd_factor=.5)
            result.update(float64BE=exact, stepWeightedError=float(np.max(abs(state-np.array(exact['state']))/(TOL+RTOL*np.maximum(abs(state), abs(base))))),
                          fdSensitivityWeighted=float(np.max(abs(np.array(exact['state'])-sensitivity['state'])/(TOL+RTOL*abs(base)))))
        except (ArithmeticError, np.linalg.LinAlgError) as error:
            result['referenceError'] = str(error)
        probes.append(result)
    return dict(schema=1,acceptanceStatus='FAIL' if first else 'INCOMPLETE',diagnosisStatus='UNRESOLVED',
                historicalAcceptanceStatus='FAIL',cantera=ct.__version__,initialAudit=initial_audit,
                observations=observations,firstExceedance=first,firstSourceExceedance=first_source,probes=probes,
                completeTrace=not data.get('dropped', 0),
                completeAcceptedCoverage=len(observations)==accepted_events,acceptedEventsSeen=accepted_events,
                note='Partial diagnostic window never promotes the full GRI30 gate.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('input', type=Path); p.add_argument('output', type=Path)
    p.add_argument('--max-probes', type=int, default=12)
    args = p.parse_args()
    report = analyze(json.loads(args.input.read_text(encoding='utf-8')), args.max_probes)
    args.output.write_text(json.dumps(report, allow_nan=False), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['acceptanceStatus', 'diagnosisStatus']}))
