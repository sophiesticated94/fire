"""Float64 diagnostics for the same scaled constant-enthalpy Newton systems.

This does not solve chemistry for the application. Pivot ratios reported on the
GPU are not condition numbers; this independent diagnostic measures cond(A, inf).
"""
import json
from pathlib import Path

import cantera as ct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def rhs(gas, state):
    gas.TPY = state[0], ct.one_atm, state[1:]
    omega = gas.net_production_rates * gas.molecular_weights / gas.density
    return np.r_[gas.enthalpy_mass, omega]


def main():
    fixtures = json.loads((ROOT / 'tests/gpu/chemistry-fixtures.json').read_text())
    gas = ct.Solution(str(ROOT / 'src/gpu/chemistry/data/gri30.yaml'))
    rows = []
    for fixture in fixtures:
        state = np.array(fixture['state'])
        jac = np.empty((54, 54))
        for col in range(54):
            step = 1e-3 if col == 0 else 1e-9
            plus, minus = state.copy(), state.copy()
            plus[col] += step
            minus[col] -= step
            jac[:, col] = (rhs(gas, plus)-rhs(gas, minus))/(2*step)
        scale = np.r_[1e-3, np.full(53, 1e-12)] + 1e-5*np.abs(state)
        row_scale = scale.copy()
        row_scale[0] = max(1, abs(jac[0, 0])*scale[0])
        for dt in [1e-8, 1e-6, 1e-4]:
            matrix = np.eye(54)-dt*jac
            matrix[0] = jac[0]
            matrix *= scale[None, :]/row_scale[:, None]
            rows.append(dict(T=fixture['T'], phi=fixture['phi'], dt=dt,
                             conditionInfinity=float(np.linalg.cond(matrix, np.inf))))
    output = ROOT / 'artifacts/gpu-v14/conditioning.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(method='float64 central-difference Cantera; scaled DAE matrix; infinity norm', rows=rows), indent=2))
    print(f'{len(rows)} scaled systems; max condition {max(r["conditionInfinity"] for r in rows):.6g}')


if __name__ == '__main__':
    main()
