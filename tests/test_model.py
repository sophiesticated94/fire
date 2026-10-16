import json
from pathlib import Path
import time
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.models import Experiment, make_deck, geometry
from backend.engine import Engine, ROOT, solver_path
from backend.app import app


def test_validation_and_cache_identity():
    with pytest.raises(ValidationError): Experiment(fuel=-1)
    with pytest.raises(ValidationError): Experiment(oxygen=100)
    with pytest.raises(ValidationError): Experiment(duration=float('nan'))
    assert Experiment(scene='wood',fuel=1).key()==Experiment(scene='wood',fuel=20).key()
    assert Experiment(fuel=1).key()!=Experiment(fuel=2).key()
    assert Experiment(quality='fine').key()!=Experiment().key()


@pytest.mark.parametrize('scene',['burner','candle','wood'])
def test_deck_and_mesh(scene):
    preview=Experiment(scene=scene)
    fine=preview.model_copy(update={'quality':'fine'})
    bounds,cells=geometry(preview)
    assert geometry(fine)[0]==bounds
    assert all(b==int(a*1.5) for a,b in zip(cells,geometry(fine)[1]))
    deck=make_deck(preview)
    assert deck.count('&SLCF')==7
    assert 'CELL_CENTERED=.TRUE.' in deck
    assert '&TAIL /' in deck
    assert ('MATL_ID' in deck)==(scene=='wood')


@pytest.mark.parametrize('scene,rate',[('burner',12),('candle',1.2)])
def test_mass_flux_preserves_fuel_rate(scene,rate):
    # Parse precisely the quantities emitted in our controlled deck.
    import re
    for quality in ['preview','fine']:
        c=Experiment(scene=scene,fuel=rate,quality=quality)
        text=make_deck(c)
        surf=re.search(r'MASS_FLUX(?:\(1:3\))?=([^/]+)',text).group(1)
        flux=float(surf.split(',')[0])
        coords=[float(v) for v in re.search(r'&OBST XB=([^,]+,[^,]+,[^,]+,[^,]+,[^,]+,[^,]+), SURF_IDS',text).group(1).split(',')]
        area=(coords[1]-coords[0])*(coords[3]-coords[2])
        assert flux*area==pytest.approx(rate*1e-6)
        if quality=='preview': reference=coords
        else: assert coords==pytest.approx(reference)


def test_native_data_transport_matches_fds():
    # The first real 1-second solver run is retained as a regression fixture.
    candidates=list((ROOT/'runs').glob('*/result.json'))
    if not candidates: pytest.skip('Run a native experiment first')
    meta=json.loads(candidates[0].read_text(encoding='utf-8'))
    folder=candidates[0].parent
    import fdsreader
    sim=fdsreader.Simulation(str(folder))
    sl=next(s for s in sim.slices if s.quantity.name=='TEMPERATURE')
    native=sl.to_global()
    i=len(meta['times'])-1
    browser=np.fromfile(folder/'frames'/f'{i:05d}.bin',dtype='<f4').reshape(meta['dimensions'][2],meta['dimensions'][1],meta['dimensions'][0],7)
    np.testing.assert_array_equal(browser[...,0],native[i].transpose(2,1,0))
    assert browser[...,0].max()==pytest.approx(meta['extrema'][i]['temperature'])
    assert np.isfinite(browser).all()


def test_api_rejects_invalid_input_and_traversal():
    client=TestClient(app)
    assert client.get('/api/health').status_code==200
    assert client.post('/api/experiments',json={'fuel':-1}).status_code==422
    assert client.get('/api/experiments/not-an-id/result').status_code==404
    assert client.get('/api/experiments/00000000000000000000/frames/-1').status_code==404


def test_compressed_sample_frame(monkeypatch,tmp_path):
    import gzip
    import backend.engine as module
    ident='a'*20
    folder=tmp_path/ident
    (folder/'frames').mkdir(parents=True)
    (folder/'result.json').write_text('{}')
    payload=np.arange(70,dtype='<f4').tobytes()
    (folder/'frames/00000.bin.gz').write_bytes(gzip.compress(payload))
    monkeypatch.setattr(module,'SAMPLES',tmp_path)
    response=TestClient(app).get(f'/api/experiments/{ident}/frames/0')
    assert response.status_code==200
    assert response.headers['content-encoding']=='gzip'
    assert response.content==payload


def test_engine_missing_solver(monkeypatch,tmp_path):
    import backend.engine as module
    monkeypatch.setattr(module,'RUNS',tmp_path)
    monkeypatch.setattr(module,'solver_path',lambda:None)
    with pytest.raises(FileNotFoundError): Engine().create(Experiment())


def test_cross_process_lease_releases(monkeypatch,tmp_path):
    import backend.engine as module
    monkeypatch.setattr(module,'RUNS',tmp_path)
    one,two=Engine(),Engine()
    one._lease()
    try:
        with pytest.raises(RuntimeError): two._lease()
    finally: one._release()
    two._lease()
    two._release()


@pytest.mark.parametrize('mode',['openmp','mpi4'])
def test_cancellation_and_busy(monkeypatch,tmp_path,mode):
    import backend.engine as module
    monkeypatch.setattr(module,'RUNS',tmp_path)
    monkeypatch.setenv('IGNIS_SOLVER',mode)
    if not solver_path(): pytest.skip('Native FDS required')
    engine=Engine()
    job=engine.create(Experiment(duration=29,fuel=0))
    with pytest.raises(RuntimeError): engine.create(Experiment(duration=28,fuel=0))
    # Reach actual FDS execution, including all MPI ranks, before cancelling.
    deadline=time.monotonic()+12
    while engine.jobs[job['id']].get('physicalTime',0)<=0 and engine.active and time.monotonic()<deadline:time.sleep(.02)
    assert engine.jobs[job['id']].get('physicalTime',0)>0
    engine.cancel(job['id'])
    deadline=time.monotonic()+10
    while engine.active and time.monotonic()<deadline: time.sleep(.05)
    assert engine.active is None
    assert engine.status(job['id'])['status']=='cancelled'


def test_solver_failure_exposes_error(monkeypatch,tmp_path):
    import backend.engine as module
    monkeypatch.setattr(module,'RUNS',tmp_path)
    original=module.make_deck
    monkeypatch.setattr(module,'make_deck',lambda c,ranks=1:original(c,ranks).replace('IJK=32,32,64','IJK=0,0,0'))
    if not solver_path(): pytest.skip('Native FDS required')
    engine=Engine();job=engine.create(Experiment(duration=1))
    deadline=time.monotonic()+20
    while engine.active and time.monotonic()<deadline: time.sleep(.1)
    assert engine.status(job['id'])['status']=='failed'
    assert engine.status(job['id'])['error']
