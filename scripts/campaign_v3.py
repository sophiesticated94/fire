"""Budgeted, resumable research campaign. Pending v3 never promotes a profile."""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import time
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import Engine,ROOT,solver_path
from backend.models import Experiment,geometry
from backend.profiles import build_profile,validation_signature,REGISTRY,hardware_id,fingerprint
from backend.policy import validation_policy,VALIDATION_VERSION
from backend.progressive import atomic_json
from backend.run_data import archive_run,open_run
from backend.validation_v3 import compare_v3
from backend.diagnostics import profile_steps
from scripts.benchmark import run

EARLY=['mpi2-x2','mpi2-y2','mpi4-xy22']
LATER=['mpi4-x4','mpi4-y4','mpi2-z13','mpi2-z31','mpi4-z1124','mpi4-z4211','hybrid2x2-z','mpi2','mpi4']
CASES=[('burner',6),('wood',15)]

class BudgetStop(Exception):pass

def disk_bytes(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())

def estimated_bytes(config):
    # Native and exported seven-channel fields coexist until verified archival.
    return int(__import__('math').prod(geometry(config)[1])*7*4*(int(config.duration/.1)+2)*2*1.3+32*1024**2)

def exported_bytes(config):
    return __import__('math').prod(geometry(config)[1])*7*4*(int(config.duration/.1)+2)

def native_peak(config):
    working=estimated_bytes(config)
    # Zip coexists with native/export files until verification. Analysis has
    # its own guard after this phase, using the actual completed archive size.
    archive_bound=working//2+32*1024**2
    return archive_bound+working

class Campaign:
    def __init__(self,root,hours=8,gib=4):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'campaign.lock').open('a+b');self.lock.seek(0,2)
        if not self.lock.tell():self.lock.write(b'0');self.lock.flush()
        self.lock.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:self.lock.close();raise RuntimeError('This campaign is already running')
        self.path=self.root/'campaign.json';self.seconds=hours*3600;self.bytes=int(gib*1024**3)
        self.state=json.loads(self.path.read_text()) if self.path.exists() else dict(version=3,runs=[],events=[],status='ready',active=None,summaries=[])
        self.wall_base=self.state.get('usedWallSeconds',sum(r['campaignSeconds'] for r in self.state['runs'])+sum(e.get('seconds',0) for e in self.state['events']))
        self.wall_started=time.monotonic()
        if self.state.get('active'):
            active=self.state.pop('active');self.state['events'].append(dict(kind='interrupted',key=active['key'],seconds=active.get('elapsed',0),folder=active['folder']))
        self.exe=solver_path()
        if not self.exe:raise FileNotFoundError('FDS required')
        context=dict(hardware=hardware_id(),baseline=build_profile(self.exe,'openmp',threads=4).identity(),
                     mpi=build_profile(self.exe,'mpi4',threads=4).identity())
        if self.state.get('context',context)!=context:
            self.lock.close();raise ValueError('Campaign hardware/binaries changed; use a separate explicitly budgeted root')
        self.state['context']=context
    def close(self):
        try:self.save()
        finally:self.lock.close()
    def save(self):
        self.state.update(budget=dict(seconds=self.seconds,bytes=self.bytes),usedWallSeconds=self.used_seconds(),usedSeconds=self.used_seconds(),storedBytes=disk_bytes(self.root))
        atomic_json(self.path,self.state)
    def used_seconds(self):return self.wall_base+time.monotonic()-self.wall_started
    def key(self,c,p,phase,iteration,transport='direct'):return hashlib.sha256(json.dumps(dict(signature=validation_signature(c,p),phase=phase,iteration=iteration,transport=transport),sort_keys=True).encode()).hexdigest()
    def execute(self,c,mode,phase,iteration,transport='direct',all_steps=False):
        p=build_profile(self.exe,mode,threads=4)
        if all_steps:
            if transport!='direct':raise ValueError('All-step profiling uses the direct runner, not the production API profile')
            from dataclasses import replace
            p=replace(p,diagnostics='flux-1-allsteps')
        key=self.key(c,p,phase,iteration,transport)
        existing=next((r for r in self.state['runs'] if r['key']==key),None)
        if existing:return existing
        estimate=estimated_bytes(c);remaining=self.seconds-self.used_seconds()-300
        prior=[r['totalSeconds'] for r in self.state['runs'] if r['config']==c.canonical() and r['profile']==p.identity()]
        expected=(max(prior)*1.2) if prior else (1200 if c.scene=='wood' else 1000)
        if remaining<expected:raise BudgetStop('time reservation')
        # Reserve only this phase. Before analysis, the exact new archive size
        # is known and a separate scratch guard applies. Reserving its loose
        # upper bound together with scratch needlessly rejects complete trials.
        peak=native_peak(c)
        if disk_bytes(self.root)+peak>self.bytes or shutil.disk_usage(self.root).free<peak+3*1024**3:raise BudgetStop('native/export/archive disk reservation')
        attempt=uuid.uuid4().hex;folder=self.root/'work'/attempt
        self.state.update(status='running',active=dict(key=key,folder=str(folder),mode=mode,config=c.canonical(),phase=phase,iteration=iteration,elapsed=0));self.save()
        started=time.monotonic();lease=Engine()
        print(f'START {c.scene} {c.duration}s {mode} {phase} {iteration}',flush=True)
        def heartbeat(elapsed,folder):
            self.state['active'].update(elapsed=elapsed,folder=str(folder));self.save()
        try:
            if transport=='api':
                from scripts.api_benchmark import run_api
                result=run_api(c,p,self.root/'work',min(7200,remaining),attempt=attempt,on_progress=heartbeat)
            else:
                lease._lease()
                result=run(c,p,self.root/'work',min(7200,remaining),attempt=attempt,on_progress=heartbeat)
            folder=Path(result['folder'])
            native_seconds=time.monotonic()-started
            result['stepProfile']=profile_steps(folder)
            profile_json=folder/'profile-steps.json';atomic_json(profile_json,result['stepProfile'])
            archive_started=time.monotonic();receipt=archive_run(folder,self.root/'archives'/f'{attempt}.zip',cleanup_root=self.root/'work')
            result.update(folder=receipt['path'],archive=receipt,archiveSeconds=time.monotonic()-archive_started,campaignSeconds=native_seconds,
                          phase=phase,iteration=iteration,key=key)
            self.state['runs'].append(result);self.state['active']=None;self.save()
            print(f"DONE {result['totalSeconds']:.2f}s native exact; archive {receipt['bytes']/1024**2:.1f} MiB",flush=True)
            return result
        except BaseException as exc:
            self.state['events'].append(dict(kind='failed',key=key,seconds=time.monotonic()-started,folder=str(folder),error=str(exc)))
            self.state.update(active=None,status='failed');self.save();raise
        finally:lease._release()
    def screen_score(self,record):
        cached=record.get('screenScore')
        if cached and record.get('screenPolicyHash')==validation_policy()['hash']:return tuple(cached)
        references=[r for r in self.state['runs'] if r['phase']=='reference' and r['iteration']>0 and r['config']==record['config']]
        if len(references)!=3:raise ValueError('Reference triplet incomplete')
        # Full diagnostics versus each repeat; no trajectory alignment.
        comparisons=[self.compare(r,record) for r in references]
        worst=max(max(f['error']/f['limit'] for f in c['legacy']['fields']+c['legacy']['interfaces']) for c in comparisons)
        passed=all(c['promotionEligible'] if validation_policy()['approved'] else c['legacy']['passed'] for c in comparisons)
        score=(int(not passed),0 if passed else worst,record['totalSeconds'])
        record.update(screenScore=list(score),screenPolicyHash=validation_policy()['hash']);self.save();return score
    def compare(self,a,b):
        policy=validation_policy()
        code=[fingerprint(ROOT/'backend'/name) for name in ('validation_v3.py','validation.py')]
        key=hashlib.sha256(json.dumps([a['archive']['sha256'],b['archive']['sha256'],policy['hash'],code]).encode()).hexdigest()
        path=self.root/'comparisons'/f'{key}.json'
        if path.exists():return json.loads(path.read_text(encoding='utf-8'))
        if self.used_seconds()+60>self.seconds:raise BudgetStop('analysis time reservation')
        scratch=estimated_bytes(Experiment(**b['config']))+exported_bytes(Experiment(**a['config']))
        if disk_bytes(self.root)+scratch>self.bytes or shutil.disk_usage(self.root).free<scratch+3*1024**3:
            raise BudgetStop('analysis disk reservation after archival')
        result=compare_v3(a['folder'],b['folder'],self.root/'scratch')
        path.parent.mkdir(parents=True,exist_ok=True);atomic_json(path,result);self.save()
        return result
    def summarize(self):
        # A budget stop can occur between two scenes of the later screening
        # matrix. Evaluate every completed screen, even without a finalist.
        for record in self.state['runs']:
            if record['phase'] in ('screen','cpu-screen'):self.screen_score(record)
        groups=defaultdict(list)
        for r in self.state['runs']:
            if r['phase'] in ('reference','finalist') and r['iteration']>0:groups[json.dumps(r['signature'],sort_keys=True)].append(r)
        summaries=[];policy=validation_policy();receipts=[]
        for key,runs in groups.items():
            if len(runs)!=3:continue
            references=[r for r in self.state['runs'] if r['phase']=='reference' and r['iteration']>0 and r['config']==runs[0]['config']]
            if len(references)!=3:continue
            pairs=([(a,b) for i,a in enumerate(references) for b in references[i+1:]] if runs[0]['profile']['mode']=='openmp'
                   else [(a,b) for a in references for b in runs])
            comparisons=[self.compare(a,b) for a,b in pairs]
            if not comparisons:continue
            median=statistics.median(r['totalSeconds'] for r in runs);baseline=statistics.median(r['totalSeconds'] for r in references)
            repeatability=[self.compare(a,b) for i,a in enumerate(references) for b in references[i+1:]]
            passed=all(c['promotionEligible'] for c in comparisons+repeatability)
            summary=dict(config=runs[0]['config'],mode=runs[0]['profile']['mode'],median=median,min=min(r['totalSeconds'] for r in runs),max=max(r['totalSeconds'] for r in runs),
                         speedup=baseline/median,passed=passed,status='approved' if passed else ('pending-review' if not policy['approved'] else 'rejected'),
                         spreadSeconds=max(r['totalSeconds'] for r in runs)-min(r['totalSeconds'] for r in runs),
                         legacyPassed=all(v['legacy']['passed'] for v in comparisons),comparisonCount=len(comparisons))
            summaries.append(summary)
            if passed and baseline/median>=1/.95:
                receipts.append(dict(mode=summary['mode'],signature=runs[0]['signature'],validationVersion=VALIDATION_VERSION,policyHash=policy['hash'],passed=True,speedup=baseline/median,median=median,measuredRuns=3))
        self.state['summaries']=summaries;self.save()
        if policy['approved'] and receipts:
            old=json.loads(REGISTRY.read_text()) if REGISTRY.exists() else []
            keys=[r['signature'] for r in receipts];atomic_json(REGISTRY,[r for r in old if r.get('signature') not in keys]+receipts)
    def campaign(self):
        try:
            for scene,duration in CASES:
                for i in range(4):self.execute(Experiment(scene=scene,duration=duration),'openmp','reference',i)
            for mode in EARLY:
                for scene,duration in CASES:self.execute(Experiment(scene=scene,duration=duration),mode,'screen',-1)
            for scene,duration in CASES:
                candidates=[r for r in self.state['runs'] if r['phase']=='screen' and r['config']['scene']==scene]
                best=min(candidates,key=self.screen_score)
                for i in range(4):self.execute(Experiment(scene=scene,duration=duration),best['profile']['mode'],'finalist',i)
            for mode in LATER:
                for scene,duration in CASES:self.execute(Experiment(scene=scene,duration=duration),mode,'screen',-1)
            for scene,duration in CASES:
                candidates=[r for r in self.state['runs'] if r['phase']=='screen' and r['config']['scene']==scene]
                best=min(candidates,key=self.screen_score)
                for i in range(4):self.execute(Experiment(scene=scene,duration=duration),best['profile']['mode'],'finalist',i)
            for mode in ('openmp-pcores','mpi4-z4-pcores','hybrid2x2-z-pcores'):
                for scene,duration in CASES:self.execute(Experiment(scene=scene,duration=duration),mode,'cpu-screen',-1)
            self.state['status']='completed-research'
        except BudgetStop as exc:self.state.update(status='budget-stopped',stopReason=str(exc))
        finally:
            try:self.summarize()
            except BudgetStop as exc:self.state.update(status='budget-stopped',stopReason=str(exc));self.save()
            render(self.state,self.root/'report.md')

def render(state,path):
    lines=['# Kampania execution-3','',f"Stan: {state['status']}. Natywne próby: {len(state['runs'])}. Czas nowych zadań: {state.get('usedSeconds',0)/3600:.3f} h.",
           '','Polityka validation-v3 jest osobno zatwierdzana. Brak promocji nie oznacza nieudanego pomiaru. Czasy archiwizacji i niezależnej kontroli są raportowane osobno.',
           '','| Scena | Profil | Etap | Próba | Całość s | Archiwum MiB |','|---|---|---|---:|---:|---:|']
    for r in state['runs']:lines.append(f"| {r['config']['scene']} {r['config']['duration']:g}s | {r['profile']['mode']} | {r['phase']} | {r['iteration']} | {r['totalSeconds']:.2f} | {r['archive']['bytes']/1024**2:.1f} |")
    missing=[]
    for mode,phase in [(m,'screen') for m in EARLY+LATER]+[(m,'cpu-screen') for m in ('openmp-pcores','mpi4-z4-pcores','hybrid2x2-z-pcores')]:
        scenes=[scene for scene,duration in CASES if not any(r['profile']['mode']==mode and r['phase']==phase and r['config']['scene']==scene for r in state['runs'])]
        if scenes:missing.append(f"`{mode}` ({', '.join(scenes)})")
    if missing:lines+=['','Niewykonane próby w tej kampanii: '+', '.join(missing)+'. Brak pomiaru nie jest dowodem zgodności ani przyspieszenia.']
    lines+=['','## Czas i zasoby','',
            'Konwersja częściowo zachodzi podczas pracy solvera; nie sumujemy jej ponownie do czasu całości. Pamięć oznacza szczytowy commit Windows Job, nie RSS. Liczniki I/O dotyczą procesów FDS/MPI, nie przepustowości fizycznego dysku.',
            '','| Scena | Profil | Etap / próba | Solver s | Konwersja s | Pierwsza klatka s | Commit MiB | Odczyt MiB | Zapis MiB |',
            '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in state['runs']:
        t=r.get('telemetry',{});first=r.get('firstFrameSeconds');first_text=f'{first:.2f}' if first is not None else '—'
        lines.append(f"| {r['config']['scene']} | {r['profile']['mode']} | {r['phase']} / {r['iteration']} | {r['solverSeconds']:.2f} | {r['conversionSeconds']:.2f} | {first_text} | "+' | '.join(f'{t.get(k,0)/1024**2:.2f}' for k in ('peakMemoryBytes','readBytes','writeBytes'))+' |')
    lines+=['','## Zestawy z pełnymi pomiarami','']
    for s in state['summaries']:lines.append(f"- {s['config']['scene']}: {s['mode']}, mediana {s['median']:.2f}s, {s['speedup']:.3f}×; stare bramki {'PASS' if s.get('legacyPassed') else 'FAIL'}, kwalifikacja v3: {s['status']}.")
    if any(r['phase'] in ('reference','finalist') for r in state['runs']):
        lines+=['','Szczegółowe błędy pól, sond i strumieni: [zgodność numeryczna](numerical-v3.md). Raport rozróżnia dostępne porównania i brakujące pary.']
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT/'artifacts/campaign-v3');p.add_argument('--hours',type=float,default=8);p.add_argument('--gib',type=float,default=4);p.add_argument('--summary-only',action='store_true');a=p.parse_args()
    c=Campaign(a.root,a.hours,a.gib)
    try:
        if a.summary_only:c.summarize();render(c.state,c.root/'report.md')
        else:c.campaign()
        from scripts.report_campaign_validation import report as numerical_report
        numerical_output=ROOT/'docs/numerical-v3.md'
        numerical_report(c.root,numerical_output)
        (c.root/'numerical-v3.md').write_bytes(numerical_output.read_bytes())
        (c.root/'benchmark-v3-data.json').write_bytes(numerical_output.with_name('benchmark-v3-data.json').read_bytes())
    finally:c.close()
