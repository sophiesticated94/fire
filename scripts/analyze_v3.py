"""Reassess existing runs without launching FDS or promoting any profile."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import ROOT
from backend.progressive import atomic_json
from backend.validation_v3 import compare_v3
from backend.policy import VALIDATION_VERSION

def analyze(source,output):
    data=json.loads(Path(source).read_text(encoding='utf-8'));groups=defaultdict(list)
    for run in data['runs']:
        if run['iteration']>0 and run.get('nativeExact'):groups[json.dumps(run['config'],sort_keys=True)].append(run)
    report=dict(version=VALIDATION_VERSION,status='pending-review',source=str(source),groups=[])
    if output.exists():report=json.loads(output.read_text(encoding='utf-8'))
    for key,runs in groups.items():
        config=json.loads(key);reference=[r for r in runs if r['profile']['mode']=='openmp']
        if len(reference)!=3:raise ValueError('Exactly three OpenMP reference repetitions required')
        group=next((g for g in report['groups'] if g['config']==config),None)
        if group is None:group=dict(config=config,comparisons=[]);report['groups'].append(group)
        pairs=[(reference[i],reference[j],'openmp-repeatability') for i in range(3) for j in range(i+1,3)]
        pairs += [(a,b,b['profile']['mode']) for a in reference for b in runs if b['profile']['mode']!='openmp']
        for a,b,kind in pairs:
            ident=[a['folder'],b['folder']]
            if any(c['pair']==ident for c in group['comparisons']):continue
            print(f"ANALYZE {config['scene']} {config['duration']:g}s {kind} {a['iteration']}:{b['iteration']}",flush=True)
            comparison=compare_v3(a['folder'],b['folder'])
            group['comparisons'].append(dict(pair=ident,kind=kind,result=comparison))
            atomic_json(output,report)
    return report

def render(report,path):
    lines=['# Walidacja v3 — ponowna ocena zapisanych przebiegów','',
           'Status: **oczekuje na osobny przegląd progów**. Nowe miary nie promują profili. Dotychczasowe limity pól średnich, energii i zapłonu pozostają bez zmian.',
           '','Porównania OpenMP obejmują trzy pary powtórzeń; każdy kandydat jest porównany z każdą z trzech referencji. Rozrzut jest opisowy, bez deklarowania przedziałów ufności.',
           '','W tabeli: maksymalny znormalizowany błąd chwilowy w drugiej połowie nagrania. Tlen: bezwzględny RMS mol/mol. Pełne okno, granice siatek, zmienność, sondy i HRR są w danych JSON.',
           '','| Scena / czas | Rodzaj | ΔT | HRRPUV | Sadza | O₂ | U | V | W | Stare bramki |','|---|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for group in report['groups']:
        for kind in sorted({c['kind'] for c in group['comparisons']}):
            values=[c['result'] for c in group['comparisons'] if c['kind']==kind]
            maxima=[max(c['temporal']['late'][i]['error'] for c in values) for i in range(7)]
            c=group['config'];passed=all(v['legacy']['passed'] for v in values)
            lines.append(f"| {c['scene']} / {c['duration']:g}s | {kind} | "+' | '.join(f'{x:.5g}' for x in maxima)+f" | {'PASS' if passed else 'FAIL'} |")
    lines+=['','## Interpretacja i decyzja','',
            'Różnica chwilowych trajektorii sama nie rozstrzyga o błędzie modelu. Zestawienie z rozrzutem OpenMP, średnimi, zmiennością i strumieniami służy osobnemu przeglądowi.',
            'Historyczne przebiegi nie zawierają dodatkowych strumieni diagnostycznych; ich brak jest jawnie raportowany i blokuje promocję v3.',
            'Plik polityki `config/validation-v3.json` pozostaje `pending-review`. Także wcześniej zaakceptowana świeca wymaga ponownej kwalifikacji.']
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=ROOT/'artifacts/benchmark-v2.json');p.add_argument('--output',type=Path,default=ROOT/'artifacts/validation-v3.json');p.add_argument('--report',type=Path,default=ROOT/'docs/validation-v3.md');a=p.parse_args()
    report=analyze(a.input,a.output);render(report,a.report)
