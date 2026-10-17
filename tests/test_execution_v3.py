import json
import os
from pathlib import Path
from types import SimpleNamespace
import zipfile
import numpy as np
import pytest
from backend.models import Experiment,geometry,make_deck
from backend.meshes import LAYOUTS,partition,interface_mask
from backend.incremental import Tail,CSVSeries,OutputProgress,Deadline
from backend.profiles import build_profile,resolve_profile
from backend.engine import solver_path,Engine
from backend.policy import validation_policy
from backend.progressive import atomic_json
from backend.validation_v3 import compare_v3
from backend.cpu import performance_cores

@pytest.mark.parametrize('layout',list(LAYOUTS))
@pytest.mark.parametrize('scene',['burner','candle','wood'])
@pytest.mark.parametrize('quality',['preview','fine'])
def test_integer_partitions_cover_once(scene,quality,layout):
    c=Experiment(scene=scene,quality=quality);bounds,dims=geometry(c)
    if any(n%sum(weights) for n,weights in zip(dims,LAYOUTS[layout])):
        with pytest.raises(ValueError):partition(dims,layout)
        return
    regions=partition(dims,layout);coverage=np.zeros(dims,dtype=np.uint8)
    for region in regions:
        assert region['process']<len(regions)
        coverage[tuple(slice(a,b) for a,b in zip(region['start'],region['end']))]+=1
    assert np.all(coverage==1)
    profile=SimpleNamespace(layout=layout)
    deck=make_deck(c,len(regions),profile=profile)
    assert deck.count('&MESH')==len(regions)
    # Only mesh records differ; physical source and boundaries are invariant.
    physical=lambda text:'\n'.join(line for line in text.splitlines() if not line.startswith('&MESH'))
    assert physical(deck)==physical(make_deck(c))
    mask=interface_mask(dims,layout)
    assert mask.shape==tuple(dims[::-1])
    assert bool(mask.any())==(len(regions)>1)

def test_real_xy_and_unequal_interfaces():
    mask=interface_mask([8,8,8],'xy22')
    assert mask[:,3:5,:].all() and mask[:,:,3:5].all()
    assert not mask[0,0,0]
    unequal=interface_mask([8,8,8],'z1124')
    for boundary in (1,2,4):assert unequal[boundary-1:boundary+1].all()
    assert not unequal[6].any()

def test_incremental_csv_partial_rotation_and_no_rereads(tmp_path):
    p=tmp_path/'series.csv';p.write_bytes(b's,kW\nTime,HRR\n0,0\n.1,2')
    series=CSVSeries(p);assert series.read()=={'Time':[0.],'HRR':[0.]}
    assert series.units=={'Time':'s','HRR':'kW'}
    consumed=series.tail.bytes_read
    assert series.read()['Time']==[0.];assert series.tail.bytes_read==consumed
    with p.open('ab') as f:f.write(b'\n')
    assert series.read()['HRR']==[0.,2.]
    p.write_bytes(b's,kW\nTime,HRR\n0,5\n')
    assert series.read()['HRR']==[5.]

def test_complete_invalid_csv_rejected(tmp_path):
    p=tmp_path/'a.csv';p.write_text('s,kW\nTime,HRR\n0,nan\n')
    with pytest.raises(ValueError,match='finite'):CSVSeries(p).read()

def test_progress_tail_and_deadline_do_not_repeat_window(tmp_path):
    p=tmp_path/'run.out';p.write_text('Step Size: .1, Total Ti')
    progress=OutputProgress(p);assert progress.read()==0
    with p.open('a') as f:f.write('me: 1.2\n')
    assert progress.read()==1.2
    old=progress.tail.bytes_read;assert progress.read()==1.2;assert progress.tail.bytes_read==old
    d=Deadline(2);assert d.due(0);assert not d.due(.1);assert not d.due(1.99);assert d.due(2.01);assert not d.due(2.9);assert d.due(8);assert not d.due(8.1)

def write_case(folder,config,times,velocity):
    (folder/'frames').mkdir(parents=True)
    meta=dict(config=config,dimensions=[2,2,4],coordinates=dict(x=[0,.1],y=[0,.1],z=[0,.1,.2,.3]),times=times,
              series=dict(Time=times,HRR=[1]*len(times)),devices={},profile=dict(ranks=1,layout='single'),complete=True)
    atomic_json(folder/'result.json',meta)
    for i,u in enumerate(velocity):
        data=np.zeros((4,2,2,7),dtype='<f4');data[...,0]=20;data[...,3]=.209;data[...,4]=u;data.tofile(folder/'frames'/f'{i:05d}.bin')

def test_temporal_error_detects_cancelling_trajectories(tmp_path):
    c=Experiment().model_copy(update={'duration':.3}).canonical();times=[0,.1,.2,.3]
    a=tmp_path/'a';b=tmp_path/'b';write_case(a,c,times,[0]*4);write_case(b,c,times,[.1,-.1,.1,-.1])
    result=compare_v3(a,b)
    assert result['legacy']['passed']
    assert result['temporal']['late'][4]['error']>1.9
    assert result['temporal']['full'][4]['error']>1.9
    assert result['status']=='pending-review' and result['promotionEligible'] is False
    assert not result['diagnosticsAvailable']

def test_no_extrapolation_or_incomplete_promotion(tmp_path):
    c=Experiment().model_copy(update={'duration':.3}).canonical()
    a=tmp_path/'a';b=tmp_path/'b';write_case(a,c,[0,.1,.2,.3],[0]*4);write_case(b,c,[0,.1,.2],[0]*3)
    with pytest.raises(ValueError,match='coverage'):compare_v3(a,b)
    meta=json.loads((a/'result.json').read_text());meta['complete']=False;atomic_json(a/'result.json',meta)
    with pytest.raises(ValueError,match='Incomplete'):compare_v3(a,a)

def test_cpu_classes_are_not_assumed_logical_numbers():
    records=[dict(group=0,core=10,logical=6,efficiency=2,flags=1),dict(group=0,core=10,logical=7,efficiency=2,flags=0),dict(group=0,core=2,logical=0,efficiency=0,flags=0)]
    assert performance_cores(records)==[6]
    with pytest.raises(ValueError,match='klas'):performance_cores([records[-1]])

@pytest.mark.parametrize('mode',['mpi2-x2','mpi4-y4','mpi4-xy22','mpi2-z13','mpi4-z1124','hybrid2x2-z'])
def test_profile_layouts_hybrid_and_cache(mode):
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    p=build_profile(exe,mode,threads=4);config=Experiment()
    assert p.version=='execution-3' and len(partition(geometry(config)[1],p.layout))==p.ranks
    assert config.key(p)!=config.key(build_profile(exe))
    assert p.diagnostics=='flux-1'
    if mode.startswith('hybrid'):
        assert p.ranks==2 and p.threads==2
        assert Path(p.executable).name=='fds_openmp.exe'
        assert p.environment()['OMP_NUM_THREADS']=='2'

def test_pending_policy_blocks_old_and_new_receipts(monkeypatch,tmp_path):
    import backend.profiles as p
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    monkeypatch.setenv('IGNIS_SOLVER','auto');monkeypatch.setattr(p,'REGISTRY',tmp_path/'registry.json')
    atomic_json(p.REGISTRY,[dict(mode='mpi4',passed=True,speedup=10,measuredRuns=3,median=1)])
    monkeypatch.setattr(p,'validation_policy',lambda:dict(approved=False,hash='pending'))
    assert resolve_profile(exe,Experiment(scene='candle',duration=2)).mode=='openmp'

@pytest.mark.parametrize('scene,duration',[('burner',2),('burner',6),('candle',2),('candle',6),('wood',15)])
def test_family_sampling_is_reproducible_and_bounded(scene,duration):
    from backend.families import family_points,BOXES
    points=family_points(scene,duration)
    assert points==family_points(scene,duration) and len(points)==17
    assert len({json.dumps(p,sort_keys=True) for p in points})==17
    for p in points:
        assert p['quality']=='preview' and p['duration']==duration
        for name,(lo,hi) in BOXES[scene].items():assert lo<=p[name]<=hi

def test_archive_rejects_zip_slip(tmp_path):
    from backend.run_data import open_run
    z=tmp_path/'bad.zip'
    with zipfile.ZipFile(z,'w') as f:f.writestr('../escape','bad')
    with pytest.raises(ValueError,match='Unsafe'):
        with open_run(z,tmp_path/'scratch'):pass
    assert not (tmp_path/'escape').exists()

def test_budget_reserves_before_launch(monkeypatch,tmp_path):
    from scripts.campaign_v3 import Campaign,BudgetStop
    from scripts import campaign_v3
    if not solver_path():pytest.skip('FDS required')
    monkeypatch.setattr(campaign_v3,'run',lambda *args,**kwargs:pytest.fail('native launch forbidden'))
    for hours,gib in [(0,4),(8,.01)]:
        c=Campaign(tmp_path/str(gib),hours,gib)
        try:
            with pytest.raises(BudgetStop):c.execute(Experiment(),'openmp','reference',0)
            assert not c.state['runs'] and c.state['active'] is None
        finally:c.close()

@pytest.mark.parametrize('mode',['mpi4-xy22','mpi2-x2','mpi4-y4','mpi4-z1124','hybrid2x2-z','openmp-pcores','hybrid2x2-z-pcores','mpi4-z4-pcores'])
def test_native_archive_reconstruction_is_exact(tmp_path,mode):
    from backend.run_data import archive_run,open_run,sha256
    from scripts.benchmark import run
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    lease=Engine();lease._lease()
    try:
        c=Experiment(fuel=0,duration=1)
        result=run(c,build_profile(exe,mode),tmp_path/'work',90)
    finally:lease._release()
    folder=Path(result['folder']);meta=json.loads((folder/'result.json').read_text())
    hashes={p.name:sha256(p) for p in (folder/'preview/frames').glob('*.bin')}
    if mode.endswith('-pcores'):
        allowed=sum(1<<cpu for cpu in build_profile(exe,mode).affinity)
        telemetry=result['telemetry']
        assert telemetry['observedProcessAffinity'] and telemetry['observedThreadAffinity']
        assert all(int(mask,16)&~allowed==0 for mask in telemetry['observedProcessAffinity'].values())
        assert all(int(t['mask'],16)&~allowed==0 for t in telemetry['observedThreadAffinity'].values())
    receipt=archive_run(folder,tmp_path/'native.zip',cleanup_root=tmp_path/'work')
    assert result['nativeExact'] and receipt['frames']==11 and not folder.exists()
    with open_run(receipt['path'],tmp_path/'scratch') as restored:
        assert {p.name:sha256(p) for p in (restored/'preview/frames').glob('*.bin')}==hashes
        assert json.loads((restored/'result.json').read_text())['meshLayout']==meta['meshLayout']
    if mode=='mpi4-xy22':
        before=sha256(receipt['path'])
        with open_run(receipt['path'],tmp_path/'scratch',fields_only=True) as restored:
            assert not list(restored.glob('*.sf')) and not (restored/'ignis.smv').exists()
            assert {p.name:sha256(p) for p in (restored/'preview/frames').glob('*.bin')}==hashes
        assert sha256(receipt['path'])==before
    assert not list((tmp_path/'scratch').iterdir())


def test_diagnostic_series_reject_missing_nan_or_unordered():
    from backend.validation_v3 import series_metrics
    ref={'Time':[0,1],'flux':[0,1]}
    for candidate in [{'Time':[0,1]}, {'Time':[0,1],'flux':[0,float('nan')]}, {'Time':[1,0],'flux':[0,1]}]:
        with pytest.raises(ValueError):series_metrics(ref,candidate)


def test_native_http_api_flow(tmp_path):
    from scripts.api_benchmark import run_api
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    result=run_api(Experiment(fuel=0,duration=1),build_profile(exe,'openmp',threads=4),tmp_path,90)
    assert result['nativeExact'] and result['transport']=='http-api'
    assert result['firstFrameSeconds'] is not None and result['backendIO']['outputBytesRead']>0


def test_empirical_family_requires_every_point_and_current_policy(monkeypatch,tmp_path):
    import backend.families as f
    import backend.profiles as p
    from backend.models import MODEL_VERSION,SOLVER_VERSION
    from backend.policy import VALIDATION_VERSION
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    monkeypatch.setenv('IGNIS_SOLVER','auto');monkeypatch.setattr(p,'REGISTRY',tmp_path/'missing-exact.json')
    monkeypatch.setattr(f,'REGISTRY',tmp_path/'families.json')
    policy=dict(approved=True,hash='reviewed');monkeypatch.setattr(p,'validation_policy',lambda:policy)
    profile=build_profile(exe,'mpi4-xy22',threads=4)
    points=[dict(config=config,passed=True,nativeExact=True,measuredRuns=3,referenceRuns=3,speedup=1.2,
                 signature=p.validation_signature(Experiment(**config),profile)) for config in f.family_points('burner',6)]
    entry=dict(scene='burner',duration=6,bounds=f.BOXES['burner'],validationVersion=VALIDATION_VERSION,policyHash=policy['hash'],
               hardware=p.hardware_id(),model=MODEL_VERSION,solver=SOLVER_VERSION,mode=profile.mode,profile=profile.identity(),points=points)
    atomic_json(f.REGISTRY,[entry]);config=Experiment(scene='burner',duration=6,oxygen=20.5,wind=.05)
    assert resolve_profile(exe,config).mode==profile.mode
    assert resolve_profile(exe,config.model_copy(update={'quality':'fine'})).mode=='openmp'
    assert resolve_profile(exe,config.model_copy(update={'fuel':20})).mode=='openmp'
    entry['points']=points[:-1];atomic_json(f.REGISTRY,[entry]);assert resolve_profile(exe,config).mode=='openmp'
    entry['points']=points;atomic_json(f.REGISTRY,[entry]);policy['approved']=False;assert resolve_profile(exe,config).mode=='openmp'


def test_manifest_http_is_consistent_during_atomic_publication(monkeypatch,tmp_path):
    import threading
    import time
    import backend.app as api
    from fastapi.testclient import TestClient
    (tmp_path/'preview').mkdir();path=tmp_path/'preview/manifest.json'
    atomic_json(path,dict(revision=0,padding='x'))
    monkeypatch.setattr(api.engine,'folder',lambda ident:tmp_path)
    stop=threading.Event();errors=[]
    def publish():
        i=0
        try:
            while not stop.wait(.002):
                i+=1;atomic_json(path,dict(revision=i,padding='x'*(1000*(1+i%2))))
        except BaseException as exc:errors.append(exc)
    writer=threading.Thread(target=publish);writer.start()
    try:
        client=TestClient(api.app)
        for _ in range(40):
            response=client.get('/api/experiments/test/preview/manifest')
            assert response.status_code==200 and response.headers['cache-control']=='no-store'
            assert int(response.headers['content-length'])==len(response.content)
            assert response.json()['revision']>=0
    finally:stop.set();writer.join(timeout=3)
    assert not writer.is_alive() and not errors


def test_api_affinity_applies_to_solver_not_parent_server(monkeypatch,tmp_path):
    import scripts.api_benchmark as api
    from types import SimpleNamespace
    captured={}
    class Tree:
        stopped=True
        def start(self,command,cwd,env,log):
            captured.update(env);raise RuntimeError('stop-before-start')
        def close(self):pass
    monkeypatch.setattr(api,'ProcessTree',Tree)
    profile=SimpleNamespace(mode='openmp-pcores',executable='fds_openmp.exe',threads=4,
                            environment=lambda:dict(IGNIS_CPU_MASK='0x55'))
    with pytest.raises(RuntimeError,match='stop-before-start'):api.run_api(Experiment(),profile,tmp_path,1)
    assert 'IGNIS_CPU_MASK' not in captured and captured['IGNIS_SOLVER']=='openmp-pcores'


def test_explicit_missing_binary_does_not_silently_benchmark_stock(monkeypatch,tmp_path):
    monkeypatch.setenv('IGNIS_FDS',str(tmp_path/'missing-custom-fds.exe'))
    assert solver_path() is None
    with pytest.raises(FileNotFoundError,match='IGNIS_FDS'):Engine().create(Experiment())


def test_sampled_diagnostics_use_actual_step_counter():
    from backend.diagnostics import profile_texts
    steps=' ,,s,s,s\nTime Step,Wall Time,Step Size,Simulation Time,CPU Time\n1,date,.01,.01,1\n100,date,.002,.2,10\n250,date,.001,.5,25\n'
    p=profile_texts(steps,'Maximum CFL Number : .9\n','Rank,DIVG,MASS\n0,25,50\n1,25,25\n')
    assert p['steps']==250 and p['recordedSteps']==3 and not p['allStepsRecorded']
    assert sum(b['count'] for b in p['histogram'])==3
    assert p['subsystemsPerStepEstimated']['DIVG']==pytest.approx(.2) and p['subsystemsPerStepEstimated']['MASS']==pytest.approx(.3)
    assert p['meanPhysicalStepSeconds']==.002
    complete=profile_texts(',,s,s,s\nTime Step,Wall Time,Step Size,Simulation Time,CPU Time\n1,date,.1,.1,1\n2,date,.1,.2,2\n','','')
    assert complete['allStepsRecorded'] and complete['steps']==2


def test_all_step_diagnostics_are_separate_from_production_profile():
    from dataclasses import replace
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    p=build_profile(exe,'openmp');instrumented=replace(p,diagnostics='flux-1-allsteps');c=Experiment(duration=2)
    normal=make_deck(c,profile=p,diagnostics=True);full=make_deck(c,profile=instrumented,diagnostics=True)
    assert 'DIAGNOSTICS_INTERVAL=1' in full
    assert normal==full.replace(', DIAGNOSTICS_INTERVAL=1','')
    assert c.key(p)!=c.key(instrumented)


def test_native_peak_reserves_native_export_and_archive():
    from scripts.campaign_v3 import native_peak,estimated_bytes
    c=Experiment(scene='wood',duration=15);working=estimated_bytes(c)
    archive_bound=working//2+32*1024**2
    assert native_peak(c)==archive_bound+working


def test_fields_only_cleanup_never_removes_original_run(monkeypatch,tmp_path):
    import backend.progressive as progressive
    from backend.run_data import archive_run,open_run,sha256
    original=tmp_path/'original';(original/'preview/frames').mkdir(parents=True)
    data=b'unchanged-export';(original/'preview/frames/00000.bin').write_bytes(data)
    (original/'native.sf').write_bytes(b'original-native')
    atomic_json(original/'result.json',dict(id='a'*20,config=Experiment(duration=1).canonical(),profile=dict(ranks=1),frameDirectory='preview/frames'))
    receipt=archive_run(original,tmp_path/'run.zip')
    class Converter:
        def __init__(self,folder,*args):self.folder=folder
        def drain(self,**kwargs):
            (self.folder/'preview/frames').mkdir(parents=True,exist_ok=True)
            (self.folder/'preview/frames/00000.bin').write_bytes(data)
    monkeypatch.setattr(progressive,'ProgressiveConverter',Converter)
    with open_run(original,fields_only=True) as folder:assert (folder/'native.sf').read_bytes()==b'original-native'
    with open_run(receipt['path'],tmp_path/'scratch',fields_only=True) as folder:
        assert not (folder/'native.sf').exists()
        assert (folder/'preview/frames/00000.bin').read_bytes()==data
    assert (original/'native.sf').read_bytes()==b'original-native' and sha256(receipt['path'])==receipt['sha256']


def test_native_all_step_profile_covers_every_solver_step(tmp_path):
    from dataclasses import replace
    from backend.diagnostics import profile_steps
    from scripts.benchmark import run
    exe=solver_path()
    if not exe:pytest.skip('FDS required')
    p=replace(build_profile(exe,'openmp',threads=4),diagnostics='flux-1-allsteps')
    lease=Engine();lease._lease()
    try:r=run(Experiment(fuel=0,duration=1),p,tmp_path/'work',90)
    finally:lease._release()
    profile=profile_steps(r['folder'])
    assert r['nativeExact'] and profile['allStepsRecorded']
    assert profile['steps']==r['steps']==profile['recordedSteps']


def test_numerical_report_keeps_missing_pairs_and_native_units_visible(tmp_path):
    from scripts.report_campaign_validation import report,comparison_path
    from backend.policy import validation_policy
    reference=dict(config=Experiment(duration=2).canonical(),iteration=1,phase='reference',profile=dict(mode='openmp'),archive=dict(sha256='reference'))
    other=dict(reference,iteration=2,archive=dict(sha256='other'))
    candidate=dict(reference,phase='screen',iteration=-1,profile=dict(mode='mpi2-x2'),archive=dict(sha256='candidate'))
    atomic_json(tmp_path/'campaign.json',dict(runs=[reference,other,candidate]))
    p=comparison_path(tmp_path,reference,candidate,validation_policy()['hash']);p.parent.mkdir()
    atomic_json(p,dict(legacy=dict(passed=False,energyError=.06,ignitionErrorSeconds=None),
        temporal={k:[] for k in ('full','late','interfacesFull','interfacesLate','variability')},
        devices=dict(mdot_X1=dict(rms=.2,unit='kg/s'),pressure_X1_lo=dict(rms=.3,unit='Pa'))))
    output=tmp_path/'report.md';counts=report(tmp_path,output);text=output.read_text(encoding='utf-8')
    assert counts==dict(compared=1,missing=2)
    assert 'FAIL' in text and 'kg/s' in text and 'Pa' in text and 'pending-review' in text
    assert 'brakujące pary: 2' in text
    data=json.loads((tmp_path/'benchmark-v3-data.json').read_text(encoding='utf-8'))
    assert data['missingPairs']==2 and len(data['comparisons'])==1
    assert data['runs'][0]['archive']==dict(sha256='reference') and 'folder' not in data['runs'][0]


def test_single_thread_openmp_retains_the_requested_solver_binary(tmp_path):
    exe=tmp_path/'fds_openmp.exe';exe.write_bytes(b'openmp executable')
    profile=build_profile(exe,'openmp',threads=1)
    assert Path(profile.executable)==exe.resolve() and profile.threads==1 and profile.ranks==1


def test_analysis_checks_actual_disk_budget_before_extracting(monkeypatch,tmp_path):
    from scripts import campaign_v3
    c=campaign_v3.Campaign.__new__(campaign_v3.Campaign)
    c.root=tmp_path;c.bytes=1;c.seconds=3600;c.used_seconds=lambda:0;c.save=lambda:None
    calls=[]
    monkeypatch.setattr(campaign_v3.shutil,'disk_usage',lambda _:SimpleNamespace(free=100*1024**3))
    monkeypatch.setattr(campaign_v3,'compare_v3',lambda *args:calls.append(args) or dict(status='pending-review'))
    record=dict(config=Experiment(scene='wood',duration=15).canonical(),folder='not-extracted',archive=dict(sha256='a'))
    with pytest.raises(campaign_v3.BudgetStop,match='analysis disk'):c.compare(record,record)
    assert not calls
    c.bytes=4*1024**3
    assert c.compare(record,record)==dict(status='pending-review') and len(calls)==1


def test_partial_campaign_summarizes_completed_screens_without_finalists():
    from scripts.campaign_v3 import Campaign
    c=Campaign.__new__(Campaign);record=dict(phase='screen',iteration=-1)
    c.state=dict(runs=[record]);calls=[];c.screen_score=lambda r:calls.append(r);c.save=lambda:None
    c.summarize()
    assert calls==[record] and c.state['summaries']==[]


def test_manifest_snapshot_retries_transient_windows_publication(monkeypatch,tmp_path):
    from backend.progressive import snapshot_bytes
    path=tmp_path/'manifest.json'
    path.write_bytes(b'{"revision":2}')
    original=Path.read_bytes
    attempts=[]
    def read(candidate):
        if candidate==path and len(attempts)<2:
            attempts.append(True)
            raise PermissionError('delete pending')
        return original(candidate)
    monkeypatch.setattr(Path,'read_bytes',read)
    assert snapshot_bytes(path)==b'{"revision":2}' and len(attempts)==2
