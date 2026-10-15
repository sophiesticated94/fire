"""Wait for the requested native examples, then package their actual outputs."""
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.models import Experiment
root=Path(__file__).resolve().parent.parent
ids=['77861df34e4e31153afd','159b5e1a1a90477d1399',Experiment(scene='wood',duration=3,ignition=55).key()]
print('Waiting for',ids,flush=True)
while True:
    try:
        for ident in ids: json.loads((root/'runs'/ident/'result.json').read_text(encoding='utf-8'))
        break
    except (FileNotFoundError,ValueError): time.sleep(5)
subprocess.run([sys.executable,str(root/'scripts/refresh_metadata.py')],check=True)
subprocess.run([sys.executable,str(root/'scripts/package_samples.py'),*ids],check=True)
print('Three real CFD samples packaged.',flush=True)
