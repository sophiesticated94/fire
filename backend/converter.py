"""Lossless float32 transport of actual FDS cell-centered volume slices."""
import csv
import json
from pathlib import Path
import numpy as np
import fdsreader
from .models import MODEL_VERSION

CHANNELS = [
    {'name':'temperature','unit':'°C'}, {'name':'hrr','unit':'kW/m³'},
    {'name':'soot','unit':'kg/m³'}, {'name':'oxygen','unit':'mol/mol'},
    {'name':'u','unit':'m/s'}, {'name':'v','unit':'m/s'}, {'name':'w','unit':'m/s'},
]


def csv_table(path: Path):
    if not path.exists():
        return {}
    with path.open() as f:
        rows = list(csv.reader(f))
    if len(rows) < 3:
        return {}
    names = [x.strip().strip('"') for x in rows[1]]
    data = np.array([[float(x) for x in r] for r in rows[2:] if r], dtype=float)
    if not np.isfinite(data).all(): raise ValueError(f'Niefinitywne dane CSV: {path.name}')
    return {name:data[:,i].tolist() for i,name in enumerate(names)}


def convert(folder: Path, config: dict, elapsed: float):
    sim = fdsreader.Simulation(str(folder))
    slices = list(sim.slices)
    def find(q, species=None):
        candidates = [s for s in slices if s.quantity.name.upper() == q]
        if species:
            candidates = [s for s in candidates if species in (s.quantity.long_name+' '+str(s.id)).upper() or species in str(s.quantity).upper()]
        if not candidates:
            raise ValueError(f'Brak pola FDS: {q} {species or ""}. Dostępne: '+str([(s.quantity, s.id) for s in slices]))
        return candidates[0]
    # Unique quantities in this input: SOOT density and OXYGEN volume fraction.
    selected = [find(q) for q in ['TEMPERATURE','HRRPUV','SOOT DENSITY','OXYGEN VOLUME FRACTION','U-VELOCITY','V-VELOCITY','W-VELOCITY']]
    arrays = []
    coords = None
    for s in selected:
        arr, coords = s.to_global(return_coordinates=True)
        arrays.append(np.asarray(arr, dtype='<f4'))
    times = selected[0].times.tolist()
    if not times or any(a.shape != arrays[0].shape for a in arrays):
        raise ValueError('Niezgodne siatki lub czasy pól FDS')
    for s in selected[1:]:
        if not np.allclose(s.times, selected[0].times):
            raise ValueError('Niezgodne czasy zapisów FDS')
    dims = list(arrays[0].shape[1:])
    if len(dims) != 3:
        raise ValueError(f'Oczekiwano pola 3D, otrzymano {dims}')
    frame_dir = folder/'frames'
    frame_dir.mkdir(exist_ok=True)
    extrema = []
    for i in range(len(times)):
        # Browser x-fastest, then y, then z; seven interleaved float32 channels.
        frame = np.stack([a[i] for a in arrays], axis=-1).transpose(2,1,0,3).copy()
        if not np.isfinite(frame).all():
            raise ValueError('Niefinitywne wartości w wyniku solvera')
        frame.tofile(frame_dir/f'{i:05d}.bin')
        extrema.append({'temperature':float(frame[...,0].max()),'hrr':float(frame[...,1].max()),'velocity':float(np.linalg.norm(frame[...,4:7],axis=-1).max())})
    series = csv_table(folder/'ignis_hrr.csv')
    devices = csv_table(folder/'ignis_devc.csv')
    metadata = {
        'id':folder.name,'config':config,'solver':'FDS 6.11.1','model':MODEL_VERSION,
        'dimensions':dims,'coordinates':{axis:coords[axis].tolist() for axis in ('x','y','z')},
        'times':times,'channels':CHANNELS,'extrema':extrema,'elapsed':elapsed,
        'series':series,'devices':devices,'source':'FDS cell-centered 3D slices; float32',
        'solidBounds':[o.bounding_box.as_list() for o in sim.obstructions],
        'rendering':'Rekonstrukcja emisji i absorpcji; kolor nie jest pomiarem temperatury.',
    }
    temporary=folder/'result.pending'
    temporary.write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
    temporary.replace(folder/'result.json')
    return metadata
