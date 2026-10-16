"""Reproducible profiles. Automatic MPI requires a local validation receipt."""
from dataclasses import dataclass, asdict
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import platform

PROFILE_VERSION = 'execution-2'
TRANSPORT_VERSION = 'float32-7-v2'
REGISTRY = Path(__file__).resolve().parent.parent/'artifacts/validated-profiles.json'

@lru_cache(maxsize=32)
def _digest(path, size, modified):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def fingerprint(path):
    s = path.stat()
    return _digest(str(path.resolve()), s.st_size, s.st_mtime_ns)

def hardware_id():
    return hashlib.sha256(f'{platform.node()}|{platform.processor()}|{os.cpu_count()}|{platform.version()}'.encode()).hexdigest()

@dataclass(frozen=True)
class SolverProfile:
    mode: str
    ranks: int
    threads: int
    executable: str
    executable_hash: str
    launcher: str | None = None
    launcher_hash: str | None = None
    runtime_hash: str | None = None
    version: str = PROFILE_VERSION
    axis: str = 'z'
    binding: str = 'cores/close'

    def identity(self):
        return {k:v for k,v in asdict(self).items() if k not in ('executable','launcher')}

    def command(self):
        return [self.launcher,'-n',str(self.ranks),self.executable,'ignis.fds'] if self.ranks>1 else [self.executable,'ignis.fds']

    def environment(self):
        env=os.environ.copy(); parent=Path(self.executable).parent
        env['PATH']=str(parent)+os.pathsep+str(parent/'mpi')+os.pathsep+env.get('PATH','')
        for k in list(env):
            if k.startswith(('OMP_','KMP_','I_MPI_')): env.pop(k)
        env.update(OMP_NUM_THREADS=str(self.threads),OMP_PLACES='cores',OMP_PROC_BIND='close')
        if self.ranks>1: env.update(I_MPI_ROOT=str(parent/'mpi'),I_MPI_FABRICS='shm',I_MPI_PIN='1',I_MPI_PIN_DOMAIN='core')
        return env

def get_optimal_threads():
    try: return max(1,min(16,int(os.environ.get('IGNIS_THREADS',min(4,os.cpu_count() or 4)))))
    except ValueError: raise ValueError('IGNIS_THREADS musi być liczbą całkowitą.')

def build_profile(exe,mode='openmp',threads=None):
    if mode not in ('openmp','mpi2','mpi4'): raise ValueError(f'Nieznany profil: {mode}')
    ranks=int(mode[-1]) if mode.startswith('mpi') else 1
    count=(threads if threads is not None else get_optimal_threads()) if ranks==1 else 1
    binary=exe if ranks==1 and count>1 else exe.parent/('fds.exe' if os.name=='nt' else 'fds')
    launcher=exe.parent/'mpi'/('mpiexec.exe' if os.name=='nt' else 'mpiexec') if ranks>1 else None
    if not binary.is_file() or (launcher and not launcher.is_file()): raise FileNotFoundError(f'Profil {mode} niedostępny: brak binariów FDS/MPI.')
    runtime=exe.parent/'mpi/impi.dll'
    return SolverProfile(mode,ranks,count,str(binary.resolve()),fingerprint(binary),str(launcher.resolve()) if launcher else None,
                         fingerprint(launcher) if launcher else None,fingerprint(runtime) if ranks>1 and runtime.is_file() else None)

def validation_signature(config,profile):
    from .models import MODEL_VERSION,SOLVER_VERSION
    return dict(config=config.canonical(),model=MODEL_VERSION,solver=SOLVER_VERSION,profile=profile.identity(),hardware=hardware_id())

def resolve_profile(exe,config):
    mode=os.environ.get('IGNIS_SOLVER','auto').lower()
    if mode!='auto': return build_profile(exe,mode)
    baseline=build_profile(exe,threads=4)
    try: entries=json.loads(REGISTRY.read_text(encoding='utf-8'))
    except (OSError,ValueError): return baseline
    if not isinstance(entries,list):return baseline
    candidates=[]
    for e in entries:
        try:
            p=build_profile(exe,e['mode'],threads=4)
            if e['signature']==validation_signature(config,p) and e['passed'] is True and e['speedup']>=1/.95 and e['measuredRuns']>=3:
                candidates.append((e['median'],p))
        except (ValueError,KeyError,TypeError,OSError): continue
    return min(candidates,key=lambda x:x[0])[1] if candidates else baseline
