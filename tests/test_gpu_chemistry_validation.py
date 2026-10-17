"""Acceptance checks must detect transient defects and never promote partial runs."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip('cantera')
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gpu_validation',ROOT/'scripts/validate_gpu_chemistry.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def partial():
    f=json.loads((ROOT/'tests/gpu/reactor-fixtures.json').read_text())['cases'][8]
    ctl=[0.]*40
    ctl[0]=1e-7;ctl[8]=1;ctl[20]=2
    return dict(caseIds=[8],checkpoint=dict(
        mechanismSha256=json.loads((ROOT/'src/gpu/chemistry/data/provenance.json').read_text())['sha256'],
        precision='float32',initial=[f['initial']],accepted=[f['points'][1]['state']],control=ctl,
        trajectory=f['points'][0]['state']+f['points'][1]['state'],sampleTimes=[1e-8,1e-7],duration=f['horizon']))


def test_reference_partial_is_not_complete():
    result=module.validate(partial())
    assert result['status']=='INCOMPLETE'
    assert result['reactors'][0]['pointPass']


def test_transient_radical_defect_is_not_hidden_by_correct_final_state():
    data=partial()
    # Only the first sampled OH value is wrong; final composition stays correct.
    species=json.loads((ROOT/'src/gpu/chemistry/data/mechanism.json').read_text())['species']
    data['checkpoint']['trajectory'][species.index('OH')+1]+=1e-9
    result=module.validate(data)
    assert result['status']=='FAIL'
    assert result['reactors'][0]['metrics']['radicalWeighted']>1


def test_shortened_horizon_and_done_flag_cannot_promote_gate():
    data=partial();data['checkpoint']['duration']=1e-7;data['checkpoint']['control'][8]=5
    assert module.validate(data)['status']=='INCOMPLETE'


def test_initial_state_identity_is_verified():
    data=copy.deepcopy(partial());data['checkpoint']['initial'][0][0]+=1
    with pytest.raises(ValueError,match='identity'):
        module.validate(data)
