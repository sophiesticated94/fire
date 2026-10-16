"""Separately budgeted empirical family qualification; no inferred approvals."""
import argparse
import json
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.families import family_points,BOXES,REGISTRY
from backend.models import Experiment,MODEL_VERSION,SOLVER_VERSION
from backend.profiles import hardware_id
from backend.policy import validation_policy,VALIDATION_VERSION
from backend.validation_v3 import compare_v3
from backend.progressive import atomic_json
from scripts.campaign_v3 import Campaign,BudgetStop,render


def summarize(campaign,scene,duration,mode):
    policy=validation_policy();points=[];profile=None
    for config in family_points(scene,duration):
        group=[r for r in campaign.state['runs'] if r['config']==config and r['iteration']>0]
        ref=[r for r in group if r['phase']=='family-reference']
        candidate=[r for r in group if r['phase']=='family-candidate' and r['profile']['mode']==mode]
        if len(ref)!=3 or len(candidate)!=3:continue
        comparisons=[campaign.compare(a,b) for a in ref for b in candidate]
        repeatability=[campaign.compare(a,b) for i,a in enumerate(ref) for b in ref[i+1:]]
        profile=candidate[0]['profile']
        points.append(dict(config=config,signature=candidate[0]['signature'],measuredRuns=3,referenceRuns=3,
                           nativeExact=all(r['nativeExact'] for r in ref+candidate),
                           passed=all(v['promotionEligible'] for v in comparisons+repeatability),
                           speedup=statistics.median(r['totalSeconds'] for r in ref)/statistics.median(r['totalSeconds'] for r in candidate),
                           comparisons=comparisons,repeatability=repeatability))
    entry=dict(scene=scene,duration=duration,bounds=BOXES[scene],mode=mode,profile=profile,hardware=hardware_id(),model=MODEL_VERSION,solver=SOLVER_VERSION,
               validationVersion=VALIDATION_VERSION,policyHash=policy['hash'],points=points)
    complete=len(points)==17
    approved=bool(policy['approved'] and complete and all(p['passed'] and p['nativeExact'] and p['speedup']>=1/.95 for p in points))
    atomic_json(campaign.root/'family-report.json',dict(complete=complete,promotionEligible=approved,policyStatus=policy['data']['status'],entry=entry))
    if approved:
        previous=json.loads(REGISTRY.read_text()) if REGISTRY.exists() else []
        previous=[e for e in previous if (e['scene'],e['duration'],e['mode'])!=(scene,duration,mode)]
        atomic_json(REGISTRY,previous+[entry])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--scene',choices=list(BOXES),required=True)
    p.add_argument('--duration',type=float,required=True);p.add_argument('--mode',required=True)
    p.add_argument('--hours',type=float,required=True);p.add_argument('--gib',type=float,required=True);p.add_argument('--summary-only',action='store_true');a=p.parse_args()
    if a.mode=='openmp':p.error('Specify a candidate different from the OpenMP reference')
    c=Campaign(a.root,a.hours,a.gib)
    try:
        if not a.summary_only:
            try:
                for config in family_points(a.scene,a.duration):
                    for mode,phase in [('openmp','family-reference'),(a.mode,'family-candidate')]:
                        for i in range(4):c.execute(Experiment(**config),mode,phase,i)
                c.state['status']='completed-research'
            except BudgetStop as exc:c.state.update(status='budget-stopped',stopReason=str(exc))
        try:summarize(c,a.scene,a.duration,a.mode)
        except BudgetStop as exc:c.state.update(status='budget-stopped',stopReason=str(exc))
        c.save();render(c.state,c.root/'report.md')
    finally:c.close()
