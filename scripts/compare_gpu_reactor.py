"""Compare the actually reached GPU time, never substitute a shorter horizon."""
import json
from pathlib import Path

import cantera as ct
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'artifacts/gpu-v14'
    measured = json.loads((folder / 'reactor-gate.json').read_text())
    config = measured['fixture']
    gas = ct.Solution(str(ROOT / 'src/gpu/chemistry/data/gri30.yaml'))
    gas.set_equivalence_ratio(config['phi'], 'CH4', 'O2:1,N2:3.76')
    gas.TP = config['T'], ct.one_atm
    h0 = gas.enthalpy_mass
    elements0 = np.array([gas.elemental_mass_fraction(e) for e in gas.element_names])
    reactor = ct.IdealGasConstPressureReactor(gas, clone=True)
    network = ct.ReactorNet([reactor])
    network.rtol, network.atol = 1e-10, 1e-20
    reached = measured['status'][0]
    network.advance(reached)
    reference = np.r_[reactor.T, reactor.phase.Y]
    actual = np.array(measured['states'])
    radical_errors = {}
    for name in ['H', 'O', 'OH', 'HO2', 'CH3']:
        index = gas.species_index(name)+1
        radical_errors[name] = float(abs(actual[index]-reference[index])/(1e-12+.05*abs(reference[index])))
    gas.TPY = actual[0], ct.one_atm, actual[1:]
    elements = np.array([gas.elemental_mass_fraction(e) for e in gas.element_names])
    metrics = dict(
        temperatureWeightedError=float(abs(actual[0]-reference[0])/max(1, .005*abs(reference[0]-config['T']))),
        speciesWeightedError=float(max(abs(actual[1:]-reference[1:])/np.maximum(1e-4, .02*np.abs(reference[1:])))),
        radicalWeightedError=radical_errors,
        enthalpyFraction=float(abs(gas.enthalpy_mass-h0)/max(1, abs(h0))),
        elementalRelativeError=float(max(abs(elements-elements0)/np.maximum(1e-30, abs(elements0)))),
        sumYError=float(abs(actual[1:].sum()-1)),
    )
    short_pass = (metrics['temperatureWeightedError'] <= 1 and metrics['speciesWeightedError'] <= 1
                  and max(radical_errors.values()) <= 1 and metrics['enthalpyFraction'] <= 1e-5
                  and metrics['elementalRelativeError'] <= 1e-5 and metrics['sumYError'] <= 1e-5)
    report = dict(time=reached, requiredHorizon=config['horizon'], metrics=metrics,
                  shortTrajectoryPass=short_pass, fullHorizonReached=measured['stopReason']=='completed',
                  # Additional ignition, OH-peak, all-case and scale gates remain mandatory.
                  chemistryAccepted=False, reference=reference.tolist(), actual=actual.tolist())
    (folder / 'reactor-comparison.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ['reference', 'actual']}, indent=2))


if __name__ == '__main__':
    main()
