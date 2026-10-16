"""Empirical parameter boxes. Performance interpolation is never validation."""
import json
from itertools import product
from pathlib import Path
import numpy as np
from .models import Experiment
from .policy import VALIDATION_VERSION

REGISTRY=Path(__file__).resolve().parent.parent/'artifacts/validated-families-v3.json'
BOXES={
 'candle':dict(fuel=[.96,1.44],oxygen=[20,21.5],wind=[0,.1]),
 'burner':dict(fuel=[9.6,14.4],oxygen=[20,21.5],wind=[0,.1]),
 'wood':dict(moisture=[6,18],oxygen=[20,21.5],wind=[0,.1]),
}

def family_points(scene,duration):
    if duration not in ([15] if scene=='wood' else [2,6]):raise ValueError('Unverified family duration')
    bounds=BOXES[scene];keys=list(bounds);rng=np.random.default_rng(20261016)
    unit=list(product((0.,1.),repeat=3))+[(.5,.5,.5)]
    latin=np.column_stack([(rng.permutation(8)+rng.random(8))/8 for _ in keys]);unit.extend(latin)
    return [Experiment(scene=scene,duration=duration,quality='preview',**{k:float(bounds[k][0]+p[i]*(bounds[k][1]-bounds[k][0])) for i,k in enumerate(keys)}).canonical() for p in unit]

def resolve_family(exe,config,policy):
    if not policy['approved'] or config.quality!='preview':return None
    from .profiles import build_profile,validation_signature,hardware_id
    from .models import MODEL_VERSION,SOLVER_VERSION
    try:entries=json.loads(REGISTRY.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None
    if not isinstance(entries,list):return None
    choices=[];requested=config.canonical()
    for entry in entries:
        try:
            scene=entry['scene'];duration=entry['duration']
            if scene!=config.scene or duration!=config.duration or entry['bounds']!=BOXES[scene]:continue
            if entry['validationVersion']!=VALIDATION_VERSION or entry['policyHash']!=policy['hash'] or entry['hardware']!=hardware_id():continue
            if entry['model']!=MODEL_VERSION or entry['solver']!=SOLVER_VERSION:continue
            points=family_points(scene,duration);fixed=points[0]
            if any(requested[k]!=fixed[k] for k in fixed if k not in BOXES[scene]):continue
            if not all(lo<=requested[k]<=hi for k,(lo,hi) in BOXES[scene].items()):continue
            p=build_profile(exe,entry['mode'],threads=4)
            if p.identity()!=entry['profile']:continue
            evidence=entry['points']
            if len(evidence)!=len(points):continue
            valid=True
            for point in points:
                matches=[e for e in evidence if e['config']==point]
                if len(matches)!=1:valid=False;break
                e=matches[0]
                if not(e['passed'] is True and e['nativeExact'] is True and e['measuredRuns']>=3 and e['referenceRuns']>=3 and e['speedup']>=1/.95
                       and e['signature']==validation_signature(Experiment(**point),p)):valid=False;break
            if valid:choices.append((min(e['speedup'] for e in evidence),p))
        except (KeyError,ValueError,TypeError,OSError):continue
    return max(choices,key=lambda item:item[0])[1] if choices else None
