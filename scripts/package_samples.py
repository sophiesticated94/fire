"""Package real computed examples with precompressed lossless volume frames."""
import gzip
import json
from pathlib import Path
import shutil
import sys
root=Path(__file__).resolve().parent.parent
for ident in sys.argv[1:]:
    src=root/'runs'/ident
    if not (src/'result.json').exists(): raise RuntimeError(f'Incomplete experiment: {ident}')
    meta=json.loads((src/'result.json').read_text(encoding='utf-8'))
    # Preserve supplementary recordings, with one primary example per scene.
    for older in (root/'samples').glob('*/result.json'):
        old=json.loads(older.read_text(encoding='utf-8'))
        if old['config']['scene']==meta['config']['scene']:
            old['featured']=False
            temporary=older.with_suffix('.pending')
            temporary.write_text(json.dumps(old,ensure_ascii=False),encoding='utf-8')
            temporary.replace(older)
    dest=root/'samples'/ident
    dest.mkdir(parents=True,exist_ok=True)
    for name in ('config.json','ignis.fds','ignis_hrr.csv','ignis_devc.csv','solver.log','reference-check.json'):
        if (src/name).exists(): shutil.copy2(src/name,dest/name)
    meta['featured']=True
    (dest/'frames').mkdir(exist_ok=True)
    for frame in sorted((src/'frames').glob('*.bin')):
        compressed=dest/'frames'/(frame.name+'.gz')
        if not compressed.exists():
            temporary=compressed.with_suffix('.pending')
            with gzip.open(temporary,'wb',compresslevel=6) as f: f.write(frame.read_bytes())
            temporary.replace(compressed)
    temporary=dest/'result.pending'
    temporary.write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')
    temporary.replace(dest/'result.json')
    size=sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())
    print(ident,meta['config']['scene'],len(meta['times']),'frames',round(size/1024**2,2),'MiB',flush=True)
