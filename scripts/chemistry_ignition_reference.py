"""Independent RHS/Jacobian at actual ignition trial states."""
import argparse
import json
from pathlib import Path
import numpy as np
from chemistry_forensics import BackwardEuler


def prepare(report):
    probes=[p for p in report['probes'] if p['time']>=.0008]
    states=[report['initialAudit']['float32'],*[p['gpuState'] for p in probes]]
    return dict(states=states,times=[0.,*[p['time'] for p in probes]],
                source='actual GPU initial and Newton trial readbacks; no trajectory substitution')


def audit(data):
    be=BackwardEuler()
    def rhs(state):
        f=be.evaluate(state)
        h=be.gas.partial_molar_enthalpies/be.gas.molecular_weights
        f[0]=-np.dot(h,f[1:])/be.gas.cp_mass
        return f
    def jacobian(state,factor):
        state=np.array(state);f0=rhs(state);j=np.empty((54,54))
        for col in range(54):
            step=factor*(1e-3 if col==0 else max(1e-13,abs(state[col])*1e-4))
            plus=state.copy();plus[col]+=step
            if col==0 or state[col]>=step:
                minus=state.copy();minus[col]-=step
                j[:,col]=(rhs(plus)-rhs(minus))/(2*step)
            else:
                twice=state.copy();twice[col]+=2*step
                j[:,col]=(-3*f0+4*rhs(plus)-rhs(twice))/(2*step)
        return j
    result=[]
    for cell,state in enumerate(data['states']):
        state=np.asarray(state);ref=rhs(state);jac=jacobian(state,1.);half=jacobian(state,.5)
        gpu=np.array(data['values'][cell*2970:(cell+1)*2970]).reshape(54,55)
        floor=np.maximum(np.max(abs(half),axis=1)*1e-6,1e-8)
        denom=np.maximum(abs(half),floor[:,None])
        result.append(dict(time=data['times'][cell],state=state.tolist(),
            rhsWeighted=float(np.max(abs(gpu[:,54]-ref)/np.maximum(abs(ref),1e-8))),
            jacobianWeighted=float(np.max(abs(gpu[:,:54]-half)/denom)),
            fdSensitivityWeighted=float(np.max(abs(jac-half)/denom)),
            rhsReference=ref.tolist(),jacobianReference=half.ravel().tolist(),gpu=gpu.ravel().tolist()))
    rhs_status='PASS' if all(r['rhsWeighted']<=.001 for r in result) else 'FAIL'
    jac_status='INCOMPLETE' if any(r['fdSensitivityWeighted']>.001 for r in result) else 'PASS' if all(r['jacobianWeighted']<=.001 for r in result) else 'FAIL'
    return dict(source=data['source'],adapter=data['adapter'],hardware=data['hardware'],
                threshold=.001,states=result,
                rhsStatus=rhs_status,jacobianStatus=jac_status,
                status='FAIL' if rhs_status=='FAIL' or jac_status=='FAIL' else jac_status)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','audit']);p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();data=json.loads(a.input.read_text(encoding='utf-8'))
    result=prepare(data) if a.mode=='prepare' else audit(data)
    a.output.write_text(json.dumps(result,allow_nan=False),encoding='utf-8')
    if a.mode=='audit':print(json.dumps({k:result[k] for k in ['status','threshold']}))
