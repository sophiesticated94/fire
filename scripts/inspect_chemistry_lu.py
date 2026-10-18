"""Reconstruct exact inspected GPU Newton systems, independently solve in float64."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import cantera as ct

ROOT=Path(__file__).resolve().parents[1]


def inspect(data):
    reports, systems = [], []
    mechanism=ROOT/'src/gpu/chemistry/data/gri30.yaml'
    if hashlib.sha256(mechanism.read_bytes()).hexdigest()!=json.loads((ROOT/'src/gpu/chemistry/data/provenance.json').read_text())['sha256']:
        raise ValueError('Pinned GRI30 YAML integrity mismatch')
    gas=ct.Solution(str(ROOT/'src/gpu/chemistry/data/gri30.yaml'))
    def rhs(state):
        gas.TPY=state[0],ct.one_atm,state[1:]
        return np.r_[gas.enthalpy_mass,gas.net_production_rates*gas.molecular_weights/gas.density]
    for cell in range(data['count']):
        values = np.array(data['values'][cell*data['stride']:(cell+1)*data['stride']])
        jac = values[:2970].reshape(54,55)
        trial, work, ctl, status = values[2970:3024], values[3024:3294], values[3294:3334], values[3334:3342]
        base, delta = work[54:108], work[216:270]
        fd=np.empty((54,54));f0=rhs(trial)
        for col in range(54):
            h=1e-3 if col==0 else max(1e-12,abs(trial[col])*1e-5)
            plus=trial.copy();plus[col]+=h
            if col==0 or trial[col]>=h:
                minus=trial.copy();minus[col]-=h;fd[:,col]=(rhs(plus)-rhs(minus))/(2*h)
            else:
                twice=trial.copy();twice[col]+=2*h;fd[:,col]=(-3*f0+4*rhs(plus)-rhs(twice))/(2*h)
        row_floor=np.maximum(np.max(abs(fd),axis=1)*1e-6,1e-8)
        jac_error=float(np.max(abs(jac[:,:54]-fd)/np.maximum(abs(fd),row_floor[:,None])))
        scale = np.r_[1e-3,np.full(53,1e-12)]+1e-5*np.maximum(abs(trial),abs(base))
        row_scale = scale.copy()
        row_scale[0] = max(1.,abs(jac[0,0])*scale[0])
        a = np.eye(54)-ctl[2]*jac[:,:54]
        a[0] = jac[0,:54]
        a *= scale[None,:]/row_scale[:,None]
        b = -(trial-base-ctl[2]*jac[:,54])/row_scale
        energy_low=0.
        if data['layout'].get('low') is not None:
            low_count=data['layout'].get('lowCount',324)
            low=values[data['layout']['low']:data['layout']['low']+low_count]
            energy_low=low[270]-low[271]
            b=-(trial-base+low[:54]-low[108:162]-ctl[2]*jac[:,54])/row_scale
            if low_count>=325:b[1:]+=ctl[2]*low[272:325]/row_scale[1:]
        b[0] = -(jac[0,54]-ctl[3]+energy_low)/row_scale[0]
        # Probe consumes the exact representable float32 matrix, while the
        # float64 reconstruction additionally exposes matrix-assembly rounding.
        a32, b32 = a.astype(np.float32).astype(float), b.astype(np.float32).astype(float)
        solution = np.linalg.solve(a32,b32)
        gpu = delta/scale
        denom = np.linalg.norm(a32,np.inf)*np.linalg.norm(gpu,np.inf)+np.linalg.norm(b32,np.inf)
        reports.append(dict(cell=cell,dt=ctl[2],phase=ctl[8],nonlinearNorm=status[0],
            linearSolveRequired=bool(status[0]>.1*(ctl[39] if ctl[39]>0 else 1.)),gpuLuFailed=bool(status[1]),gpuReportedBackwardError=status[2],pivotRatio=status[3],
            canteraJacobianWeightedError=jac_error,sourceMassResidual=float(np.sum(jac[1:,54])),
            conditionInfinity=float(np.linalg.cond(a32,np.inf)),
            independentBackwardError=float(np.linalg.norm(a32@gpu-b32,np.inf)/max(1e-30,denom)),
            scaledSolutionRelativeError=float(np.linalg.norm(gpu-solution,np.inf)/max(1e-30,np.linalg.norm(solution,np.inf))),
            assemblyRelativeError=float(np.linalg.norm(a-a32,np.inf)/max(1e-30,np.linalg.norm(a,np.inf)))))
        systems.append(np.column_stack([a32,b32]).ravel().tolist())
    return dict(method='float64 solve of inspected float32 scaled matrix; no CPU chemistry integration',reports=reports,systems=systems)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=inspect(json.loads(args.input.read_text(encoding='utf-8')))
    args.output.write_text(json.dumps(result,allow_nan=False),encoding='utf-8')
    print(json.dumps(result['reports']))
