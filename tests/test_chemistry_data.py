"""Portable provenance and conservation checks; Cantera stays an isolated tool."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src/gpu/chemistry/data'


def test_gri30_provenance_and_complete_reaction_families():
    provenance = json.loads((DATA/'provenance.json').read_text())
    assert hashlib.sha256((DATA/'gri30.yaml').read_bytes()).hexdigest() == provenance['sha256'] == '06650b1e0ee0012f6903d5328b1bb218cb6007d07f8ebe375d18f24811039345'
    table = json.loads((DATA/'mechanism.json').read_text())
    values = np.array(table['data'])
    assert len(table['species']) == len(set(table['species'])) == 53
    assert tuple(values[:2]) == (53, 325)
    assert len(values) == 852+325*112 and np.isfinite(values).all()
    reactions = values[852:].reshape(325, 112)
    assert np.bincount(reactions[:, 0].astype(int)).tolist() == [275, 21, 26, 3]
    assert np.count_nonzero(reactions[:, 103]) > 0


def test_every_exported_reaction_conserves_molecular_mass():
    values = np.array(json.loads((DATA/'mechanism.json').read_text())['data'])
    weights = values[4:57]
    for reaction in values[852:].reshape(325, 112):
        count = int(reaction[102])
        indices = reaction[86:86+2*count:2].astype(int)
        coefficients = reaction[87:87+2*count:2]
        mass = weights[indices]*coefficients
        assert abs(mass.sum()) <= 1e-12*max(1, np.abs(mass).sum())


def test_reactor_references_are_adiabatic_and_start_without_seeded_radicals():
    references = json.loads((ROOT/'tests/gpu/reactor-fixtures.json').read_text())
    species = json.loads((DATA/'mechanism.json').read_text())['species']
    assert references['model'] == 'adiabatic constant pressure'
    assert len(references['cases']) == 10
    for case in references['cases']:
        for name in ['H', 'O', 'OH', 'HO2', 'CH3']:
            assert case['initial'][species.index(name)+1] == 0
        assert case['points'][-1]['time'] == case['horizon']
        assert case['ignitionCensored'] == (case['ignitionTime'] is None)
        for point in case['points']:
            assert abs(point['enthalpy']-case['h0'])/max(1, abs(case['h0'])) <= 1e-5
            assert abs(sum(point['state'][1:])-1) <= 1e-8
