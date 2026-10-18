"""Prescribed GPU step schedule replayed with independent float64 BE.

No GPU state is replaced. The returned states are strictly audit artifacts.
"""
import time
import argparse
import json
from pathlib import Path
import numpy as np
from chemistry_forensics import BackwardEuler, TOL, RTOL, network, weighted


def replay(report, wall_seconds=120, refinement=1):
    if refinement not in [1,2,4,8,16]:
        raise ValueError('Unsupported schedule refinement')
    be=BackwardEuler();initial=np.array(report['initialAudit']['float32'])
    state=initial.copy();target=be.evaluate(state)[0]
    start=time.monotonic();rows=[];previous_time=0.
    for observation in report['observations']:
        if time.monotonic()-start>=wall_seconds:
            return dict(status='INCOMPLETE',reason='bounded reference deadline',rows=rows)
        dt=observation['dt']
        try:
            for _ in range(refinement*2):
                second=be.step(state,dt/(refinement*2),target)
                state=np.array(second['state'])
        except (ArithmeticError,np.linalg.LinAlgError) as error:
            return dict(status='INCOMPLETE',reason=str(error),rows=rows)
        rows.append(dict(time=observation['time'],dt=dt,
            scheduleTimeDefect=observation['time']-previous_time-dt,
            state=state.tolist(),
            errorAgainstReactorNet=weighted(state,observation['roundedReference'],initial[0]),
            errorAgainstGPU=weighted(observation['state'],state,initial[0])))
        previous_time=observation['time']
    return dict(status='PASS',refinement=refinement,meaning='prescribed schedule replay completed; not a chemistry acceptance',rows=rows)


def refinements(probe):
    """Same exact GPU input, independently refined BE vs ReactorNet."""
    be=BackwardEuler();base=np.array(probe['base']);dt=probe['dt']
    # Cantera normalizes Y on assignment. The BE extension preserves the raw
    # sum, so compare its exact constant-sum extension, not a shifted initial Y.
    total=base[1:].sum()
    net,reactor=network(base);net.advance(dt/total);reference=np.r_[reactor.T,reactor.phase.Y*total]
    rows=[];target=be.evaluate(base)[0]
    for count in [1,2,4,8]:
        state=base.copy()
        for _ in range(count):state=np.array(be.step(state,dt/count,target)['state'])
        rows.append(dict(substeps=count,state=state.tolist(),
                         weightedError=float(np.max(abs(state-reference)/(TOL+RTOL*np.maximum(abs(state),abs(reference)))))))
    return dict(base=base.tolist(),dt=dt,reference=reference.tolist(),rows=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--wall-seconds',type=float,default=180)
    p.add_argument('--refinement',type=int,default=1)
    args=p.parse_args();report=json.loads(args.input.read_text(encoding='utf-8'))
    report['prescribedSchedule']=replay(report,args.wall_seconds,args.refinement)
    # Match the difficult window, not just the almost inert initial state.
    report['timeRefinement']=[refinements(x) for x in report['probes'] if .001 <= x['time'] <= .00115]
    args.output.write_text(json.dumps(report,allow_nan=False),encoding='utf-8')
    replayed=report['prescribedSchedule']
    print(json.dumps(dict(status=replayed['status'],steps=len(replayed['rows']),last=replayed['rows'][-1] if replayed['rows'] else None)))
