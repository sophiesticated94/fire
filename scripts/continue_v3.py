"""One-shot continuation of this research campaign, retaining its original budget.

Wait for an already running campaign, verify updated code while FDS is idle,
repair derived profiling, then resume missing trials with the same limits.
This is not a scheduler and never changes the scientific approval policy.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))


def read_state(root):return json.loads((root/'campaign.json').read_text(encoding='utf-8'))


def run_tree(args,timeout,log_path):
    from backend.runner import ProcessTree
    command=([os.environ.get('COMSPEC','C:/Windows/System32/cmd.exe'),'/d','/c']+args) if args[0].endswith('.cmd') else args
    with log_path.open('wb') as log:
        tree=ProcessTree()
        try:
            tree.start(command,ROOT,os.environ.copy(),log);deadline=time.monotonic()+timeout
            while tree.poll() is None:
                if time.monotonic()>deadline:raise TimeoutError('Continuation stage timeout')
                time.sleep(.2)
            return tree.wait()
        finally:
            try:
                if not tree.stopped:
                    tree.terminate()
                    if tree.pid:tree.wait()
            finally:tree.close()


def wait_owner(pid,root,hours):
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];api.OpenProcess.restype=w.HANDLE
    api.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];api.WaitForSingleObject.restype=w.DWORD
    api.CloseHandle.argtypes=[w.HANDLE];api.CloseHandle.restype=w.BOOL
    handle=api.OpenProcess(0x100000,False,pid)
    if not handle:
        if ctypes.get_last_error()==87:return
        raise ctypes.WinError(ctypes.get_last_error())
    deadline=time.monotonic()+max(0,hours*3600-read_state(root)['usedSeconds']);last=time.monotonic()-60
    try:
        while True:
            result=api.WaitForSingleObject(handle,5000)
            if result==0:return
            if result!=0x102:raise ctypes.WinError(ctypes.get_last_error())
            if time.monotonic()>deadline:raise TimeoutError('Original campaign budget elapsed while waiting')
            if time.monotonic()-last>=60:
                s=read_state(root);a=s.get('active')
                print(f"WAIT completed={len(s['runs'])} active={a['mode'] if a else '-'} {a['phase'] if a else '-'} wall={s['usedSeconds']/3600:.2f}h",flush=True)
                last=time.monotonic()
    finally:
        if not api.CloseHandle(handle):raise ctypes.WinError(ctypes.get_last_error())


def run_checks(root,hours,gib):
    started=time.monotonic();results={};remaining=hours*3600-read_state(root)['usedSeconds']
    commands=[('python',[sys.executable,'-m','pytest','tests','-q']),('build',['npm.cmd','run','build']),('browser',['npm.cmd','run','test:e2e'])]
    try:
        for name,args in commands:
            timeout=min(1800,remaining-(time.monotonic()-started)-60)
            if timeout<=0:raise TimeoutError('Insufficient remaining campaign budget for verification')
            print('VERIFY',name,flush=True)
            results[name]=run_tree(args,timeout,ROOT/f'artifacts/{name}-v3-continuation.log')==0
            if not results[name]:raise RuntimeError(f'{name} checks failed; see artifacts/{name}-v3-continuation.log')
    finally:
        # The native runner was stopped during verification. Charge that time
        # once so changing sessions cannot silently reset the eight-hour cap.
        from scripts.campaign_v3 import Campaign
        c=Campaign(root,hours,gib)
        try:
            elapsed=time.monotonic()-started;c.wall_base+=elapsed
            c.state['verification']=dict(results=results,seconds=elapsed)
            c.state['continuationStatus']='verified' if len(results)==3 and all(results.values()) else 'verification-failed'
            c.state['events'].append(dict(kind='verification',chargedToWallBudget=True,seconds=elapsed))
            c.save()
        finally:c.close()
    return results


def repair(root,hours,gib):
    from scripts.campaign_v3 import Campaign
    from scripts.report_steps import report
    c=Campaign(root,hours,gib)
    try:
        profiles=report(c.root,ROOT/'docs/steps-v3.md')
        for r in c.state['runs']:r['stepProfile']=profiles[r['key']]
        c.save()
    finally:c.close()


def publish(root):
    import re
    from backend.policy import validation_policy
    from backend.progressive import atomic_json
    state=read_state(root);checks=state.get('verification',{}).get('results',{});counts={}
    for key in ('python','browser'):
        text=(ROOT/f'artifacts/{key}-v3-continuation.log').read_text(errors='replace')
        values=re.findall(r'(\d+) passed',text);counts[key]=int(values[-1]) if values else None
    policy=validation_policy()
    status=dict(version='execution-3',softwareChecks=checks,passedCounts=counts,nativeResearch=dict(status=state['status'],completedRuns=len(state['runs']),
                stopReason=state.get('stopReason'),usedWallSeconds=state['usedSeconds'],storedBytes=state['storedBytes'],summaries=state['summaries']),
                qualificationPolicy=policy['data'].get('status'),customBuild='not executed; compatible development toolchain missing')
    atomic_json(ROOT/'artifacts/verification-status-v3.json',status)
    lines=['# Końcowa weryfikacja pierwszej kampanii v3','',
           f"Python: {counts['python']} passed; build: {'PASS' if checks.get('build') else 'FAIL'}; Playwright: {counts['browser']} passed.",
           '',f"Natywne próby: {len(state['runs'])}, stan: {state['status']}, powód zatrzymania: {state.get('stopReason','—')}.",
           f"Czas pracy wraz z weryfikacją: {state['usedSeconds']/3600:.3f} h; dane: {state['storedBytes']/1024**3:.3f} GiB.",
           '',f"Polityka: {policy['data'].get('status')}. Zatwierdzenie nowych progów jest osobnym etapem; czasy i stare bramki nie wystarczają do promocji.",
           '','[Raport eksperymentów](benchmark-v3.md) · [Profilowanie kroków](steps-v3.md) · [Opis wykonania i ograniczeń](execution-v3.md)',
           '','Własnych kompilacji nie wykonano z powodu brakującego zgodnego toolchainu. Kampanie rodzin parametrów wymagają oddzielnych budżetów. To kryteria regresji demonstracji edukacyjnej, bez deklaracji walidacji inżynierskiej.']
    (ROOT/'docs/verification-v3-final.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--after-pid',type=int,required=True);p.add_argument('--root',type=Path,default=ROOT/'artifacts/campaign-v3')
    p.add_argument('--hours',type=float,default=8);p.add_argument('--gib',type=float,default=4);a=p.parse_args();a.root=a.root.resolve()
    wait_owner(a.after_pid,a.root,a.hours)
    if read_state(a.root)['status'] not in ('budget-stopped','completed-research'):raise RuntimeError('Previous campaign failed; inspect it before retrying')
    run_checks(a.root,a.hours,a.gib);repair(a.root,a.hours,a.gib)
    print('RESUME same original wall/data budget',flush=True)
    remaining=a.hours*3600-read_state(a.root)['usedSeconds']
    code=run_tree([sys.executable,str(ROOT/'scripts/campaign_v3.py'),'--root',str(a.root),'--hours',str(a.hours),'--gib',str(a.gib)],max(1,remaining+60),ROOT/'artifacts/campaign-v3-resumed.log')
    if code:raise RuntimeError('Resumed campaign failed; see artifacts/campaign-v3-resumed.log')
    repair(a.root,a.hours,a.gib)
    shutil.copy2(a.root/'report.md',ROOT/'docs/benchmark-v3.md')
    publish(a.root)
    print('DONE docs/benchmark-v3.md and docs/verification-v3-final.md; approval policy unchanged',flush=True)
