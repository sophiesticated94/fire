"""Compute local samples or mesh studies, preserving all native FDS outputs."""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import Engine
from backend.models import Experiment

parser = argparse.ArgumentParser()
parser.add_argument('--scene',choices=['burner','candle','wood'],default='burner')
parser.add_argument('--duration',type=float,default=6)
parser.add_argument('--quality',choices=['preview','fine'],default='preview')
parser.add_argument('--fuel',type=float)
parser.add_argument('--moisture',type=float,default=12)
parser.add_argument('--wind',type=float,default=0)
parser.add_argument('--oxygen',type=float,default=20.9)
parser.add_argument('--ignition',type=float,default=35)
parser.add_argument('--primary-air',type=float,default=.3)
parser.add_argument('--wait',action='store_true',help='Wait for another local IGNIS process to release the solver')
args = parser.parse_args()
c = Experiment(scene=args.scene,duration=args.duration,quality=args.quality,fuel=args.fuel if args.fuel is not None else (1.2 if args.scene=='candle' else 12),moisture=args.moisture,wind=args.wind,oxygen=args.oxygen,ignition=args.ignition,primary_air=args.primary_air)
e = Engine()
while True:
    try:
        job=e.create(c)
        break
    except RuntimeError:
        if not args.wait: raise
        time.sleep(5)
print(json.dumps(job),flush=True)
while e.active:
    time.sleep(3)
    print(json.dumps(e.status(job['id'])),flush=True)
status = e.status(job['id'])
print(json.dumps(status),flush=True)
sys.exit(0 if status['status']=='completed' else 1)
