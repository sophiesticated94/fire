import json
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .engine import Engine, ROOT, solver_path
from .models import Experiment

engine = Engine()

@asynccontextmanager
async def lifespan(app):
    yield
    engine.shutdown()

app = FastAPI(title='IGNIS local CFD API',version='1.1.0',lifespan=lifespan)


@app.get('/api/health')
def health():
    return {'solverAvailable':solver_path() is not None,'solver':'FDS 6.11.1','active':engine.active}


@app.get('/api/experiments')
def history():
    return engine.history()


@app.post('/api/experiments')
def create(config: Experiment):
    try: return engine.create(config)
    except FileNotFoundError as exc: raise HTTPException(503,str(exc))
    except RuntimeError as exc: raise HTTPException(409,str(exc))
    except ValueError as exc: raise HTTPException(422,str(exc))


@app.get('/api/experiments/{ident}')
def status(ident: str):
    try: return engine.status(ident)
    except KeyError: raise HTTPException(404,'Nie znaleziono eksperymentu')


@app.post('/api/experiments/{ident}/cancel')
def cancel(ident: str):
    try: return engine.cancel(ident)
    except KeyError: raise HTTPException(404,'Nie znaleziono eksperymentu')


def result_folder(ident):
    try: folder = engine.folder(ident)
    except KeyError: raise HTTPException(404,'Nie znaleziono eksperymentu')
    if not (folder/'result.json').exists(): raise HTTPException(409,'Wynik nie jest gotowy')
    return folder


@app.get('/api/experiments/{ident}/result')
def result(ident: str):
    return FileResponse(result_folder(ident)/'result.json',media_type='application/json')


@app.get('/api/experiments/{ident}/frames/{frame}')
def frame(ident: str, frame: int):
    if frame < 0: raise HTTPException(404,'Brak klatki')
    folder = result_folder(ident)
    meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    directory='preview/frames' if meta.get('frameDirectory')=='preview/frames' else 'frames'
    p = folder/directory/f'{frame:05d}.bin'
    headers={'Cache-Control':'private, max-age=31536000, immutable'}
    if not p.exists():
        p=p.with_suffix('.bin.gz')
        if not p.exists(): raise HTTPException(404,'Brak klatki')
        headers['Content-Encoding']='gzip'
    return FileResponse(p,media_type='application/octet-stream',headers=headers)


@app.get('/api/experiments/{ident}/preview/manifest')
def preview_manifest(ident: str):
    try: folder=engine.folder(ident)
    except KeyError: raise HTTPException(404,'Nie znaleziono eksperymentu')
    path=folder/'preview/manifest.json'
    if not path.exists(): raise HTTPException(409,'Pierwsze klatki nie są jeszcze gotowe')
    from fastapi.responses import JSONResponse
    return JSONResponse(json.loads(path.read_text(encoding='utf-8')),headers={'Cache-Control':'no-store'})


@app.get('/api/experiments/{ident}/preview/frames/{frame}')
def preview_frame(ident: str, frame: int, attempt: str):
    if frame<0: raise HTTPException(404,'Brak klatki')
    try: folder=engine.folder(ident,attempt)
    except KeyError: raise HTTPException(404,'Nie znaleziono próby')
    manifest=folder/'preview/manifest.json'
    if not manifest.exists(): raise HTTPException(409,'Podgląd nie jest gotowy')
    meta=json.loads(manifest.read_text(encoding='utf-8'))
    if frame>=len(meta['times']): raise HTTPException(404,'Klatka nie została opublikowana')
    path=folder/'preview/frames'/f'{frame:05d}.bin'
    if not path.is_file(): raise HTTPException(404,'Brak klatki')
    return FileResponse(path,media_type='application/octet-stream',headers={'Cache-Control':'private, max-age=31536000, immutable'})


@app.get('/api/experiments/{ident}/input')
def input_file(ident: str):
    return FileResponse(result_folder(ident)/'ignis.fds',filename='ignis.fds')


@app.get('/api/experiments/{ident}/log')
def log_file(ident: str):
    try: folder = engine.folder(ident)
    except KeyError: raise HTTPException(404,'Nie znaleziono eksperymentu')
    p = folder/'solver.log'
    if not p.exists(): raise HTTPException(404,'Brak dziennika')
    return FileResponse(p,media_type='text/plain')


if (ROOT/'dist').is_dir():
    app.mount('/',StaticFiles(directory=ROOT/'dist',html=True),name='frontend')
