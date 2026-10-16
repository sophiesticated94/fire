"""Reproducible profiles. Automatic MPI requires a local validation receipt."""
from dataclasses import dataclass, asdict
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import platform
import re
from .policy import VALIDATION_VERSION,validation_policy

PROFILE_VERSION = 'execution-3'
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
    layout: str = 'single'
    affinity: tuple[int,...] = ()
    libraries: tuple[tuple[str,str],...] = ()
    diagnostics: str = 'flux-1'

    def identity(self):
        # Canonical JSON representation also normalizes tuple/list round trips.
        return json.loads(json.dumps({k:v for k,v in asdict(self).items() if k not in ('executable','launcher')}))

    def command(self):
        return [self.launcher,'-n',str(self.ranks),self.executable,'ignis.fds'] if self.ranks>1 else [self.executable,'ignis.fds']

    def environment(self):
        env=os.environ.copy(); parent=Path(self.executable).parent
        env.pop('IGNIS_CPU_MASK',None)
        env['PATH']=str(parent)+os.pathsep+str(parent/'mpi')+os.pathsep+env.get('PATH','')
        for k in list(env):
            if k.startswith(('OMP_','KMP_','I_MPI_')): env.pop(k)
        env.update(OMP_NUM_THREADS=str(self.threads),OMP_PLACES='cores',OMP_PROC_BIND='close')
        if self.ranks>1:
            mpi_root=Path(self.launcher).parent
            env['PATH']=str(mpi_root)+os.pathsep+env['PATH']
            env.update(I_MPI_ROOT=str(mpi_root),I_MPI_FABRICS='shm',I_MPI_PIN='1',I_MPI_PIN_DOMAIN='core' if self.threads==1 else str(self.threads))
        if self.affinity:
            env['IGNIS_CPU_MASK']=hex(sum(1<<cpu for cpu in self.affinity))
            # Explicit logical IDs are obtained from Windows topology, never guessed.
            env['OMP_PLACES']=','.join('{'+str(cpu)+'}' for cpu in self.affinity)
            if self.ranks>1:env['I_MPI_PIN_PROCESSOR_LIST']=','.join(map(str,self.affinity))
        return env

def get_optimal_threads():
    try: return max(1,min(16,int(os.environ.get('IGNIS_THREADS',min(4,os.cpu_count() or 4)))))
    except ValueError: raise ValueError('IGNIS_THREADS musi być liczbą całkowitą.')

def build_profile(exe,mode='openmp',threads=None):
    requested=mode;pin=mode.endswith('-pcores');mode=mode.removesuffix('-pcores')
    aliases={'mpi2':'mpi2-z2','mpi4':'mpi4-z4','mpi4-xy':'mpi4-xy22','hybrid2x2-z':'hybrid2x2-z2'}
    mode=aliases.get(mode,mode)
    match=re.fullmatch(r'(mpi[24]|hybrid2x2)-(x2|x4|y2|y4|z2|z4|xy22|z13|z31|z1124|z4211)',mode)
    if mode=='openmp':ranks=1;layout='single'
    elif match:ranks=2 if match[1] in ('mpi2','hybrid2x2') else 4;layout=match[2]
    else:raise ValueError(f'Nieznany profil: {requested}')
    from .meshes import LAYOUTS
    if __import__('math').prod(len(a) for a in LAYOUTS[layout])!=ranks:raise ValueError('Liczba procesów nie pasuje do podziału.')
    count=(threads if threads is not None else get_optimal_threads()) if ranks==1 else (2 if mode.startswith('hybrid') else 1)
    exe=Path(exe)
    binary=exe if ranks==1 or count>1 else exe.parent/('fds.exe' if os.name=='nt' else 'fds')
    launcher=Path(os.environ.get('IGNIS_MPIEXEC',str(exe.parent/'mpi'/('mpiexec.exe' if os.name=='nt' else 'mpiexec')))) if ranks>1 else None
    if not binary.is_file() or (launcher and not launcher.is_file()): raise FileNotFoundError(f'Profil {mode} niedostępny: brak binariów FDS/MPI.')
    runtime=launcher.parent/'impi.dll' if launcher else exe.parent/'mpi/impi.dll'
    affinity=()
    if pin:
        from .cpu import performance_cores
        affinity=tuple(performance_cores())
        if len(affinity)<ranks*count:raise ValueError('Nie rozpoznano wystarczającej liczby rdzeni Performance.')
        affinity=affinity[:ranks*count]
    libraries=tuple((p.name,fingerprint(p)) for p in (exe.parent/'libiomp5md.dll',runtime) if p.is_file())
    return SolverProfile(requested,ranks,count,str(binary.resolve()),fingerprint(binary),str(launcher.resolve()) if launcher else None,
                         fingerprint(launcher) if launcher else None,fingerprint(runtime) if ranks>1 and runtime.is_file() else None,
                         axis=layout[0] if layout!='single' else 'z',layout=layout,affinity=affinity,libraries=libraries)

def validation_signature(config,profile):
    from .models import MODEL_VERSION,SOLVER_VERSION
    from .models import geometry
    from .meshes import partition
    return dict(config=config.canonical(),model=MODEL_VERSION,solver=SOLVER_VERSION,profile=profile.identity(),hardware=hardware_id(),
                meshLayout=partition(geometry(config)[1],profile.layout),validationVersion=VALIDATION_VERSION)

def resolve_profile(exe,config):
    mode=os.environ.get('IGNIS_SOLVER','auto').lower()
    if mode!='auto': return build_profile(exe,mode)
    baseline=build_profile(exe,threads=4)
    policy=validation_policy()
    if not policy['approved']:return baseline
    try: entries=json.loads(REGISTRY.read_text(encoding='utf-8'))
    except (OSError,ValueError): entries=[]
    if not isinstance(entries,list):entries=[]
    candidates=[]
    for e in entries:
        try:
            p=build_profile(exe,e['mode'],threads=4)
            if (e.get('validationVersion')==VALIDATION_VERSION and e.get('policyHash')==policy['hash']
                and e['signature']==validation_signature(config,p) and e['passed'] is True and e['speedup']>=1/.95 and e['measuredRuns']>=3):
                candidates.append((e['median'],p))
        except (ValueError,KeyError,TypeError,OSError): continue
    if not candidates:
        from .families import resolve_family
        return resolve_family(exe,config,policy) or baseline
    return min(candidates,key=lambda x:x[0])[1]
