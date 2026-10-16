import ctypes
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import numpy as np
import pytest
from fastapi.testclient import TestClient
import backend.engine as engine_module
from backend.engine import Engine,solver_path
from backend.models import Experiment,geometry,make_deck
from backend.profiles import build_profile,resolve_profile,validation_signature
from backend.progressive import SliceStream,ProgressiveConverter,atomic_json
from backend.runner import ProcessTree,WindowsAPI
from backend.app import app

def wait_engine(e):
    if e.worker: e.worker.join(15)
    assert e.active is None

@pytest.mark.parametrize('ranks',[2,4])
@pytest.mark.parametrize('scene',['burner','candle','wood'])
@pytest.mark.parametrize('quality',['preview','fine'])
def test_mesh_partition_preserves_global_cells(scene,quality,ranks):
    import re
    c=Experiment(scene=scene,quality=quality);bounds,cells=geometry(c)
    meshes=re.findall(r"&MESH ID='M\d+', IJK=(\d+),(\d+),(\d+), XB=([^/]+), MPI_PROCESS=(\d+)",make_deck(c,ranks))
    assert len(meshes)==ranks
    previous=bounds[4]
    for i,(nx,ny,nz,box,rank) in enumerate(meshes):
        b=list(map(float,box.split(',')))
        assert int(nx)==cells[0] and int(ny)==cells[1] and int(nz)*ranks==cells[2]
        assert b[:4]==pytest.approx(bounds[:4]);assert b[4]==pytest.approx(previous)
        assert int(rank)==i;previous=b[5]
    assert previous==pytest.approx(bounds[5])

def test_profile_cache_identity_and_exact_promotion(monkeypatch,tmp_path):
    import backend.profiles as p
    exe=solver_path()
    if not exe: pytest.skip('FDS required')
    c=Experiment();omp=build_profile(exe);mpi=build_profile(exe,'mpi4')
    assert c.key(omp)!=c.key(mpi)
    assert c.key(omp)!=c.key()
    monkeypatch.setenv('IGNIS_SOLVER','auto');monkeypatch.setattr(p,'REGISTRY',tmp_path/'profiles.json')
    receipt=dict(mode='mpi4',signature=validation_signature(c,mpi),passed=True,speedup=1.1,measuredRuns=3,median=100)
    atomic_json(p.REGISTRY,[receipt]);assert resolve_profile(exe,c).mode=='mpi4'
    assert resolve_profile(exe,Experiment(fuel=13)).mode=='openmp'
    assert resolve_profile(exe,Experiment(quality='fine')).mode=='openmp'
    receipt['passed']=False;atomic_json(p.REGISTRY,[receipt]);assert resolve_profile(exe,c).mode=='openmp'
    receipt['passed']=True;receipt['speedup']=1.01;atomic_json(p.REGISTRY,[receipt]);assert resolve_profile(exe,c).mode=='openmp'

def test_unavailable_forced_profile(monkeypatch,tmp_path):
    monkeypatch.setenv('IGNIS_SOLVER','mpi4')
    with pytest.raises(FileNotFoundError): resolve_profile(tmp_path/'fds_openmp.exe',Experiment())


def test_auto_fallback_always_uses_measured_four_threads(monkeypatch,tmp_path):
    import backend.profiles as module
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    monkeypatch.setenv('IGNIS_SOLVER','auto');monkeypatch.setenv('IGNIS_THREADS','8')
    monkeypatch.setattr(module,'REGISTRY',tmp_path/'missing.json')
    profile=resolve_profile(exe,Experiment())
    assert profile.mode=='openmp' and profile.ranks==1 and profile.threads==4
    monkeypatch.setenv('IGNIS_SOLVER','openmp')
    assert resolve_profile(exe,Experiment()).threads==8

def fortran_record(data): return struct.pack('<i',len(data))+data+struct.pack('<i',len(data))

def test_partial_record_retries_without_losing_offset(tmp_path):
    path=tmp_path/'field.sf';shape=(3,3,3)
    values=np.arange(27,dtype='<f4').reshape(shape,order='F')
    payload=fortran_record(struct.pack('<f',.1))+fortran_record(values.tobytes(order='F'))
    path.write_bytes(b'\0'*146+payload[:-3]);s=SliceStream(path,shape)
    assert s.peek() is None;assert s.offset==146
    with path.open('ab') as f: f.write(payload[-3:])
    t,data=s.peek();assert t==pytest.approx(.1);np.testing.assert_array_equal(data,values[1:,1:,1:])
    assert s.peek()[1] is data

def test_record_corruption_rejected(tmp_path):
    path=tmp_path/'field.sf';path.write_bytes(b'\0'*146+fortran_record(struct.pack('<f',.1))+struct.pack('<i',99))
    with pytest.raises(ValueError): SliceStream(path,(3,3,3)).peek()

def test_delayed_field_waits_for_all_channels(tmp_path):
    c=Experiment();p=SimpleNamespace(identity=lambda:{},ranks=1)
    pipe=ProgressiveConverter(tmp_path,c,p,'a'*20,'b'*32)
    # Small synthetic mesh isolates atomic publication from FDS availability.
    pipe.meta['dimensions']=[2,2,2];pipe.streams=[]
    record=fortran_record(struct.pack('<f',0))+fortran_record(np.arange(27,dtype='<f4').tobytes())
    for channel in range(7):
        path=tmp_path/f'{channel}.sf';path.write_bytes(b'\0'*146+(record if channel<6 else record[:-2]))
        pipe.streams.append((channel,(slice(0,2),)*3,SliceStream(path,(3,3,3))))
    assert pipe.drain()==0;assert not list((tmp_path/'preview/frames').glob('*.bin'))
    with (tmp_path/'6.sf').open('ab') as f:f.write(record[-2:])
    assert pipe.drain()==1
    manifest=json.loads((tmp_path/'preview/manifest.json').read_text())
    assert manifest['times']==[0];assert manifest['revision']==1
    assert (tmp_path/'preview/frames/00000.bin').stat().st_size==2*2*2*7*4

def test_engine_initialization_failure_releases_lease(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path)
    class Broken:
        def __init__(self):raise OSError('Job Object failed')
    monkeypatch.setattr(engine_module,'ProcessTree',Broken)
    e=Engine();job=e.create(Experiment(duration=1,fuel=.123));wait_engine(e)
    assert e.status(job['id'])['status']=='failed';assert e.lease is None
    two=Engine();two._lease();two._release()

def test_thread_start_failure_releases_lease(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path)
    def broken(self): raise RuntimeError('thread unavailable')
    monkeypatch.setattr(threading.Thread,'start',broken)
    e=Engine()
    with pytest.raises(RuntimeError,match='thread unavailable'):e.create(Experiment())
    assert e.active is None and e.lease is None
    two=Engine();two._lease();two._release()
    e.worker=None

def test_cancel_before_start_does_not_spawn(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path)
    original=engine_module.ProgressiveConverter
    class CancelPipeline(original):
        def __init__(self,*args):super().__init__(*args);e.stop_event.set()
    monkeypatch.setattr(engine_module,'ProgressiveConverter',CancelPipeline)
    e=Engine();job=e.create(Experiment());wait_engine(e)
    assert e.status(job['id'])['status']=='cancelled'
    assert not (e.folder(job['id'])/'result.json').exists()
    first=e.folder(job['id']);second=e.create(Experiment());wait_engine(e)
    assert e.folder(second['id'])!=first and first.is_dir()

@pytest.mark.skipif(os.name!='nt',reason='Windows x64 integration')
def test_job_terminates_children_and_closes_handles(tmp_path):
    pidfile=tmp_path/'child.pid'
    child="import time;time.sleep(60)"
    parent=f"import subprocess,sys,time;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c',{child!r}]);Path({str(pidfile)!r}).write_text(str(p.pid));time.sleep(60)"
    with (tmp_path/'log').open('wb') as log:
        tree=ProcessTree().start([sys.executable,'-c',parent],tmp_path,os.environ.copy(),log)
        deadline=time.monotonic()+5
        while not pidfile.exists() and time.monotonic()<deadline:time.sleep(.02)
        assert pidfile.exists();pid=int(pidfile.read_text())
        tree.terminate();tree.wait();assert tree.poll()!=0
        api=tree.api.dll;api.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];api.OpenProcess.restype=ctypes.c_void_p
        handle=api.OpenProcess(0x100000,False,pid)
        if handle:
            assert api.WaitForSingleObject(handle,0)==0;api.CloseHandle(handle)
        tree.close();tree.close();assert tree.handle is None and tree.job is None

@pytest.mark.skipif(os.name!='nt',reason='Windows x64 integration')
def test_assignment_failure_never_resumes_child(monkeypatch,tmp_path):
    flag=tmp_path/'executed'
    tree=ProcessTree();original=tree.api.dll.AssignProcessToJobObject
    monkeypatch.setattr(tree.api.dll,'AssignProcessToJobObject',lambda *args:0)
    with (tmp_path/'log').open('wb') as log:
        with pytest.raises(OSError):tree.start([sys.executable,'-c',f'from pathlib import Path;Path({str(flag)!r}).touch()'],tmp_path,os.environ.copy(),log)
    assert not flag.exists();assert tree.handle is None and tree.job is None

def test_preview_api_attempt_isolation(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path)
    ident='a'*20;old='b'*32;new='c'*32
    for attempt,value in [(old,b'old'),(new,b'new')]:
        folder=tmp_path/ident/'attempts'/attempt;(folder/'preview/frames').mkdir(parents=True)
        atomic_json(folder/'preview/manifest.json',dict(times=[0],attempt=attempt))
        (folder/'preview/frames/00000.bin').write_bytes(value)
    atomic_json(tmp_path/ident/'latest.json',dict(attempt=new))
    client=TestClient(app)
    assert client.get(f'/api/experiments/{ident}/preview/manifest').json()['attempt']==new
    assert client.get(f'/api/experiments/{ident}/preview/frames/0?attempt={old}').content==b'old'
    assert client.get(f'/api/experiments/{ident}/preview/frames/0?attempt={new}').content==b'new'
    assert client.get(f'/api/experiments/{ident}/preview/frames/1?attempt={new}').status_code==404
    assert client.get(f'/api/experiments/{ident}/preview/frames/0?attempt=../foo').status_code==404


def test_completed_status_restores_profile_after_server_restart(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path)
    ident='d'*20;attempt='e'*32;folder=tmp_path/ident/'attempts'/attempt
    folder.mkdir(parents=True)
    profile=dict(version='execution-2',mode='mpi4',ranks=4,threads=1)
    config=Experiment(scene='candle',duration=6).canonical()
    atomic_json(tmp_path/ident/'latest.json',dict(attempt=attempt))
    atomic_json(folder/'result.json',dict(id=ident,attempt=attempt,profile=profile,
                                        config=config,elapsed=123,times=[0,.1,6]))
    status=Engine().status(ident)
    assert status['status']=='completed' and status['cached'] is True
    assert status['profile']==profile and status['attempt']==attempt
    assert status['config']==config and status['physicalTime']==6
    assert status['previewFrames']==3

@pytest.mark.skipif(os.name!='nt',reason='Windows x64 integration')
def test_abrupt_owner_exit_kills_owned_solver(tmp_path):
    pidfile=tmp_path/'solver.pid'
    child='import time;time.sleep(60)'
    code=f'''from backend.runner import ProcessTree
from pathlib import Path
import os,sys,time
log=Path({str(tmp_path/'log')!r}).open('wb')
tree=ProcessTree().start([sys.executable,'-c',{child!r}],Path.cwd(),os.environ.copy(),log)
Path({str(pidfile)!r}).write_text(str(os.getpid())+','+str(tree.pid))
time.sleep(60)
'''
    owner=subprocess.Popen([sys.executable,'-c',code],cwd=engine_module.ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline=time.monotonic()+5
        while not pidfile.exists() and time.monotonic()<deadline:time.sleep(.02)
        assert pidfile.exists();owner_pid,pid=map(int,pidfile.read_text().split(','))
        api=WindowsAPI().dll;handle=api.OpenProcess(0x100000,False,pid)
        assert handle
        try:
            # The venv Python launcher has a separate interpreter child.
            # Terminate the interpreter owning the job, not merely its stub.
            owner_handle=api.OpenProcess(0x1,False,owner_pid)
            assert owner_handle
            try:assert api.TerminateProcess(owner_handle,1)
            finally:api.CloseHandle(owner_handle)
            assert api.WaitForSingleObject(handle,5000)==0
        finally:api.CloseHandle(handle)
    finally:
        if owner.poll() is None:owner.kill()
        owner.wait(timeout=5)

def test_numeric_gate_rejects_oxygen_energy_and_velocity_regressions(tmp_path):
    from backend.validation import compare
    c=Experiment(duration=1)
    times=np.linspace(0,1,11).tolist()
    meta=dict(config=c.canonical(),dimensions=[2,2,4],coordinates=dict(x=[0,.1],y=[0,.1],z=[0,.1,.2,.3]),times=times,
              series=dict(Time=times,HRR=[1]*11),devices={},profile=dict(ranks=1))
    reference=tmp_path/'ref';candidate=tmp_path/'candidate'
    values=np.zeros((4,2,2,7),dtype='<f4');values[...,0]=200;values[...,1]=100;values[...,3]=.209
    for folder in [reference,candidate]:
        (folder/'frames').mkdir(parents=True);atomic_json(folder/'result.json',meta)
        for i in range(11):values.tofile(folder/'frames'/f'{i:05d}.bin')
    assert compare(reference,candidate)['passed']
    changed=values.copy();changed[...,3]+=.01;changed[...,4]=.02
    for i in range(11):changed.tofile(candidate/'frames'/f'{i:05d}.bin')
    check=compare(reference,candidate)
    assert not check['passed'] and not check['fields'][3]['passed'] and not check['fields'][4]['passed']
    meta['series']['HRR']=[1.2]*11;atomic_json(candidate/'result.json',meta)
    assert compare(reference,candidate)['energyError']==pytest.approx(.2)

class FakeTree:
    def __init__(self):self.pid=1;self.code=None;self.closed=False
    def start(self,command,cwd,env,log):log.write(b'STOP: FDS completed successfully');return self
    def poll(self):return self.code
    def telemetry(self):return {}
    def terminate(self):self.code=1
    def wait(self):return self.code
    def close(self):self.closed=True

def test_benchmark_start_failure_preserves_original_error(monkeypatch,tmp_path):
    import scripts.benchmark as benchmark
    class FailedStart(FakeTree):
        stopped=True
        def start(self,*args):raise OSError('assignment failed; handles already closed')
        def terminate(self):raise AssertionError('closed tree must not be terminated again')
        def wait(self):raise AssertionError('closed handles must not be polled')
    tree=FailedStart()
    monkeypatch.setattr(benchmark,'ProcessTree',lambda:tree)
    profile=SimpleNamespace(ranks=1,identity=lambda:{},command=lambda:['unavailable.exe'],environment=lambda:{})
    with pytest.raises(OSError,match='assignment failed'):
        benchmark.run(Experiment(),profile,tmp_path,1)
    assert tree.closed


def test_timeout_terminates_tree_and_releases_lease(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path);monkeypatch.setenv('IGNIS_TIMEOUT','.01')
    tree=FakeTree();monkeypatch.setattr(engine_module,'ProcessTree',lambda:tree)
    e=Engine();job=e.create(Experiment());wait_engine(e)
    assert e.status(job['id'])['status']=='failed'
    assert 'limit' in e.status(job['id'])['error'] and tree.closed
    assert e.lease is None

def test_cancel_during_final_conversion_never_publishes_result(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path)
    tree=FakeTree();tree.code=0;monkeypatch.setattr(engine_module,'ProcessTree',lambda:tree)
    original=ProgressiveConverter
    class CancelConversion(original):
        def drain(self,*args,**kwargs):
            if kwargs.get('final'):e.stop_event.set()
            return 0
    monkeypatch.setattr(engine_module,'ProgressiveConverter',CancelConversion)
    e=Engine();job=e.create(Experiment());wait_engine(e)
    assert e.status(job['id'])['status']=='cancelled'
    folder=e.folder(job['id']);assert not (folder/'result.json').exists()
    manifest=json.loads((folder/'preview/manifest.json').read_text(encoding='utf-8'))
    assert manifest['status']=='cancelled' and manifest['complete'] is False
    assert tree.closed and e.lease is None

def test_cancel_after_commit_cannot_change_completed_state():
    e=Engine();ident='a'*20;e.active=ident;e.jobs[ident]=dict(id=ident,status='completed',progress=1)
    assert e.cancel(ident)['status']=='completed'
    assert not e.stop_event.is_set()
    e.active=None

def test_metadata_cleanup_failure_does_not_keep_solver_lease(monkeypatch,tmp_path):
    monkeypatch.setattr(engine_module,'RUNS',tmp_path)
    tree=FakeTree();tree.code=0;monkeypatch.setattr(engine_module,'ProcessTree',lambda:tree)
    class BrokenMetadata(ProgressiveConverter):
        def finish(self,*args,**kwargs):raise OSError('metadata storage failed')
    monkeypatch.setattr(engine_module,'ProgressiveConverter',BrokenMetadata)
    e=Engine();job=e.create(Experiment());wait_engine(e)
    assert e.status(job['id'])['status']=='failed' and e.lease is None

@pytest.mark.skipif(os.name!='nt',reason='Windows reader sharing semantics')
def test_atomic_manifest_survives_brief_windows_reader(tmp_path):
    path=tmp_path/'manifest.json';atomic_json(path,{'revision':1})
    errors=[]
    def publish():
        try:atomic_json(path,{'revision':2})
        except Exception as exc:errors.append(exc)
    with path.open('r') as reader:
        worker=threading.Thread(target=publish);worker.start();time.sleep(.06)
        assert json.load(reader)=={'revision':1}
    worker.join(2);assert not worker.is_alive() and not errors
    assert json.loads(path.read_text())=={'revision':2}

@pytest.mark.parametrize('ranks',[1,2,4])
@pytest.mark.parametrize('quality',['preview','fine'])
def test_wood_rounded_smv_nodes_preserve_exact_fields(monkeypatch,tmp_path,ranks,quality):
    import backend.progressive as module
    from backend.progressive import QUANTITIES
    c=Experiment(scene='wood',quality=quality);bounds,dims=geometry(c)
    for name in ('ignis.smv','ignis_hrr.csv','ignis_steps.csv'):(tmp_path/name).write_text('0'*160+'\n')
    slices=[]
    for channel,quantity in enumerate(QUANTITIES):
        subs=[]
        for rank in range(ranks):
            shape=(dims[0]+1,dims[1]+1,dims[2]//ranks+1)
            offset=rank*(dims[2]//ranks)
            nodes={}
            for axis,a in enumerate('xyz'):
                full=np.linspace(bounds[axis*2],bounds[axis*2+1],dims[axis]+1)
                nodes[a]=np.round(full[offset:offset+shape[2]] if axis==2 else full,5)
            filename=f'{channel}-{rank}.sf'
            x,y,z=np.indices(shape)
            raw=(x+10*y+100*(z+offset)+10000*channel).astype('<f4')
            payload=fortran_record(struct.pack('<f',0))+fortran_record(raw.tobytes(order='F'))
            (tmp_path/filename).write_bytes(b'\0'*146+payload)
            subs.append(SimpleNamespace(mesh=SimpleNamespace(id=f'M{rank}'),filename=filename,
                                        dimension=SimpleNamespace(shape=lambda cell_centered=False,s=shape:s),
                                        get_coordinates=lambda ignore_cell_centered=False,n=nodes:n))
        slices.append(SimpleNamespace(quantity=SimpleNamespace(name=quantity),subslices=subs))
    monkeypatch.setattr(module.fdsreader,'Simulation',lambda path:SimpleNamespace(slices=slices,obstructions=[]))
    profile=SimpleNamespace(ranks=ranks,identity=lambda:{'ranks':ranks})
    pipe=ProgressiveConverter(tmp_path,c,profile,'a'*20,'b'*32)
    assert pipe.initialize(final=True)
    assert pipe.drain()==1
    frame=np.fromfile(tmp_path/'preview/frames/00000.bin',dtype='<f4').reshape(tuple(dims[::-1])+(7,))
    z,y,x=np.indices(tuple(dims[::-1]))
    expected=x+1+10*(y+1)+100*(z+1)
    for channel in range(7):np.testing.assert_array_equal(frame[...,channel],expected+10000*channel)
    # A real displacement is still rejected; only printed coordinate precision
    # is accommodated, never a shifted mesh or altered field values.
    slices[0].subslices[0].get_coordinates()['z'][1]+=(bounds[5]/dims[2])*.2
    pipe.streams=None
    with pytest.raises(ValueError,match='geometria'):pipe.initialize()
