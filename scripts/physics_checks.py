"""Native FDS edge cases; writes measured results, never synthetic fixtures."""
import json
from pathlib import Path
import sys
import time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.models import Experiment
from backend.engine import Engine, ROOT
from backend.validation import frame_path

cases=[
    ('no-fuel',Experiment(duration=1,fuel=0)),
    ('low-oxygen',Experiment(duration=1,oxygen=12)),
    ('crosswind',Experiment(duration=1,wind=.2)),
    ('no-heating',Experiment(scene='wood',duration=1,moisture=0,ignition=0)),
    ('dry-wood',Experiment(scene='wood',duration=2,moisture=0,ignition=35)),
]
results=[]
for label,config in cases:
    engine=Engine()
    while True:
        try: job=engine.create(config); break
        except RuntimeError: time.sleep(5)
    print(label,job['id'],flush=True)
    while engine.active: time.sleep(3)
    status=engine.status(job['id'])
    if status['status']!='completed': raise RuntimeError(status)
    folder=engine.folder(job['id'])
    meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    frame=np.fromfile(frame_path(folder,meta,len(meta['times'])-1),dtype='<f4').reshape(-1,7)
    hrr=meta['series']['HRR']
    row={'case':label,'id':job['id'],'peakHRR_W':max(hrr)*1000,'finalPeakTemperature_C':float(frame[:,0].max()),'meanU_m_s':float(frame[:,4].mean()),'elapsed_s':meta['elapsed']}
    if label in ('no-fuel','no-heating'):
        assert max(np.abs(hrr))<1e-6
        assert abs(row['finalPeakTemperature_C']-config.ambient)<2
    if label=='crosswind': assert row['meanU_m_s']>0.02
    assert np.isfinite(frame).all()
    results.append(row)
    target=ROOT/'docs/physics-checks.json'
    target.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(row),flush=True)
print('Native checks passed',flush=True)
