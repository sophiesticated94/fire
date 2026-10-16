"""Sequential, resumable native suite sharing the production runner/pipeline."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import statistics
import sys
import time
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import Engine,ROOT,solver_path
from backend.models import Experiment,make_deck
from backend.profiles import build_profile,validation_signature,REGISTRY
from backend.runner import ProcessTree
from backend.progressive import ProgressiveConverter,atomic_json
from backend.validation import compare,verify_native
from scripts.report_benchmark import render

def parse_cpu_csv(path):
    if not path.exists(): return {}
    with path.open() as f: rows=list(csv.reader(f))
    out={}
    for row in rows[1:]:
        for k,v in zip(rows[0],row):
            try: out[k.strip()]=out.get(k.strip(),0)+float(v)
            except ValueError: pass
    return out

def run(config,profile,root,timeout,preview=True):
    attempt=uuid.uuid4().hex;folder=root/attempt;folder.mkdir(parents=True)
    (folder/'ignis.fds').write_text(make_deck(config,profile.ranks),encoding='ascii')
    pipe=ProgressiveConverter(folder,config,profile,config.key(profile),attempt)
    tree=ProcessTree();started=time.perf_counter();conversion=0;first_frame=None;affinity={}
    try:
        with (folder/'solver.log').open('wb') as log:
            tree.start(profile.command(),folder,profile.environment(),log)
            while tree.poll() is None:
                elapsed=time.perf_counter()-started
                if elapsed>timeout: raise TimeoutError(f'Timeout {timeout} s')
                if int(elapsed)%2==0:affinity.update(tree.telemetry().get('processAffinity',{}))
                if preview:
                    before=time.perf_counter();pipe.drain(elapsed);conversion+=time.perf_counter()-before
                    if first_frame is None and pipe.meta['times']: first_frame=elapsed
                time.sleep(.2)
            tree.wait();solver_time=time.perf_counter()-started
            text=(folder/'solver.log').read_text(errors='replace')+(folder/'ignis.out').read_text(errors='replace')
            if tree.poll()!=0 or 'STOP: FDS completed successfully' not in text: raise RuntimeError(text[-3000:])
            before=time.perf_counter();pipe.drain(solver_time,final=True);meta=pipe.finish(solver_time)
            conversion+=time.perf_counter()-before
            meta.update(frameDirectory='preview/frames',telemetry=tree.telemetry())
            meta['telemetry']['observedProcessAffinity']=affinity
            atomic_json(folder/'result.json',meta)
        total=time.perf_counter()-started
        verify_native(folder)
        steps=0;step_file=folder/'ignis_steps.csv'
        if step_file.exists():
            with step_file.open() as f: rows=list(csv.reader(f))
            if len(rows)>2: steps=int(rows[-1][0])
        return dict(folder=str(folder),config=config.canonical(),profile=profile.identity(),signature=validation_signature(config,profile),
                    solverSeconds=solver_time,conversionSeconds=conversion,totalSeconds=total,steps=steps,secondsPerStep=solver_time/max(steps,1),
                    firstFrameSeconds=first_frame,telemetry=meta['telemetry'],cpu=parse_cpu_csv(folder/'ignis_cpu.csv'),nativeExact=True)
    finally:
        try:
            if not tree.stopped:
                tree.terminate()
                if tree.pid: tree.wait()
        finally:tree.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scene',choices=['burner','candle','wood'])
    parser.add_argument('--duration',type=float)
    parser.add_argument('--quality',choices=['preview','fine'],default='preview')
    parser.add_argument('--iterations',type=int,default=3)
    parser.add_argument('--timeout',type=float,default=7200)
    parser.add_argument('--modes',nargs='+',default=['openmp','mpi2','mpi4'])
    parser.add_argument('--output-json',default='artifacts/benchmark-v2.json')
    parser.add_argument('--no-preview',action='store_true',help='Measure solver with progressive reading disabled')
    args=parser.parse_args();path=ROOT/args.output_json;path.parent.mkdir(parents=True,exist_ok=True)
    if args.iterations<3: parser.error('Wymagane minimum 3 pomiary po rozgrzewce.')
    report=json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(version=2,runs=[],comparisons=[],summaries=[])
    exe=solver_path()
    if not exe: raise RuntimeError('Brak FDS')
    cases=[(args.scene,args.duration or (15 if args.scene=='wood' else 6))] if args.scene else [('burner',2),('candle',2),('burner',6),('candle',6),('wood',15)]
    lease=Engine()
    try:
        lease._lease()
        for scene,duration in cases:
            c=Experiment(scene=scene,duration=duration,quality=args.quality,fuel=1.2 if scene=='candle' else 12)
            for mode in args.modes:
                p=build_profile(exe,mode,threads=4)
                signature=validation_signature(c,p)
                previous=[r for r in report['runs'] if r['signature']==signature and r['preview']==(not args.no_preview)]
                for iteration in range(args.iterations+1):
                    if any(r['iteration']==iteration for r in previous): continue
                    print(f'START {scene} {duration}s {mode} iteration={iteration}',flush=True)
                    result=run(c,p,ROOT/'artifacts/benchmark-v2',args.timeout,not args.no_preview)
                    result.update(iteration=iteration,preview=not args.no_preview)
                    report['runs'].append(result);atomic_json(path,report);render(path,ROOT/'docs/benchmark-v2.md')
                    print(f"DONE solver={result['solverSeconds']:.2f}s total={result['totalSeconds']:.2f}s frames exact",flush=True)
            signatures={mode:validation_signature(c,build_profile(exe,mode,threads=4)) for mode in args.modes}
            group=[r for r in report['runs'] if r['signature']==signatures.get(r['profile']['mode']) and r['iteration']>0 and r['preview']==(not args.no_preview)]
            baseline=[r for r in group if r['profile']['mode']=='openmp']
            if len(baseline)<args.iterations: continue
            reference=sorted(baseline,key=lambda r:r['totalSeconds'])[len(baseline)//2]
            receipts=[]
            for mode in args.modes:
                runs=[r for r in group if r['profile']['mode']==mode]
                if len(runs)<args.iterations: continue
                comparisons=[compare(reference['folder'],r['folder']) for r in runs]
                median=statistics.median(r['totalSeconds'] for r in runs)
                speedup=statistics.median(r['totalSeconds'] for r in baseline)/median
                summary=dict(config=c.canonical(),mode=mode,median=median,min=min(r['totalSeconds'] for r in runs),max=max(r['totalSeconds'] for r in runs),
                             stdev=statistics.stdev(r['totalSeconds'] for r in runs),speedup=speedup,passed=all(v['passed'] for v in comparisons),comparisons=comparisons)
                report['summaries']=[s for s in report['summaries'] if not (s['config']==c.canonical() and s['mode']==mode)]+[summary]
                receipts.append(dict(signature=runs[0]['signature'],mode=mode,median=median,speedup=speedup,passed=summary['passed'],measuredRuns=len(runs)))
                print('GATE',scene,duration,mode,'PASS' if summary['passed'] else 'FAIL',f'speedup={speedup:.3f}',flush=True)
            # Only default pipeline measurements can promote production profiles.
            if not args.no_preview:
                entries=json.loads(REGISTRY.read_text()) if REGISTRY.exists() else []
                signatures=[r['signature'] for r in receipts]
                entries=[e for e in entries if e['signature'] not in signatures]+receipts
                atomic_json(REGISTRY,entries)
            atomic_json(path,report)
            render(path,ROOT/'docs/benchmark-v2.md')
    finally: lease._release()

if __name__=='__main__': main()
