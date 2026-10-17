"""Generate local SI tables and independent constant-pressure RHS/Jacobian fixtures."""
import hashlib
import json
import math
from pathlib import Path
import shutil
import cantera as ct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src/gpu/chemistry/data'
STRIDE = 112
YAML_SHA256 = '06650b1e0ee0012f6903d5328b1bb218cb6007d07f8ebe375d18f24811039345'


def rhs(gas, state):
    gas.TPY = state[0], ct.one_atm, state[1:]
    omega = gas.net_production_rates * gas.molecular_weights
    return np.r_[-np.dot(gas.partial_molar_enthalpies / gas.molecular_weights, omega) / (gas.density * gas.cp_mass), omega / gas.density]


def main():
    assert ct.__version__ == '3.2.0'
    OUT.mkdir(parents=True, exist_ok=True)
    original = Path(ct.get_data_directories()[-1]) / 'gri30.yaml'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == YAML_SHA256, 'Unreviewed mechanism data'
    shutil.copyfile(original, OUT / 'gri30.yaml')
    gas = ct.Solution(str(OUT / 'gri30.yaml'))
    assert (gas.n_species, gas.n_reactions) == (53, 325)
    nasa = []
    for sp in gas.species():
        coeff = sp.thermo.coeffs
        assert len(coeff) == 15
        nasa.extend([coeff[0], *coeff[8:15], *coeff[1:8]])
    tables = [53., 325., ct.gas_constant, ct.one_atm, *gas.molecular_weights, *nasa]
    kinds = {}
    for reaction in gas.reactions():
        assert len(reaction.reactants) <= 3 and len(reaction.products) <= 6
        assert all(v == int(v) for v in [*reaction.reactants.values(), *reaction.products.values()])
        d = np.zeros(STRIDE)
        kind = {'Arrhenius': 0, 'three-body-Arrhenius': 1, 'falloff-Troe': 2, 'falloff-Lindemann': 3}[reaction.reaction_type]
        kinds[reaction.reaction_type] = kinds.get(reaction.reaction_type, 0) + 1
        d[:4] = kind, reaction.reversible, len(reaction.reactants), len(reaction.products)
        high = reaction.rate if kind < 2 else reaction.rate.high_rate
        d[4:7] = math.log(high.pre_exponential_factor), high.temperature_exponent, high.activation_energy / ct.gas_constant
        if kind >= 2:
            low = reaction.rate.low_rate
            d[7:10] = math.log(low.pre_exponential_factor), low.temperature_exponent, low.activation_energy / ct.gas_constant
            if kind == 2:
                coefficients = reaction.rate.falloff_coeffs
                d[10:10 + len(coefficients)] = coefficients
        for start, terms in [(15, reaction.reactants), (21, reaction.products)]:
            for j, (species, count) in enumerate(terms.items()):
                d[start + 2*j:start + 2*j + 2] = gas.species_index(species), count
        if reaction.third_body:
            d[33:86] = reaction.third_body.default_efficiency
            for species, efficiency in reaction.third_body.efficiencies.items():
                d[33 + gas.species_index(species)] = efficiency
        net = gas.product_stoich_coeffs[:, len(tables[852:]) // STRIDE] - gas.reactant_stoich_coeffs[:, len(tables[852:]) // STRIDE]
        nz = np.flatnonzero(net)
        assert len(nz) <= 8
        for j, i in enumerate(nz):
            d[86 + 2*j:88 + 2*j] = i, net[i]
        d[102:104] = len(nz), reaction.duplicate
        tables.extend(d.tolist())
    (OUT / 'mechanism.json').write_text(json.dumps(dict(species=gas.species_names, data=tables), separators=(',', ':')), encoding='utf-8')
    provenance = dict(source='Cantera v3.2.0/data/gri30.yaml', url='https://github.com/Cantera/cantera/blob/v3.2.0/data/gri30.yaml', sha256=YAML_SHA256,
                      cantera=ct.__version__, species=53, reactions=325, kinds=kinds, stride=STRIDE,
                      units='m, s, kg, kmol, J, K; Arrhenius A converted by Cantera; Ea/R in K',
                      normalization='RHS uses Y/sum(Y); Jacobian differentiates this normalization at fixed pressure')
    (OUT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    fixtures = []
    for temperature in [300., 1000., 1500., 2500.]:
        for phi in [.5, 1., 2.]:
            gas.set_equivalence_ratio(phi, 'CH4', 'O2:1,N2:3.76')
            # Positive trace components permit independent central differences.
            y = gas.Y + 1e-7; y /= y.sum()
            state = np.r_[temperature, y]; reference = rhs(gas, state)
            jacobian = np.empty((54, 54))
            for j in range(54):
                epsilon = 1e-3 if j == 0 else 1e-9
                plus, minus = state.copy(), state.copy();plus[j] += epsilon;minus[j] -= epsilon
                jacobian[:, j] = (rhs(gas, plus) - rhs(gas, minus)) / (2*epsilon)
            fixtures.append(dict(T=temperature, phi=phi, state=state.tolist(), rhs=reference.tolist(), jacobian=jacobian.ravel().tolist()))
    target = ROOT / 'tests/gpu/chemistry-fixtures.json'
    target.write_text(json.dumps(fixtures, separators=(',', ':')), encoding='utf-8')
    print(json.dumps(provenance, indent=2))


if __name__ == '__main__':
    main()
