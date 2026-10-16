"""Reproducible two-resolution study. Short runs test initial transients only."""
import json
from pathlib import Path
import sys
import time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.models import Experiment
from backend.engine import Engine, ROOT

def compute(config):
    engine=Engine()
    job=engine.create(config)
    print('study',config.scene,config.quality,job['id'],flush=True)
    while engine.active:
        time.sleep(5)
    final=engine.status(job['id'])
    if final['status']!='completed': raise RuntimeError(str(final))
    return job['id']

def meta(ident):
    path=Engine().folder(ident)/'result.json'
    return json.loads(path.read_text(encoding='utf-8'))

def summarize(m,t):
    times=np.asarray(m['series']['Time'])
    q=np.asarray(m['series']['HRR'])
    ts=np.linspace(t*.5,t,101)
    mean=float(np.trapezoid(np.interp(ts,times,q),ts)/(ts[-1]-ts[0]))*1000
    device=m['devices']
    probe=float(np.interp(t,device['Time'],device['probe_T']))
    peak=float(np.interp(t,m['times'],[x['temperature'] for x in m['extrema']]))
    return mean,probe,peak

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--wood':
        for quality in ('preview','fine'):
            compute(Experiment(scene='wood',duration=2,quality=quality,moisture=12,ignition=35))
    elif len(sys.argv)==7:
        pairs=[(sys.argv[i],sys.argv[i+1]) for i in (1,3,5)]
        lines=['# Porównanie dwóch siatek','','To badanie wrażliwości początkowego przebiegu, nie dowód zbieżności ani walidacja eksperymentalna. Moc to średnia w drugiej połowie badanego okna. Temperatura sondy pochodzi z urządzenia FDS w tym samym fizycznym punkcie. Tmax jest interpolacją maksimów zapisanych klatek.','','| Scena / czas | Siatka | Moc W | Sonda °C | Tmax °C | Czas obliczeń s |','|---|---|---:|---:|---:|---:|']
        for a,b in pairs:
            coarse,fine=meta(a),meta(b)
            t=2 if coarse['config']['scene']=='wood' else .8
            av,bv=summarize(coarse,t),summarize(fine,t)
            for m,v in ((coarse,av),(fine,bv)):
                lines.append(f"| {m['config']['scene']} / {t} s | {' × '.join(map(str,m['dimensions']))} | {v[0]:.2f} | {v[1]:.2f} | {v[2]:.2f} | {m['elapsed']:.1f} |")
            dif=[abs(y-x)/max(abs(x),1e-9)*100 for x,y in zip(av,bv)]
            lines.append(f"| Zmiana względem podglądu | | {dif[0]:.1f}% | {dif[1]:.1f}% | {dif[2]:.1f}% | — |")
        lines+=['','Duże różnice temperatur lub mocy oznaczają, że ta rozdzielczość nie uzasadnia ilościowych przewidywań dla rzeczywistego płomienia. Nawet mała różnica na dwóch siatkach nie zastępuje testu trzeciej siatki, wielkości domeny, bilansów i porównania z pomiarami. Badanie drewna jest krótkim przebiegiem nagrzewania/zapłonu; nie ocenia pełnego wypalenia ani utleniania żaru. Czasy pracy zawierają wpływ równoległych prac na komputerze i nie są benchmarkiem wyłącznego dostępu do CPU.','', 'Identyfikatory danych: '+', '.join(sys.argv[1:])]
        (ROOT/'docs/mesh-study.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        print('\n'.join(lines))
    else:
        print('Use --wood to compute wood runs, or six IDs: burner coarse fine, candle coarse fine, wood coarse fine.')
