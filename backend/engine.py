from __future__ import annotations
import atexit
import json
import os
from pathlib import Path
import re
import shutil
import threading
import time
import uuid
from .models import Experiment,make_deck
from .profiles import resolve_profile
from .runner import ProcessTree
from .progressive import ProgressiveConverter,atomic_json

ROOT=Path(__file__).resolve().parent.parent
RUNS=Path(os.environ.get('IGNIS_RUNS_DIR',str(ROOT/'runs'))).resolve()
LEASE_ROOT=ROOT/'runs'
SAMPLES=ROOT/'samples'

def solver_path():
    explicit=os.environ.get('IGNIS_FDS')
    if explicit:
        path=Path(explicit).expanduser()
        return path.resolve() if path.is_file() else None
    choices=[ROOT/'tools/fds/firemodels/FDS6/bin/fds_openmp.exe',Path('C:/Program Files/firemodels/FDS6/bin/fds_openmp.exe')]
    for p in choices:
        if p and Path(p).is_file(): return Path(p).resolve()
    found=shutil.which('fds_openmp') or shutil.which('fds')
    return Path(found).resolve() if found else None

def solver_env(exe):
    from .profiles import build_profile
    return build_profile(exe).environment()

class Engine:
    def __init__(self):
        RUNS.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.active=None;self.jobs={};self.process=None
        self.stop_event=threading.Event();self.lease=None;self.worker=None
        atexit.register(self.shutdown)

    def _lease(self):
        LEASE_ROOT.mkdir(parents=True,exist_ok=True)
        handle=(LEASE_ROOT/'.solver.lock').open('a+b');handle.seek(0,2)
        if handle.tell()==0: handle.write(b'0');handle.flush()
        handle.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            handle.close();raise RuntimeError('Inny proces IGNIS oblicza eksperyment.')
        self.lease=handle

    def _release(self):
        if self.lease: self.lease.close();self.lease=None

    def folder(self,ident,attempt=None):
        if not re.fullmatch(r'[a-f0-9]{20}',ident): raise KeyError('Nieprawidłowy identyfikator')
        if attempt is not None:
            if not re.fullmatch(r'[a-f0-9]{32}',attempt): raise KeyError('Nieprawidłowa próba')
            p=RUNS/ident/'attempts'/attempt
            if p.is_dir(): return p
            raise KeyError('Nie znaleziono próby')
        for base in (SAMPLES,RUNS):
            p=base/ident
            if not p.is_dir(): continue
            pointer=p/'latest.json'
            if pointer.exists():
                return self.folder(ident,json.loads(pointer.read_text())['attempt'])
            if base==SAMPLES and not (p/'result.json').exists(): continue
            return p
        raise KeyError('Nie znaleziono eksperymentu')

    def status(self,ident):
        with self.lock:
            if ident in self.jobs: return dict(self.jobs[ident])
        folder=self.folder(ident)
        if (folder/'result.json').exists():
            meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
            return dict(id=ident,status='completed',progress=1,cached=True,
                        profile=meta.get('profile'),attempt=meta.get('attempt'),config=meta['config'],
                        duration=meta['config']['duration'],physicalTime=meta['config']['duration'],
                        elapsed=meta.get('elapsed'),previewFrames=len(meta.get('times',[])))
        stored=folder/'job.json'
        previous=json.loads(stored.read_text(encoding='utf-8')) if stored.exists() else {'id':ident}
        if previous.get('status') not in ('cancelled','failed'):
            previous.update(status='interrupted',error='Obliczenia przerwano. Uruchom ponownie.')
        return previous

    def _persist(self,ident,folder):
        atomic_json(folder/'job.json',self.jobs[ident])

    def create(self,config:Experiment):
        with self.lock:
            exe=solver_path()
            if not exe:
                if os.environ.get('IGNIS_FDS'):raise FileNotFoundError('IGNIS_FDS nie wskazuje istniejącego pliku solvera.')
                raise FileNotFoundError('Brak FDS 6.11.1. Uruchom scripts/setup.ps1.')
            profile=resolve_profile(exe,config);ident=config.key(profile)
            try:
                folder=self.folder(ident)
                if (folder/'result.json').exists() and os.environ.get('IGNIS_CACHE_READ','1')!='0': return dict(id=ident,status='completed',progress=1,cached=True,profile=profile.identity())
            except KeyError: pass
            if self.active: raise RuntimeError('Inny eksperyment jest już obliczany.')
            self._lease()
            try:
                attempt=uuid.uuid4().hex;root=RUNS/ident;folder=root/'attempts'/attempt;folder.mkdir(parents=True)
                (folder/'ignis.fds').write_text(make_deck(config,profile.ranks,profile=profile,diagnostics=profile.diagnostics!='none'),encoding='ascii')
                atomic_json(folder/'config.json',config.canonical())
                atomic_json(root/'latest.json',{'attempt':attempt})
                self.jobs[ident]=dict(id=ident,attempt=attempt,status='running',progress=0,physicalTime=0,duration=config.duration,config=config.canonical(),profile=profile.identity())
                self.active=ident;self.stop_event.clear();self._persist(ident,folder)
                self.worker=threading.Thread(target=self._run,args=(ident,config,profile,folder),daemon=True)
                self.worker.start()
            except BaseException:
                self.active=None;self.worker=None;self._release()
                if ident in self.jobs:
                    self.jobs[ident].update(status='failed',error='Nie udało się uruchomić zadania.')
                    self._persist(ident,folder)
                raise
            return dict(self.jobs[ident])

    def cancel(self,ident):
        with self.lock:
            if self.active!=ident: return self.status(ident)
            if self.jobs[ident]['status'] in ('completed','cancelled','failed'):return dict(self.jobs[ident])
            self.stop_event.set();self.jobs[ident]['status']='cancelling'
            return dict(self.jobs[ident])

    def _run(self,ident,config,profile,folder):
        started=time.monotonic();job=self.jobs[ident];tree=None;pipeline=None;affinity={};threads={};conversion=0;first_frame=None
        from .incremental import Deadline,OutputProgress
        telemetry_deadline=Deadline(2);status_deadline=Deadline(1);progress=OutputProgress(folder/'ignis.out')
        try:
            pipeline=ProgressiveConverter(folder,config,profile,ident,job['attempt'])
            with (folder/'solver.log').open('wb') as log:
                with self.lock:
                    if not self.stop_event.is_set():
                        tree=ProcessTree();self.process=tree
                        tree.start(profile.command(),folder,profile.environment(),log)
                timeout=float(os.environ.get('IGNIS_TIMEOUT','7200'))
                while tree and tree.poll() is None and not self.stop_event.wait(.2):
                    elapsed=time.monotonic()-started
                    if elapsed>timeout: raise TimeoutError(f'Przekroczono limit obliczeń {timeout:g} s.')
                    if telemetry_deadline.due(elapsed):
                        sample=tree.telemetry();affinity.update(sample.get('processAffinity',{}));threads.update(sample.get('threadAffinity',{}))
                    conversion_started=time.monotonic();pipeline.drain(elapsed,stop=self.stop_event);conversion+=time.monotonic()-conversion_started
                    if first_frame is None and pipeline.meta['times']:first_frame=time.monotonic()-started
                    t=progress.read();job.update(physicalTime=t,progress=min(.96,t/config.duration*.96))
                    job.update(elapsed=round(elapsed,2),previewFrames=len(pipeline.meta['times']))
                    if status_deadline.due(elapsed):self._persist(ident,folder)
                if tree:
                    if self.stop_event.is_set(): tree.terminate()
                    tree.wait()
                solver_elapsed=time.monotonic()-started
            if self.stop_event.is_set():
                job.update(status='cancelled',error=None);return
            logs=(folder/'solver.log').read_text(errors='replace')
            output=folder/'ignis.out'
            if output.exists(): logs+='\n'+output.read_text(errors='replace')
            if not tree or tree.poll()!=0 or 'STOP: FDS completed successfully' not in logs: raise RuntimeError(logs[-5000:])
            job.update(status='converting',progress=.97)
            conversion_started=time.monotonic();pipeline.drain(time.monotonic()-started,final=True,stop=self.stop_event);conversion+=time.monotonic()-conversion_started
            with self.lock:
                if self.stop_event.is_set(): job.update(status='cancelled',error=None);return
                conversion_started=time.monotonic();meta=pipeline.finish(time.monotonic()-started);conversion+=time.monotonic()-conversion_started
                meta.update(solverSeconds=solver_elapsed,conversionSeconds=conversion,firstFrameSeconds=first_frame,
                            backendIO=dict(outputBytesRead=progress.tail.bytes_read,hrrBytesRead=pipeline.series_reader.tail.bytes_read,deviceBytesRead=pipeline.device_reader.tail.bytes_read))
                meta['telemetry']=tree.telemetry()
                meta['telemetry']['observedProcessAffinity']=affinity
                meta['telemetry']['observedThreadAffinity']=threads
                # Final frames reuse the immutable preview files, not another copy.
                meta['frameDirectory']='preview/frames'
                atomic_json(folder/'result.json',meta)
                job.update(status='completed',progress=1,physicalTime=config.duration,elapsed=round(time.monotonic()-started,2),previewFrames=len(meta['times']))
        except Exception as exc:
            job.update(status='cancelled' if self.stop_event.is_set() else 'failed',error=None if self.stop_event.is_set() else str(exc))
        finally:
            native_stopped=tree is None
            try:
                if tree:
                    try:
                        if not getattr(tree,'stopped',False):
                            tree.terminate()
                            if tree.pid:tree.wait()
                        native_stopped=True
                    finally:tree.close()
                if pipeline and job['status']!='completed': pipeline.finish(time.monotonic()-started,job['status'])
                self._persist(ident,folder)
            except Exception as exc:
                job.update(status='failed',error=f'Błąd sprzątania procesów: {exc}')
                try:self._persist(ident,folder)
                except OSError:pass
            finally:
                with self.lock:
                    if native_stopped:
                        self.process=None;self.active=None;self._release()

    def history(self):
        results={}
        for base in (RUNS,SAMPLES):
            for root in base.iterdir() if base.exists() else []:
                if not root.is_dir() or not re.fullmatch('[a-f0-9]{20}',root.name): continue
                try:
                    folder=self.folder(root.name) if base==RUNS else root
                    meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
                    results[root.name]=dict(id=meta['id'],config=meta['config'],elapsed=meta['elapsed'],sample=base==SAMPLES,featured=meta.get('featured',False),profile=meta.get('profile'))
                except (OSError,ValueError,KeyError): pass
        return list(results.values())

    def shutdown(self):
        with self.lock:
            self.stop_event.set();worker=self.worker
        if worker and worker is not threading.current_thread(): worker.join(timeout=15)
        if worker and worker.is_alive():
            # Do not release the lease while a worker still owns native processes.
            with self.lock:
                if self.process: self.process.terminate()
            worker.join(timeout=15)
