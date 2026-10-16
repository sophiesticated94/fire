"""Recompute derived profiling from native archives without loading 3D fields."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import ROOT
from backend.diagnostics import profile_steps
from backend.progressive import atomic_json


def report(root,output):
    state=json.loads((root/'campaign.json').read_text(encoding='utf-8'));profiles={};directory=root/'profiling-v2';directory.mkdir(exist_ok=True)
    lines=['# Profilowanie kroków — dane natywne','',
           'Liczba kroków pochodzi z końcowego licznika `Time Step`, nie z liczby wierszy CSV. Histogram Δt i statystyki CFL/VN są próbkowane. Koszty podsystemów podzielono przez rzeczywistą liczbę kroków; są estymacją średnią, dla MPI sumą czasów rang.',
           '','| Scena | Profil | Etap / próba | Kroki | Zapisane próbki | Średni fizyczny krok ms | CFL max | DIVG ms/krok | MASS ms/krok | RADI ms/krok |',
           '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in state['runs']:
        p=profile_steps(r['folder']);profiles[r['key']]=p
        atomic_json(directory/(r['key']+'.json'),dict(sourceSha256=r['archive']['sha256'],profile=p))
        costs=p['subsystemsPerStepEstimated'];c=r['config']
        lines.append(f"| {c['scene']} {c['duration']:g}s | {r['profile']['mode']} | {r['phase']} / {r['iteration']} | {p['steps']} | {p['recordedSteps']} | {p['meanPhysicalStepSeconds']*1000:.4f} | {p['cfl'].get('max',0):.3g} | "+' | '.join(f'{costs.get(k,0)*1000:.3f}' for k in ('DIVG','MASS','RADI'))+' |')
    lines+=['','Rozgrzewki mają numer 0 i nie wchodzą do median wydajności. Oryginalne archiwa są niezmienione. Pole `stepProfile` bez wersji `step-profile-2` w starszym dzienniku lub archiwum ma błędny mianownik; zastępują je skorygowane pliki `profiling-v2/*.json` oparte na tych samych danych natywnych.',
            '','Pełny histogram wszystkich kroków wymaga osobnej próby `DIAGNOSTICS_INTERVAL=1`. Dodatkowa diagnostyka ma koszt komunikacji/wyjścia i nie stanowi porównywalnego pomiaru produkcyjnego.',
            '','Źródło: [FDS 6.11.1 — diagnostyka i Time Step Data](https://github.com/firemodels/fds/blob/ff928dbf68a2623ced3a007be75391c6dc6c9f90/Manuals/FDS_User_Guide/FDS_User_Guide.tex).']
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return profiles


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT/'artifacts/campaign-v3');p.add_argument('--output',type=Path,default=ROOT/'docs/steps-v3.md');p.add_argument('--repair-state',action='store_true');a=p.parse_args()
    if a.repair_state:
        from scripts.campaign_v3 import Campaign
        c=Campaign(a.root)
        try:
            profiles=report(c.root,a.output)
            for r in c.state['runs']:r['stepProfile']=profiles[r['key']]
            c.save()
        finally:c.close()
    else:report(a.root,a.output)
