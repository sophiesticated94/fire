"""Independent float64 audit. Cantera never supplies a GPU chemistry state.

Input: {caseIds: [...], checkpoint: TileCheckpoint}. Inspect *every* reached
reactor and sample, including partial runs. Physical times are rounded to the
actual float32 schedule before ReactorNet.advance(t).
"""
import argparse
import json
from pathlib import Path

import cantera as ct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def validate(payload):
    if ct.__version__ != '3.2.0':
        raise ValueError('Cantera 3.2.0 is required')
    fixtures = json.loads((ROOT / 'tests/gpu/reactor-fixtures.json').read_text())['cases']
    cp = payload['checkpoint']
    expected_hash = json.loads((ROOT / 'src/gpu/chemistry/data/provenance.json').read_text())['sha256']
    if cp['mechanismSha256'] != expected_hash or cp['precision'] != 'float32':
        raise ValueError('Unsupported mechanism or precision')
    reports = []
    for cell, case_id in enumerate(payload['caseIds']):
        fixture = fixtures[case_id]
        initial = np.array(cp['initial'][cell])
        if not np.array_equal(initial, fixture['initial']):
            raise ValueError('Fixture identity mismatch')
        ctl = cp['control'][cell*40:(cell+1)*40]
        count = int(ctl[20])
        gas = ct.Solution(str(ROOT / 'src/gpu/chemistry/data/gri30.yaml'))
        gas.TPY = initial[0], ct.one_atm, initial[1:]
        h0 = gas.enthalpy_mass
        elements = np.array([gas.elemental_mass_fraction(e) for e in gas.element_names])
        reactor = ct.IdealGasConstPressureReactor(gas, clone=True)
        network = ct.ReactorNet([reactor])
        network.rtol, network.atol = 1e-10, 1e-20
        metrics = dict(temperatureWeighted=0., speciesWeighted=0., radicalWeighted=0.,
                       enthalpyFraction=0., elementsFraction=0., sumYError=0.)
        samples, gpu_ignition = [], None
        previous_t, previous_T = 0., initial[0]
        times = [float(np.float32(t)) for t in cp['sampleTimes'][:count]]
        actual = np.array(cp['trajectory']).reshape(len(cp['initial']), len(cp['sampleTimes']), 54)[cell, :count]
        observations = list(zip(times, actual))
        # The last accepted state is audited even before a full sample interval.
        if not times or ctl[0]-ctl[27] > times[-1]:
            observations.append((ctl[0]-ctl[27], np.array(cp['accepted'][cell])))
        for time, state in observations:
            network.advance(time)
            ref = np.array([reactor.T, *reactor.phase.Y])
            if not np.all(np.isfinite(state)) or np.any(state[1:] < 0):
                raise ValueError('Non-finite or negative accepted state')
            metrics['temperatureWeighted'] = max(metrics['temperatureWeighted'], abs(state[0]-ref[0])/max(1., .005*abs(ref[0]-initial[0])))
            metrics['speciesWeighted'] = max(metrics['speciesWeighted'], float(np.max(np.abs(state[1:]-ref[1:])/np.maximum(1e-4,.02*np.abs(ref[1:])))))
            radicals = np.array([gas.species_index(s)+1 for s in ['H','O','OH','HO2','CH3']])
            metrics['radicalWeighted'] = max(metrics['radicalWeighted'], float(np.max(np.abs(state[radicals]-ref[radicals])/(1e-12+.05*np.abs(ref[radicals])))))
            gas.TPY = state[0], ct.one_atm, state[1:]
            metrics['enthalpyFraction'] = max(metrics['enthalpyFraction'], abs(gas.enthalpy_mass-h0)/max(1.,abs(h0)))
            current = np.array([gas.elemental_mass_fraction(e) for e in gas.element_names])
            metrics['elementsFraction'] = max(metrics['elementsFraction'], float(np.max(abs(current-elements)/np.maximum(1e-30,abs(elements)))))
            metrics['sumYError'] = max(metrics['sumYError'], abs(float(state[1:].sum())-1))
            if gpu_ignition is None and state[0] >= initial[0]+400:
                gpu_ignition = previous_t+(time-previous_t)*(initial[0]+400-previous_T)/(state[0]-previous_T)
            previous_t, previous_T = time, state[0]
            oh = gas.species_index('OH')+1
            samples.append(dict(time=time, state=state.tolist(), reference=ref.tolist(), OH=float(state[oh]), referenceOH=float(ref[oh])))
        limits = dict(temperatureWeighted=1., speciesWeighted=1., radicalWeighted=1., enthalpyFraction=1e-5, elementsFraction=1e-5, sumYError=1e-5)
        point_pass = all(metrics[k] <= limits[k] for k in limits)
        finished = (ctl[8] == 5 and count == len(cp['sampleTimes']) and cp['duration'] == fixture['horizon']
                    and ctl[0] == float(np.float32(fixture['horizon']))
                    and cp['sampleTimes'][-1] == fixture['horizon'])
        ignition_error = None
        if fixture['ignitionTime'] is not None and gpu_ignition is not None:
            ignition_error = abs(gpu_ignition-fixture['ignitionTime'])/fixture['ignitionTime']
        ignition_pass = (gpu_ignition is None) if fixture['ignitionCensored'] else (ignition_error is not None and ignition_error <= .05)
        peak = max((s['OH'] for s in samples),default=0.)
        ref_peak = max((s['referenceOH'] for s in samples),default=0.)
        peak_error = abs(peak-ref_peak)/max(1e-12,ref_peak)
        reports.append(dict(caseId=case_id, time=ctl[0]-ctl[27], complete=finished, metrics=metrics,
            pointPass=point_pass, ignitionTime=gpu_ignition, ignitionError=ignition_error,
            ignitionCensored=gpu_ignition is None, OHPeak=peak, OHPeakError=peak_error,
            accepted=int(ctl[14]), rejections=int(ctl[13]), samples=samples,
            status='FAIL' if not point_pass or (finished and (not ignition_pass or peak_error>.1)) else 'PASS' if finished else 'INCOMPLETE'))
    return dict(cantera=ct.__version__, source='independent float64 constant-pressure adiabatic reactor', reactors=reports,
                status='FAIL' if any(r['status']=='FAIL' for r in reports) else 'PASS' if all(r['status']=='PASS' for r in reports) else 'INCOMPLETE')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=validate(json.loads(args.input.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='reactors'}))
