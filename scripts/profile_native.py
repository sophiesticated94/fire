"""Separately budgeted detailed diagnostics, excluded from production timing."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.models import Experiment
from scripts.campaign_v3 import Campaign,BudgetStop,render
from scripts.report_steps import report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--scene',choices=['burner','candle','wood'],required=True)
    p.add_argument('--duration',type=float,required=True);p.add_argument('--mode',default='openmp');p.add_argument('--all-steps',action='store_true')
    p.add_argument('--hours',type=float,required=True);p.add_argument('--gib',type=float,required=True);a=p.parse_args()
    c=Campaign(a.root,a.hours,a.gib)
    try:
        try:
            result=c.execute(Experiment(scene=a.scene,duration=a.duration,fuel=1.2 if a.scene=='candle' else 12),a.mode,'step-profile',0,all_steps=a.all_steps)
            if a.all_steps and not result['stepProfile']['allStepsRecorded']:raise ValueError('Native all-step coverage is incomplete')
            c.state['status']='completed-profiling'
        except BudgetStop as exc:c.state.update(status='budget-stopped',stopReason=str(exc))
        c.save();render(c.state,c.root/'report.md');report(c.root,c.root/'step-report.md')
    finally:c.close()
