"""Publish existing campaign comparisons; never recompute or qualify a run."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from backend.policy import validation_policy
from backend.profiles import fingerprint


def comparison_path(root, reference, candidate, policy_hash):
    code = [fingerprint(ROOT / 'backend' / name) for name in ('validation_v3.py', 'validation.py')]
    key = hashlib.sha256(json.dumps([
        reference['archive']['sha256'], candidate['archive']['sha256'], policy_hash, code
    ]).encode()).hexdigest()
    return root / 'comparisons' / f'{key}.json'


def report(root, output):
    root = Path(root)
    state = json.loads((root / 'campaign.json').read_text(encoding='utf-8'))
    policy = validation_policy()
    lines = ['# Zgodność numeryczna bieżącej kampanii', '',
             f"Polityka: `{policy['data']['status']}`. Raport odczytuje wyłącznie istniejące porównania dla aktualnego kodu i polityki; brak obliczenia jest jawny. Nie zatwierdza profili.", '',
             'RMS czasowo-przestrzenny zachowuje różnice chwilowe. Wszystkie błędy pól są znormalizowane zgodnie z raportem walidacji; tlen jest bezwzględnym RMS w mol/mol. Zmienność trajektorii OpenMP jest referencją interpretacyjną, nie automatycznym usprawiedliwieniem odchyleń MPI.', '']
    groups = {}
    for r in state['runs']:
        if r['iteration'] == 0:
            continue
        key = json.dumps(r['config'], sort_keys=True)
        groups.setdefault(key, []).append(r)
    compared = missing = 0
    evidence = []
    for records in groups.values():
        c = records[0]['config']
        lines += [f"## {c['scene']} — {c['duration']:g} s", '']
        refs = [r for r in records if r['phase'] == 'reference' and r['iteration'] > 0]
        pairs = [('OpenMP / OpenMP', a, b) for i, a in enumerate(refs) for b in refs[i + 1:]]
        pairs += [(f"{r['profile']['mode']} / {r['phase']} {r['iteration']}", a, r)
                  for r in records if r['phase'] != 'reference' for a in refs]
        existing = []
        for label, a, b in pairs:
            p = comparison_path(root, a, b, policy['hash'])
            if p.exists():
                result = json.loads(p.read_text(encoding='utf-8'))
                existing.append((label, a, b, result))
                evidence.append(dict(reference=a.get('key',a['archive']['sha256']),candidate=b.get('key',b['archive']['sha256']),metrics=result))
                compared += 1
            else:
                missing += 1
        lines += ['| Kandydat | Referencja | Stare bramki | Energia, błąd wzgl. | Zapłon, różnica s |',
                  '|---|---:|---|---:|---:|']
        for label, a, b, result in existing:
            legacy = result['legacy']
            ignition = legacy.get('ignitionErrorSeconds')
            lines.append(f"| {label} | {a['iteration']} | {'PASS' if legacy['passed'] else 'FAIL'} | {legacy['energyError']:.6g} | {ignition if ignition is not None else 'brak zgodnego zapłonu'} |")
        lines += ['', 'Maksimum błędu po dostępnych parach w danej grupie; wartości poszczególnych par pozostają w `comparisons/*.json`.', '',
                  '| Grupa | Okno | Kanał | Największy błąd |', '|---|---|---|---:|']
        maxima = {}
        diagnostic = {}
        for label, a, b, result in existing:
            group = 'OpenMP / OpenMP' if label == 'OpenMP / OpenMP' else b['profile']['mode']
            for window in ('full', 'late', 'interfacesFull', 'interfacesLate', 'variability'):
                for metric in result['temporal'][window]:
                    key = (group, window, metric['channel'])
                    maxima[key] = max(maxima.get(key, 0), metric['error'])
            for name, metric in result['devices'].items():
                # Different quantities and units are never collapsed together.
                key = (group, name, metric.get('unit') or 'nieznana')
                diagnostic[key] = max(diagnostic.get(key, 0), metric['rms'])
        for (group, window, channel), value in sorted(maxima.items()):
            lines.append(f'| {group} | {window} | {channel} | {value:.6g} |')
        lines += ['', '### Natywne sondy i strumienie', '',
                  'Największy bezwzględny RMS po dostępnych parach; zachowujemy położenie sondy i natywne jednostki.', '',
                  '| Grupa | Urządzenie | Jednostka | RMS |', '|---|---|---|---:|']
        for (group, name, unit), value in sorted(diagnostic.items()):
            lines.append(f'| {group} | {name} | {unit} | {value:.6g} |')
    lines += ['', f'Zapisane porównania: {compared}; brakujące pary: {missing}. Brakujące porównania nie oznaczają zgodności.', '',
              '[Dane maszynowe i hashe dowodów](benchmark-v3-data.json). Archiwa natywne pozostają na dysku komputera; JSON nie zastępuje surowych pól.', '',
              'Kryteria regresji demonstracji edukacyjnej; bez deklaracji walidacji inżynierskiej.']
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    keys = ('key','config','profile','signature','solverSeconds','conversionSeconds','totalSeconds','steps','secondsPerStep',
            'firstFrameSeconds','telemetry','cpu','nativeExact','stepProfile','archiveSeconds','campaignSeconds','phase','iteration','screenScore','screenPolicyHash')
    runs = [dict(**{k:r[k] for k in keys if k in r},archive={k:r['archive'][k] for k in ('sha256','bytes') if k in r['archive']}) for r in state['runs']]
    data = dict(version='measured-evidence-3',context=state.get('context'),budget=state.get('budget'),usedWallSeconds=state.get('usedSeconds'),
                storedBytes=state.get('storedBytes'),status=state.get('status'),stopReason=state.get('stopReason'),policy=policy['data'],policyHash=policy['hash'],
                verification=state.get('verification'),runs=runs,comparisons=evidence,missingPairs=missing)
    output.with_name('benchmark-v3-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return dict(compared=compared, missing=missing)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=ROOT / 'artifacts/campaign-v3')
    p.add_argument('--output', type=Path, default=ROOT / 'docs/numerical-v3.md')
    args = p.parse_args()
    print(report(args.root, args.output))
