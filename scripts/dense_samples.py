"""Compute and package examples with an explicit 10 Hz volume output rate."""
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.models import Experiment
from backend.engine import Engine, ROOT

for scene,fuel in [('burner',12),('candle',1.2),('wood',0)]:
    config=Experiment(scene=scene,duration=2,fuel=fuel,ignition=55)
    engine=Engine()
    while True:
        try: job=engine.create(config); break
        except RuntimeError: time.sleep(5)
    print(scene,job['id'],flush=True)
    while engine.active: time.sleep(5)
    status=engine.status(job['id'])
    if status['status']!='completed': raise RuntimeError(status)
    metadata=json.loads((engine.folder(job['id'])/'result.json').read_text(encoding='utf-8'))
    if len(metadata['times'])<20: raise RuntimeError('Expected at least 20 native volume frames')
    subprocess.run([sys.executable,str(ROOT/'scripts/package_samples.py'),job['id']],check=True)
    print(scene,'ready',metadata['elapsed'],flush=True)
