"""Lossless native archives; exported frame copies can be reconstructed."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time
from types import SimpleNamespace
import zipfile

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def archive_run(folder,destination,cleanup_root=None):
    folder=Path(folder).resolve();destination=Path(destination).resolve()
    if cleanup_root is not None:
        root=Path(cleanup_root).resolve()
        if folder==root or not folder.is_relative_to(root):raise ValueError('Archive cleanup outside campaign workspace')
    if destination.is_relative_to(folder):raise ValueError('Archive must be outside source attempt')
    files=[p for p in folder.rglob('*') if p.is_file() and 'frames' not in p.relative_to(folder).parts and p.suffix not in ('.pickle','.pkl')]
    if any(p.is_symlink() or p.is_junction() for p in folder.rglob('*')):raise ValueError('Linked archive input')
    meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    directory=folder/meta.get('frameDirectory','frames')
    frame_hashes={p.name:sha256(p) for p in directory.glob('*.bin')}
    manifest=dict(version=1,files={p.relative_to(folder).as_posix():sha256(p) for p in files},frames=frame_hashes)
    destination.parent.mkdir(parents=True,exist_ok=True);pending=destination.with_suffix('.pending')
    with zipfile.ZipFile(pending,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in files:z.write(path,path.relative_to(folder).as_posix())
        z.writestr('archive-manifest.json',json.dumps(manifest))
    with zipfile.ZipFile(pending) as z:
        if z.testzip() is not None:raise ValueError('Corrupted archive')
        for name,digest in manifest['files'].items():
            with z.open(name) as f:
                if hashlib.file_digest(f,'sha256').hexdigest()!=digest:raise ValueError('Archive checksum mismatch')
    pending.replace(destination)
    receipt=dict(path=str(destination),sha256=sha256(destination),bytes=destination.stat().st_size,frames=len(frame_hashes))
    if cleanup_root is not None:remove_temporary_tree(folder,Path(cleanup_root).resolve())
    return receipt

def remove_temporary_tree(path,root):
    path=Path(path).resolve();root=Path(root).resolve()
    if path==root or not path.is_relative_to(root):raise ValueError('Cleanup escaped its explicit root')
    for retry in range(20):
        try:shutil.rmtree(path);return
        except PermissionError:
            if retry==19:raise
            time.sleep(.1)

@contextmanager
def open_run(path,scratch_root=None,*,fields_only=False):
    path=Path(path)
    if path.is_dir():yield path;return
    if path.suffix!='.zip':raise ValueError('Expected run directory or native zip archive')
    temp_root=Path(scratch_root or tempfile.gettempdir()).resolve();temp_root.mkdir(parents=True,exist_ok=True)
    folder=Path(tempfile.mkdtemp(prefix='ignis-analysis-',dir=temp_root)).resolve()
    try:
        with zipfile.ZipFile(path) as z:
            if sum(i.file_size for i in z.infolist())>4*1024**3:raise ValueError('Oversized native archive')
            for item in z.infolist():
                target=(folder/item.filename).resolve()
                if not target.is_relative_to(folder) or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe archive entry')
            manifest=json.loads(z.read('archive-manifest.json'))
            z.extractall(folder)
        for name,digest in manifest['files'].items():
            target=(folder/name).resolve()
            if not target.is_relative_to(folder) or sha256(target)!=digest:raise ValueError('Native archive checksum mismatch')
        from .models import Experiment
        from .progressive import ProgressiveConverter,atomic_json
        meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        p=meta.get('profile',{});profile=SimpleNamespace(ranks=p.get('ranks',1),layout=p.get('layout','single' if p.get('ranks',1)==1 else f"z{p['ranks']}"),identity=lambda:p,diagnostics=meta.get('diagnosticsRecipe','none'))
        pipe=ProgressiveConverter(folder,Experiment(**meta['config']),profile,meta['id'],meta.get('attempt','archive'))
        pipe.drain(final=True)
        for name,digest in manifest['frames'].items():
            if sha256(folder/'preview/frames'/name)!=digest:raise ValueError('Reconstructed frame differs from verified export')
        meta['frameDirectory']='preview/frames';atomic_json(folder/'result.json',meta)
        if fields_only:
            # Comparisons need only the verified exports and metadata. Remove
            # extracted native copies, never the immutable source archive.
            for child in folder.iterdir():
                if child.name in ('preview','result.json'):continue
                if child.is_dir():remove_temporary_tree(child,folder)
                else:
                    for retry in range(20):
                        try:child.unlink();break
                        except PermissionError:
                            if retry==19:raise
                            time.sleep(.1)
        yield folder
    finally:remove_temporary_tree(folder,temp_root)
