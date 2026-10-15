from __future__ import annotations
import json
import atexit
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from .models import Experiment, make_deck
from .converter import convert
from .solver_config import WindowsJobObject, get_solver_env, get_solver_command

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT/'runs'
SAMPLES = ROOT/'samples'


def solver_path():
    choices = [os.environ.get('IGNIS_FDS',''), ROOT/'tools/fds/firemodels/FDS6/bin/fds_openmp.exe', Path('C:/Program Files/firemodels/FDS6/bin/fds_openmp.exe')]
    for p in choices:
        if p and Path(p).is_file():
            return Path(p).resolve()
    found = shutil.which('fds_openmp') or shutil.which('fds')
    return Path(found) if found else None


def solver_env(exe: Path):
    return get_solver_env(exe)


class Engine:
    def __init__(self):
        RUNS.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.active = None
        self.jobs = {}
        self.process = None
        self.job_object = None
        self.stop_event = threading.Event()
        self.started = 0
        self.lease = None
        atexit.register(self.shutdown)

    def _lease(self):
        handle = (RUNS/'.solver.lock').open('a+b')
        handle.seek(0,2)
        if handle.tell()==0: handle.write(b'0'); handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise RuntimeError('Inny proces IGNIS oblicza eksperyment. Poczekaj na jego zakończenie.')
        self.lease = handle

    def _release(self):
        if self.lease:
            self.lease.close()
            self.lease = None

    def folder(self, ident):
        if not re.fullmatch(r'[a-f0-9]{20}', ident):
            raise KeyError('Nieprawidłowy identyfikator')
        for base in (SAMPLES,RUNS):
            p = base/ident
            if p.is_dir():
                if base==SAMPLES and not (p/'result.json').exists(): continue
                return p
        raise KeyError('Nie znaleziono eksperymentu')

    def status(self, ident):
        if ident in self.jobs:
            return dict(self.jobs[ident])
        folder = self.folder(ident)
        if (folder/'result.json').exists():
            return {'id':ident,'status':'completed','progress':1,'cached':True}
        return {'id':ident,'status':'interrupted','progress':0,'error':'Obliczenia przerwano. Uruchom ponownie.'}

    def create(self, config: Experiment):
        ident = config.key()
        with self.lock:
            try:
                folder = self.folder(ident)
                if (folder/'result.json').exists():
                    return {'id':ident,'status':'completed','progress':1,'cached':True}
            except KeyError:
                pass
            if self.active:
                raise RuntimeError('Inny eksperyment jest już obliczany.')
            exe = solver_path()
            if not exe:
                raise FileNotFoundError('Brak FDS 6.11.1. Uruchom scripts/setup.ps1.')
            self._lease()
            folder = RUNS/ident
            try:
                folder.mkdir(exist_ok=True)
                # A retry starts clean: only remove artifacts in this exact job.
                for item in folder.iterdir():
                    if item.is_file() or item.is_symlink(): item.unlink()
                    elif item.is_dir(): shutil.rmtree(item, ignore_errors=True)
                (folder/'ignis.fds').write_text(make_deck(config),encoding='ascii')
                (folder/'config.json').write_text(json.dumps(config.canonical()),encoding='utf-8')
            except Exception:
                self._release()
                raise
            self.jobs[ident] = {'id':ident,'status':'running','progress':0,'physicalTime':0,'duration':config.duration,'config':config.canonical()}
            self.active = ident
            self.stop_event.clear()
            threading.Thread(target=self._run,args=(ident,config,exe,folder),daemon=True).start()
            return dict(self.jobs[ident])

    def cancel(self, ident):
        with self.lock:
            if self.active != ident:
                return self.status(ident)
            self.stop_event.set()
            if self.job_object:
                self.job_object.terminate()
            if self.process and self.process.poll() is None:
                self.process.terminate()
            self.jobs[ident]['status'] = 'cancelling'
            return dict(self.jobs[ident])

    def _run(self, ident, config, exe, folder):
        started = time.monotonic()
        job = self.jobs[ident]
        cmd = get_solver_command(exe)
        self.job_object = WindowsJobObject()
        try:
            with (folder/'solver.log').open('w',encoding='utf-8') as log:
                self.process = subprocess.Popen(cmd,cwd=folder,env=solver_env(exe),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                if self.job_object:
                    self.job_object.assign_process(self.process.pid)
                while self.process.poll() is None:
                    if self.stop_event.wait(0.5):
                        if self.job_object:
                            self.job_object.terminate()
                        self.process.terminate()
                        try: self.process.wait(timeout=5)
                        except subprocess.TimeoutExpired: self.process.kill(); self.process.wait()
                        break
                    output = folder/'ignis.out'
                    if output.exists():
                        content = output.read_text(errors='replace')
                        matches = re.findall(r'Total Time:\s*([\d.E+\-]+)',content)
                        if matches:
                            t = float(matches[-1])
                            job.update(physicalTime=t,progress=min(.96,t/config.duration*.96))
                    job['elapsed'] = round(time.monotonic()-started,1)
            if self.stop_event.is_set():
                job.update(status='cancelled',error=None)
                return
            log_text = (folder/'solver.log').read_text(errors='replace')
            out_text = (folder/'ignis.out').read_text(errors='replace') if (folder/'ignis.out').exists() else ''
            if self.process.returncode != 0 or 'STOP: FDS completed successfully' not in log_text+out_text:
                raise RuntimeError((log_text+'\n'+out_text)[-5000:])
            job.update(status='converting',progress=.97)
            elapsed = time.monotonic()-started
            convert(folder,config.canonical(),elapsed)
            job.update(status='completed',progress=1,physicalTime=config.duration,elapsed=round(time.monotonic()-started,2))
        except Exception as exc:
            job.update(status='failed',error=str(exc))
        finally:
            with self.lock:
                self.active = None
                self.process = None
                if self.job_object:
                    self.job_object.close()
                    self.job_object = None
                self._release()

    def history(self):
        results = []
        for base in (RUNS,SAMPLES):
            if not base.exists(): continue
            for folder in base.iterdir():
                p = folder/'result.json'
                if p.exists():
                    try:
                        meta = json.loads(p.read_text(encoding='utf-8'))
                        results.append({'id':meta['id'],'config':meta['config'],'elapsed':meta['elapsed'],'sample':base==SAMPLES,'featured':meta.get('featured',False)})
                    except (ValueError, KeyError): pass
        return list({x['id']:x for x in results}.values())

    def shutdown(self):
        """Never leave a CPU-intensive native process orphaned on server exit."""
        self.stop_event.set()
        if self.job_object:
            self.job_object.terminate()
            self.job_object.close()
            self.job_object = None
        p = self.process
        if p is not None and p.poll() is None:
            p.terminate()
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=5)
