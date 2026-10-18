"""Independent BE is a diagnostic reference, not a production chemistry path."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest
import sys

pytest.importorskip('cantera')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('forensics',ROOT/'scripts/chemistry_forensics.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)


def initial():
    return np.array(json.loads((ROOT/'tests/gpu/reactor-fixtures.json').read_text())['cases'][8]['initial'])


def test_float64_be_preserves_enthalpy_and_reproduces_two_half_estimator():
    be=f.BackwardEuler();state=initial();h0=be.evaluate(state)[0]
    result=be.doubled(state,1e-7)
    full=np.array(result['full']['state']);half=np.array(result['secondHalf']['state'])
    expected=np.max(abs(full-half)/(f.TOL+f.RTOL*np.maximum(abs(full),abs(half))))
    assert result['estimator']==pytest.approx(expected)
    assert abs(be.evaluate(half)[0]-h0)/max(1,abs(h0))<1e-10
    assert min(half[1:])>=0


def test_backward_euler_converges_towards_independent_reactornet():
    be=f.BackwardEuler();state=initial();h0=be.evaluate(state)[0];end=1e-6
    net,reactor=f.network(state);net.advance(end);ref=np.r_[reactor.T,reactor.phase.Y]
    errors=[]
    for count in [1,2,4]:
        x=state.copy()
        for _ in range(count):x=np.array(be.step(x,end/count,h0)['state'])
        errors.append(np.linalg.norm(x-ref))
    assert errors[2]<errors[1]<errors[0]


def test_initial_rounding_and_trace_integrity_are_checked():
    state=initial();rounded=state.astype(np.float32).astype(float)
    report=f.analyze(dict(initial=state.tolist(),gpuInitial=rounded.tolist(),records=[]))
    assert report['acceptanceStatus']=='INCOMPLETE'
    assert report['historicalAcceptanceStatus']=='FAIL'
    assert report['diagnosisStatus']=='UNRESOLVED'
    bad=rounded.copy();bad[0]+=1
    with pytest.raises(ValueError,match='initial readback'):
        f.analyze(dict(initial=state.tolist(),gpuInitial=bad.tolist(),records=[]))
    with pytest.raises(ValueError,match='truncated'):
        f.analyze(dict(initial=state.tolist(),gpuInitial=rounded.tolist(),records=[{'sequence':1}]))


def test_chunk_manifest_detects_corruption(tmp_path):
    import hashlib
    chunk=tmp_path/'chunk.json'
    payload=json.dumps(dict(dropped=0,records=[dict(sequence=0)]),separators=(',',':'))
    raw=('{"schema":1,"sha256":"'+hashlib.sha256(payload.encode()).hexdigest()+'","payload":'+payload+'}').encode()
    chunk.write_bytes(raw)
    data=dict(traceFiles=[dict(path=str(chunk),sha256=hashlib.sha256(raw).hexdigest())])
    assert list(f.trace_records(data))==[dict(sequence=0)]
    chunk.write_bytes(raw+b' ')
    with pytest.raises(ValueError,match='integrity'):
        list(f.trace_records(data))


def test_time_refinement_uses_same_unnormalized_initial_state():
    from chemistry_schedule_reference import refinements
    state=initial();state[1:]*=1+3e-6
    result=refinements(dict(base=state.tolist(),dt=1e-6))
    errors=[r['weightedError'] for r in result['rows']]
    assert errors[-1]<errors[0]/4
    for row in result['rows']:
        assert sum(row['state'][1:])==pytest.approx(sum(state[1:]),abs=1e-12)


def test_effective_source_gate_checks_low_parts_and_all_species():
    from chemistry_effective_source import inspect_source
    be=f.BackwardEuler();state=initial().astype(np.float32).astype(float)
    reference=be.evaluate(state)
    values=np.zeros(3670);values[2970:3024]=state
    jac=values[:2970].reshape(54,55);jac[1:,54]=reference[1:]
    snapshot=dict(count=1,stride=3670,layout=dict(low=3342,lowCount=328),values=values.tolist())
    assert inspect_source(snapshot)['status']=='PASS'
    i=be.gas.species_index('NNH')+1
    defect=.002*max(abs(reference[i]),1e-8)
    jac[i,54]+=defect
    snapshot['values']=values.tolist()
    assert inspect_source(snapshot)['status']=='FAIL'
    values[3342+271+i]=-defect
    snapshot['values']=values.tolist()
    assert inspect_source(snapshot)['status']=='PASS'


def test_missing_inspection_is_incomplete_data_not_a_numerical_fail():
    from chemistry_effective_source import inspect_source
    with pytest.raises(ValueError,match='Incomplete inspection'):
        inspect_source(dict(count=0,stride=3342,layout={},values=[]))


def test_unanalyzed_accepted_event_cannot_claim_complete_trajectory_coverage():
    state=initial();rounded=state.astype(np.float32).astype(float)
    control=[0.]*40;control[8]=4
    after=control.copy();after[14]=1;after[8]=5
    # Deliberately inconsistent data: the observer must not claim it analyzed
    # all accepted events simply because the file sequence is contiguous.
    records=[dict(sequence=0,control=control),dict(sequence=1,control=after)]
    result=f.analyze(dict(initial=state.tolist(),gpuInitial=rounded.tolist(),records=records))
    assert result['completeTrace']
    assert not result['completeAcceptedCoverage']
    assert result['diagnosisStatus']=='UNRESOLVED'
