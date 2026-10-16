"""Render the native evidence as a tracked, portable Markdown report."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import ROOT

def render(source,destination):
    report=json.loads(Path(source).read_text(encoding='utf-8'))
    lines=['# Natywne pomiary profilu execution-2','',
           'Pomiary lokalne Windows x64, Intel Core i5-12500H, FDS 6.11.1. Zachowano model fizyczny i siatkę. ',
           'Każdy wariant ma jedną rozgrzewkę oraz trzy pomiary. Czas całkowity obejmuje pracę solvera i przygotowanie danych; ',
           'czas konwersji przyrostowej częściowo nakłada się na solver i nie należy go ponownie dodawać. Niezależna kontrola fdsreader odbywa się poza pomiarem.',
           '',f"Źródło: `{Path(source).name}`. Zapisano {len(report['runs'])} ukończonych prób. Docelowa macierz preview zawiera 60 prób.",
           '', 'Pełne dane pomiarowe, sondy, maski affinity i profilowanie FDS: [benchmark-v2-data.json](benchmark-v2-data.json).',
           '', '| Scena / czas | Wariant | Mediana całości s | Min–max s | Odch. s | Przyspieszenie | Bramka pól i energii |',
           '|---|---|---:|---:|---:|---:|---|']
    for s in report['summaries']:
        c=s['config'];lines.append(f"| {c['scene']} / {c['duration']:g} s / {c['quality']} | {s['mode']} | {s['median']:.2f} | {s['min']:.2f}–{s['max']:.2f} | {s['stdev']:.2f} | {s['speedup']:.3f}× | {'PASS' if s['passed'] else 'FAIL'} |")
    lines+=['','Automatyczna promocja wymaga PASS dla każdego pomiaru i oszczędności mediany co najmniej 5%. Brak wyniku w tabeli oznacza brak dowodu, a nie pozytywną walidację.',
            '','## Szczegóły prób','', '| Scena / czas | Wariant / próba (0 = rozgrzewka) | Solver s | Konwersja s | Kroki | Pierwsza klatka s | Szczyt pamięci commit MiB | I/O odczyt/zapis MiB |',
            '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in report['runs']:
        c=r['config'];t=r['telemetry'];first=r['firstFrameSeconds']
        lines.append(f"| {c['scene']} / {c['duration']:g} | {r['profile']['mode']} / {r['iteration']} | {r['solverSeconds']:.2f} | {r['conversionSeconds']:.2f} | {r['steps']} | {first:.2f} | {t.get('peakMemoryBytes',0)/2**20:.1f} | {t.get('readBytes',0)/2**20:.1f}/{t.get('writeBytes',0)/2**20:.1f} |" if first is not None else f"| {c['scene']} / {c['duration']:g} | {r['profile']['mode']} / {r['iteration']} | {r['solverSeconds']:.2f} | {r['conversionSeconds']:.2f} | {r['steps']} | po zakończeniu | {t.get('peakMemoryBytes',0)/2**20:.1f} | — |")
    lines+=['','## Zgodność numeryczna','']
    for s in report['summaries']:
        lines.append(f"### {s['config']['scene']} {s['config']['duration']:g} s — {s['mode']}")
        lines+=['','| Pole | Maks. błąd RMS pola | Maks. błąd przy granicach siatek | Limit |', '|---|---:|---:|---:|']
        for i,field in enumerate(s['comparisons'][0]['fields']):
            maximum=max(comp['fields'][i]['error'] for comp in s['comparisons'])
            interfaces=[comp['interfaces'][i]['error'] for comp in s['comparisons'] if comp['interfaces']]
            boundary=f'{max(interfaces):.6g}' if interfaces else '—'
            lines.append(f"| {field['channel']} | {maximum:.6g} | {boundary} | {field['limit']:g} |")
        lines.append('')
        lines.append(f"Największa względna różnica energii: {max(c['energyError'] for c in s['comparisons']):.6g}; limit 0,05.")
        if s['config']['scene']=='wood':
            ignition=[comp['ignitionErrorSeconds'] for comp in s['comparisons']]
            value=f'{max(ignition):.6g} s' if all(v is not None for v in ignition) else 'brak zapłonu w jednym z porównywanych przebiegów (FAIL)'
            lines.append(f'Największa różnica czasu zapłonu: {value}; limit 0,2 s. Brak zapłonu w obu przebiegach oznacza różnicę 0 s.')
        if s['comparisons'][0]['interfaces']:
            lines.append('Bramka obejmuje również warstwy komórek przy granicach podsiatek; szczegółowe błędy i sondy są w JSON.')
        lines.append('')
    lines+=['## Affinity i ograniczenia','',
            'Maski procesów MPI/FDS zmierzone w trakcie pracy są zapisane jako `observedProcessAffinity` w JSON. Nie utożsamiamy ich automatycznie z rdzeniami P. ',
            'Telemetria pamięci commit i I/O obejmuje procesy należące do Job Object solvera/MPI; nie obejmuje procesu Python wykonującego konwersję. ',
            'Raport zachowuje czasy podsystemów FDS w polu `cpu`, identyfikatory binariów i konfiguracji oraz dokładną zgodność eksportu siedmiu pól (`nativeExact`). ',
            'Porównania nie stanowią walidacji inżynierskiej. Definicje progów: [execution-v2.md](execution-v2.md).']
    Path(destination).write_text('\n'.join(line.rstrip() for line in lines)+'\n',encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',default=str(ROOT/'artifacts/benchmark-v2.json'));parser.add_argument('--output',default=str(ROOT/'docs/benchmark-v2.md'))
    args=parser.parse_args();render(args.input,args.output)
