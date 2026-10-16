"""Incremental SLCF reader. One pending record per field/mesh, no history reload."""
import json
from pathlib import Path
import struct
import time
import numpy as np
import fdsreader
from .models import geometry, MODEL_VERSION, SOLVER_VERSION
from .profiles import TRANSPORT_VERSION
from .converter import CHANNELS

QUANTITIES=['TEMPERATURE','HRRPUV','SOOT DENSITY','OXYGEN VOLUME FRACTION','U-VELOCITY','V-VELOCITY','W-VELOCITY']
# SMV TRN node coordinates are printed to five decimal places in metres.
# Field records retain their full float32 precision. This is a file-format
# allowance, not a relaxation of any physical comparison gate.
SMV_COORD_ATOL=5.1e-6

class MeshGeometryError(ValueError):
    """Complete mesh metadata contradicts the declared numerical grid."""

def atomic_json(path,data):
    temporary=path.with_suffix(path.suffix+'.pending')
    temporary.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    # Windows readers may briefly hold the old file without FILE_SHARE_DELETE.
    for attempt in range(20):
        try:temporary.replace(path);break
        except PermissionError:
            if attempt==19:raise
            time.sleep(.025)

class SliceStream:
    def __init__(self,path,shape):
        self.path=Path(path); self.shape=tuple(shape); self.offset=146; self.pending=None

    @staticmethod
    def record(stream,size):
        start=stream.tell(); head=stream.read(4)
        if len(head)<4: return None
        if struct.unpack('<i',head)[0]!=size: raise ValueError('Nieprawidłowy znacznik rekordu SLCF.')
        payload=stream.read(size); tail=stream.read(4)
        if len(payload)!=size or len(tail)!=4: return None
        if struct.unpack('<i',tail)[0]!=size: raise ValueError('Uszkodzony końcowy znacznik SLCF.')
        return payload

    def peek(self):
        if self.pending is not None: return self.pending
        if not self.path.is_file(): return None
        with self.path.open('rb') as f:
            f.seek(self.offset)
            time= self.record(f,4)
            if time is None: return None
            payload=self.record(f,int(np.prod(self.shape))*4)
            if payload is None: return None
            values=np.frombuffer(payload,dtype='<f4').reshape(self.shape,order='F')[1:,1:,1:]
            timestamp=struct.unpack('<f',time)[0]
            if not np.isfinite(timestamp) or not np.isfinite(values).all(): raise ValueError('Niefinitywne dane SLCF.')
            self.offset=f.tell(); self.pending=(timestamp,values)
        return self.pending

class ProgressiveConverter:
    def __init__(self,folder,config,profile,ident,attempt):
        self.folder=Path(folder); self.config=config; self.profile=profile
        self.streams=None; self.sim=None
        from .incremental import CSVSeries
        self.series_reader=CSVSeries(self.folder/'ignis_hrr.csv');self.device_reader=CSVSeries(self.folder/'ignis_devc.csv')
        self.published_token=None
        bounds,cells=geometry(config)
        coords={a:(np.linspace(bounds[i*2],bounds[i*2+1],cells[i]+1)[:-1]+(bounds[i*2+1]-bounds[i*2])/cells[i]/2).tolist() for i,a in enumerate('xyz')}
        self.meta=dict(id=ident,attempt=attempt,config=config.canonical(),profile=profile.identity(),solver='FDS '+SOLVER_VERSION,
                       model=MODEL_VERSION,transport=TRANSPORT_VERSION,dimensions=list(cells),coordinates=coords,times=[],extrema=[],channels=CHANNELS,
                       elapsed=0,series={},devices={},source='FDS cell-centered 3D slices; float32',solidBounds=[],revision=0,complete=False,status='running',
                       rendering='Rekonstrukcja emisji i absorpcji; kolor nie jest pomiarem temperatury.')
        from .meshes import partition
        layout=getattr(profile,'layout','single' if profile.ranks==1 else f'z{profile.ranks}')
        self.meta['meshLayout']=partition(cells,layout)
        self.meta['diagnosticsRecipe']=getattr(profile,'diagnostics','none')
        (self.folder/'preview/frames').mkdir(parents=True,exist_ok=True)
        self.publish()

    def publish(self):
        token=(self.meta['revision'],self.meta['status'],self.meta['complete'],len(self.meta.get('series',{}).get('Time',[])),len(self.meta.get('devices',{}).get('Time',[])))
        if token==self.published_token:return
        atomic_json(self.folder/'preview/manifest.json',self.meta)
        self.published_token=token

    def initialize(self,final=False):
        if self.streams is not None: return True
        if not all((self.folder/name).exists() for name in ('ignis.smv','ignis_hrr.csv','ignis_steps.csv')): return False
        if not final and any((self.folder/name).stat().st_size<150 for name in ('ignis_hrr.csv','ignis_steps.csv')): return False
        try:
            sim=fdsreader.Simulation(str(self.folder))
            selected=[next(s for s in sim.slices if s.quantity.name.upper()==q) for q in QUANTITIES]
            if any(len(s.subslices)!=self.profile.ranks for s in selected): return False
            streams=[]; dims=self.meta['dimensions']; coords=self.meta['coordinates']
            covered=np.zeros(tuple(dims)+(7,),dtype=np.uint8)
            for channel,s in enumerate(selected):
                for sub in s.subslices:
                    nodes=sub.get_coordinates(ignore_cell_centered=True); starts=[]; ends=[]
                    for axis,a in enumerate('xyz'):
                        step=coords[a][1]-coords[a][0]
                        origin=coords[a][0]-step/2
                        start=round((float(nodes[a][0])-origin)/step)
                        end=start+len(nodes[a])-1;starts.append(start);ends.append(end)
                        expected=origin+np.arange(start,end+1)*step
                        tolerance=min(SMV_COORD_ATOL,step*.05)
                        if start<0 or end>dims[axis] or not np.allclose(nodes[a],expected,atol=tolerance,rtol=0):
                            raise MeshGeometryError(f'Niezgodna geometria podsiatki {sub.mesh.id}, oś {a}.')
                    region=tuple(slice(a,b) for a,b in zip(starts,ends))
                    covered[region+(channel,)]+=1
                    streams.append((channel,region,SliceStream(self.folder/sub.filename,sub.dimension.shape(cell_centered=False))))
            if not np.all(covered==1): raise MeshGeometryError('Luki lub nakładające się siatki CFD.')
            self.sim=sim;self.streams=streams
            self.meta['solidBounds']=[o.bounding_box.as_list() for o in sim.obstructions]
            return True
        except MeshGeometryError:
            raise
        except (ValueError,KeyError,IndexError,StopIteration,OSError,AssertionError):
            if final: raise
            return False

    def drain(self,elapsed=0,final=False,stop=None,max_frames=2):
        if not self.initialize(final):
            if final: raise ValueError('Niekompletne metadane siatek FDS.')
            return 0
        count=0
        while final or count<max_frames:
            if stop and stop.is_set(): return count
            records=[s.peek() for _,_,s in self.streams]
            if any(r is None for r in records): break
            times=[r[0] for r in records]
            if max(times)-min(times)>1e-5: raise ValueError('Niezgodne czasy pól lub podsiatek FDS.')
            if self.meta['times'] and times[0]<=self.meta['times'][-1]: raise ValueError('Nierosnące czasy FDS.')
            frame=np.empty(tuple(self.meta['dimensions'])+(7,),dtype='<f4')
            for (channel,region,s),(_,values) in zip(self.streams,records):
                frame[region+(channel,)]=values; s.pending=None
            frame=frame.transpose(2,1,0,3).copy()
            i=len(self.meta['times']); path=self.folder/'preview/frames'/f'{i:05d}.bin'
            pending=path.with_suffix('.pending'); frame.tofile(pending); pending.replace(path)
            self.meta['times'].append(times[0])
            self.meta['extrema'].append(dict(temperature=float(frame[...,0].max()),hrr=float(frame[...,1].max()),velocity=float(np.linalg.norm(frame[...,4:],axis=-1).max())))
            self.meta.update(revision=i+1,elapsed=elapsed)
            count+=1
        if count:
            self.meta.update(series=self.series_reader.read(),devices=self.device_reader.read())
            self.meta.update(seriesUnits=self.series_reader.units,deviceUnits=self.device_reader.units)
            self.publish()
        if final:
            if any(s.peek() is not None for _,_,s in self.streams): raise ValueError('Niekompletny zestaw końcowych pól FDS.')
            if not self.meta['times'] or abs(self.meta['times'][-1]-self.config.duration)>.051: raise ValueError('Niepełny czas końcowego wyniku FDS.')
        return count

    def finish(self,elapsed,status='completed'):
        self.meta.update(elapsed=elapsed,status=status,complete=status=='completed')
        if status=='completed':
            self.meta.update(series=self.series_reader.read(),devices=self.device_reader.read())
            self.meta.update(seriesUnits=self.series_reader.units,deviceUnits=self.device_reader.units)
        self.publish()
        return self.meta
