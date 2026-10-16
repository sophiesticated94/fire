"""Time actual HTTP create/status/preview/result flow on an isolated local server."""
import argparse
import json
from pathlib import Path
import socket
import sys
import time
import urllib.request
import urllib.error
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import ROOT,solver_path
from backend.runner import ProcessTree
from backend.profiles import validation_signature,build_profile
from backend.validation import verify_native
from backend.progressive import atomic_json

def request(base,path,payload=None):
    body=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(base+path,data=body,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as response:return response.read()

def run_api(config,profile,root,timeout,attempt=None,on_progress=None):
    attempt=attempt or uuid.uuid4().hex;workspace=Path(root)/attempt;workspace.mkdir(parents=True)
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}';env=profile.environment()
    # Production pins only the solver's nested job, not the API/converter.
    # Engine will derive the requested mask again for its own ProcessTree.
    env.pop('IGNIS_CPU_MASK',None)
    env.update(IGNIS_RUNS_DIR=str((workspace/'runs').resolve()),IGNIS_CACHE_READ='0',IGNIS_SOLVER=profile.mode,IGNIS_FDS=profile.executable,IGNIS_THREADS=str(profile.threads))
    # The server resolves its own profile from the same installed OpenMP entry.
    # Pure MPI profiles still need the stock OpenMP path as the resolver base.
    env['IGNIS_FDS']=str(solver_path())
    tree=ProcessTree();folder=None;job=None;first=None;started=None
    try:
        with (workspace/'api-server.log').open('wb') as log:
            tree.start([sys.executable,'-m','uvicorn','backend.app:app','--host','127.0.0.1','--port',str(port)],ROOT,env,log)
            startup=time.monotonic()
            while True:
                if tree.poll() is not None:raise RuntimeError('Isolated API server exited during startup')
                try:request(base,'/api/health');break
                except (OSError,urllib.error.URLError):
                    if time.monotonic()-startup>30:raise TimeoutError('API server startup')
                    time.sleep(.1)
            started=time.perf_counter();job=json.loads(request(base,'/api/experiments',config.canonical()));ident=job['id']
            folder=workspace/'runs'/ident/'attempts'/job['attempt']
            while True:
                elapsed=time.perf_counter()-started
                if elapsed>timeout:raise TimeoutError('API experiment timeout')
                job=json.loads(request(base,f'/api/experiments/{ident}'))
                try:
                    manifest=json.loads(request(base,f'/api/experiments/{ident}/preview/manifest'))
                    if manifest['times'] and first is None:
                        data=request(base,f"/api/experiments/{ident}/preview/frames/0?attempt={job['attempt']}")
                        if data!=(folder/'preview/frames/00000.bin').read_bytes():raise ValueError('HTTP preview frame transport mismatch')
                        first=time.perf_counter()-started
                except urllib.error.HTTPError as exc:
                    if exc.code!=409:raise
                if on_progress:on_progress(elapsed,folder)
                if job['status']=='completed':break
                if job['status'] in ('cancelled','failed','interrupted'):raise RuntimeError(str(job))
                time.sleep(1)
            meta=json.loads(request(base,f'/api/experiments/{ident}/result'))
            if meta['profile']!=profile.identity():raise ValueError('API resolved a different execution profile')
            last=len(meta['times'])-1;data=request(base,f'/api/experiments/{ident}/frames/{last}')
            expected=(folder/meta.get('frameDirectory','frames')/f'{last:05d}.bin').read_bytes()
            if data!=expected:raise ValueError('HTTP frame transport mismatch')
            total=time.perf_counter()-started;server_telemetry=tree.telemetry()
    finally:
        try:
            if not tree.stopped:
                tree.terminate()
                if tree.pid:tree.wait()
        finally:tree.close()
    verify_native(folder)
    return dict(folder=str(folder),config=config.canonical(),profile=profile.identity(),signature=validation_signature(config,profile),
                solverSeconds=meta['solverSeconds'],conversionSeconds=meta['conversionSeconds'],totalSeconds=total,firstFrameSeconds=first,
                telemetry=meta['telemetry'],serverJobTelemetry=server_telemetry,backendIO=meta['backendIO'],nativeExact=True,
                transport='http-api',firstFrameDetectionIntervalSeconds=1,serverStartupIncluded=False)

if __name__=='__main__':
    from backend.models import Experiment
    from scripts.campaign_v3 import Campaign,render,BudgetStop
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT/'artifacts/campaign-v3');p.add_argument('--scene',choices=['burner','candle','wood'],default='burner');p.add_argument('--duration',type=float,default=6);p.add_argument('--mode',default='openmp');p.add_argument('--hours',type=float,default=8);a=p.parse_args()
    c=Campaign(a.root,a.hours)
    try:
        for i in range(4):c.execute(Experiment(scene=a.scene,duration=a.duration),a.mode,'api',i,transport='api')
    except BudgetStop as exc:c.state.update(status='budget-stopped',stopReason=str(exc));c.save()
    finally:render(c.state,c.root/'report.md');c.close()
