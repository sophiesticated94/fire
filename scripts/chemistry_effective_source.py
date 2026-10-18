"""Audit the actual coupled shader RHS, including saved low-part corrections."""
import argparse
import hashlib
import json
from pathlib import Path
import cantera as ct
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
THRESHOLD=.001
FLOOR=1e-8


def inspect_source(snapshot):
    if ct.__version__!='3.2.0':raise ValueError('Cantera 3.2.0 required')
    mechanism=ROOT/'src/gpu/chemistry/data/gri30.yaml'
    expected=json.loads((ROOT/'src/gpu/chemistry/data/provenance.json').read_text())['sha256']
    if hashlib.sha256(mechanism.read_bytes()).hexdigest()!=expected:raise ValueError('Pinned GRI30 YAML integrity mismatch')
    if not isinstance(snapshot.get('count'),int) or not 1<=snapshot['count']<=4 or snapshot.get('stride',0)<3342 or len(snapshot.get('values',[]))!=snapshot['count']*snapshot['stride']:
        raise ValueError('Incomplete inspection is not a numerical comparison')
    gas=ct.Solution(str(mechanism))
    reports=[]
    for cell in range(snapshot['count']):
        data=np.array(snapshot['values'][cell*snapshot['stride']:(cell+1)*snapshot['stride']])
        jac=data[:2970].reshape(54,55)
        state=data[2970:3024].copy()
        source=jac[1:,54].copy()
        if snapshot['layout'].get('low') is not None:
            start=snapshot['layout']['low'];count=snapshot['layout'].get('lowCount',324)
            if count not in [324,328] or start<3342 or start+count>snapshot['stride']:raise ValueError('Incomplete low-part inspection')
            low=data[start:start+count];state+=low[:54]
            if count>=325:source+=low[272:325]
        if np.any(~np.isfinite(state)) or np.any(state[1:]<0):raise ValueError('Invalid inspected state')
        gas.TPY=state[0],ct.one_atm,state[1:]
        reference=gas.net_production_rates*gas.molecular_weights/gas.density
        errors=abs(source-reference)/np.maximum(abs(reference),FLOOR)
        worst=int(np.argmax(errors))
        reports.append(dict(cell=cell,state=state.tolist(),source=source.tolist(),reference=reference.tolist(),
            baseTime=float(data[3294]-data[3294+27]),substep=int(data[3294+9]),
            worstSpecies=gas.species_names[worst],weightedError=float(errors[worst]),
            absoluteError=float(abs(source[worst]-reference[worst])),referenceAtWorst=float(reference[worst]),
            status='PASS' if np.all(errors<=THRESHOLD) else 'FAIL'))
    return dict(cantera=ct.__version__,units='mass fraction / s',threshold=THRESHOLD,absoluteFloor=FLOOR,
        source='independent Cantera on exact inspected high+low state; effective GPU high+low RHS',
        status='PASS' if reports and all(r['status']=='PASS' for r in reports) else 'FAIL',reports=reports)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();raw=args.input.read_bytes();r=inspect_source(json.loads(raw))
    r['inputName']=args.input.name;r['inputSha256']=hashlib.sha256(raw).hexdigest()
    args.output.write_text(json.dumps(r,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(status=r['status'],reports=[{k:x[k] for k in ['worstSpecies','weightedError','absoluteError','referenceAtWorst']} for x in r['reports']])))
