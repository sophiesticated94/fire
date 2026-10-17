"""Independent float64 Cantera reactors; never a replacement GPU chemistry path."""
import json
from pathlib import Path

import cantera as ct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    assert ct.__version__ == '3.2.0'
    cases = []
    for temperature, horizon in [(500., 1.), (1000., 10.), (1200., 2.), (1500., .5)]:
        for phi in ([1.] if temperature == 500 else [.5, 1., 2.]):
            gas = ct.Solution(str(ROOT / 'src/gpu/chemistry/data/gri30.yaml'))
            gas.set_equivalence_ratio(phi, 'CH4', 'O2:1,N2:3.76')
            gas.TP = temperature, ct.one_atm
            initial = [temperature, *gas.Y.tolist()]
            h0 = gas.enthalpy_mass
            elements = [gas.elemental_mass_fraction(e) for e in gas.element_names]
            reactor = ct.IdealGasConstPressureReactor(gas, clone=True)
            network = ct.ReactorNet([reactor])
            network.rtol, network.atol = 1e-10, 1e-20
            points = []
            for time in sorted(set([1e-8, 1e-7, 1e-6, 1e-5, 1e-4, *np.geomspace(1e-3, horizon, 160)])):
                network.advance(float(time))
                phase = reactor.phase
                points.append(dict(time=float(time), state=[phase.T, *phase.Y.tolist()],
                                   enthalpy=phase.enthalpy_mass,
                                   elements=[phase.elemental_mass_fraction(e) for e in phase.element_names]))
            # Independent adaptive-step threshold detection, not inferred from a final temperature.
            gas.TPY = temperature, ct.one_atm, initial[1:]
            ignition_reactor = ct.IdealGasConstPressureReactor(gas, clone=True)
            ignition_net = ct.ReactorNet([ignition_reactor])
            ignition_net.rtol, ignition_net.atol = 1e-10, 1e-20
            previous_time, previous_T, ignition = 0., temperature, None
            while ignition_net.time < horizon:
                time = ignition_net.step()
                current_T = ignition_reactor.T
                if current_T >= temperature + 400:
                    crossing = previous_time + (time-previous_time)*(temperature+400-previous_T)/(current_T-previous_T)
                    if crossing <= horizon:
                        ignition = crossing
                    break
                previous_time, previous_T = time, current_T
            cases.append(dict(T=temperature, phi=phi, horizon=horizon, initial=initial,
                              h0=h0, elements=elements, ignitionTime=ignition,
                              ignitionCensored=ignition is None, points=points))
    destination = ROOT / 'tests/gpu/reactor-fixtures.json'
    destination.write_text(json.dumps(dict(cantera=ct.__version__, pressure=ct.one_atm,
        rtol=1e-10, atol=1e-20, model='adiabatic constant pressure', cases=cases), separators=(',', ':')), encoding='utf-8')
    print(f'{len(cases)} independent reactor references -> {destination}')


if __name__ == '__main__':
    main()
