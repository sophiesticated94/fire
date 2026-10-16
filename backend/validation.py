"""Fixed regression gates; never loosened automatically to promote MPI."""
import json
from pathlib import Path
import numpy as np
from .progressive import QUANTITIES,SMV_COORD_ATOL

def frame_path(folder,meta,i):
    return folder/('preview/frames' if meta.get('frameDirectory')=='preview/frames' else 'frames')/f'{i:05d}.bin'

def mean_field(folder,meta,times):
    shape=tuple(meta['dimensions'][::-1])+(7,)
    total=np.zeros(shape,dtype=np.float64)
    native=np.asarray(meta['times'])
    for t in times:
        hi=min(int(np.searchsorted(native,t)),len(native)-1);lo=max(hi-1,0)
        b=np.fromfile(frame_path(folder,meta,hi),dtype='<f4').reshape(shape)
        if hi==lo or abs(native[hi]-t)<1e-6: total+=b;continue
        a=np.fromfile(frame_path(folder,meta,lo),dtype='<f4').reshape(shape)
        weight=(t-native[lo])/(native[hi]-native[lo]);total+=a*(1-weight)+b*weight
    return total/len(times)

def ignition(meta):
    time=meta['series'].get('Time',[]);power=np.asarray(meta['series'].get('HRR',[]))*1000
    for i in range(max(0,len(power)-2)):
        if np.all(power[i:i+3]>10): return float(time[i])
    return None

def compare(reference,candidate):
    reference,candidate=Path(reference),Path(candidate)
    r=json.loads((reference/'result.json').read_text(encoding='utf-8'));c=json.loads((candidate/'result.json').read_text(encoding='utf-8'))
    if r['config']!=c['config'] or r['dimensions']!=c['dimensions']: raise ValueError('Porównanie różnych konfiguracji lub siatek.')
    for axis in 'xyz': np.testing.assert_allclose(r['coordinates'][axis],c['coordinates'][axis],atol=1e-7,rtol=0)
    duration=r['config']['duration'];times=np.arange(duration/2,duration+.00001,.1)
    a=mean_field(reference,r,times);b=mean_field(candidate,c,times)
    a[...,0]-=r['config']['ambient'];b[...,0]-=r['config']['ambient']
    floors=[50,10,1e-7,1,.05,.05,.05];thresholds=[.1,.2,.25,.005,.2,.2,.2]
    def errors(x,y):
        output=[]
        for channel in range(7):
            rms=float(np.sqrt(np.mean((x[...,channel]-y[...,channel])**2)))
            denominator=1 if channel==3 else max(float(np.sqrt(np.mean(x[...,channel]**2))),floors[channel])
            value=rms/denominator;output.append(dict(channel=QUANTITIES[channel],error=value,limit=thresholds[channel],passed=value<=thresholds[channel]))
        return output
    metrics=errors(a,b)
    ranks=c.get('profile',{}).get('ranks',1);interface=[]
    if ranks>1:
        planes=[]
        for i in range(1,ranks):
            k=c['dimensions'][2]*i//ranks;planes.extend([k-1,k])
        interface=errors(a[planes],b[planes])
    def energy(m): return float(np.trapezoid(m['series']['HRR'],m['series']['Time']))
    er,ec=energy(r),energy(c);energy_error=abs(er-ec)/max(abs(er),1e-6)
    ir,ic=ignition(r),ignition(c)
    ignition_error=0 if ir is None and ic is None else (abs(ir-ic) if ir is not None and ic is not None else None)
    ignition_pass=r['config']['scene']!='wood' or (ignition_error is not None and ignition_error<=.2)
    # Probes are reported independently, not silently substituted for volume gates.
    probes={}
    for key,values in r.get('devices',{}).items():
        if key=='Time' or key not in c.get('devices',{}): continue
        t=np.asarray(r['devices']['Time']);other=np.interp(t,c['devices']['Time'],c['devices'][key])
        probes[key]=dict(rms=float(np.sqrt(np.mean((np.asarray(values)-other)**2))))
    return dict(passed=all(m['passed'] for m in metrics+interface) and energy_error<=.05 and ignition_pass,
                fields=metrics,interfaces=interface,energyError=energy_error,energyLimit=.05,ignitionErrorSeconds=ignition_error,
                ignitionLimitSeconds=.2,probes=probes,window=[duration/2,duration])

def verify_native(folder):
    """Independent fdsreader reference, all channels, times and interface cells."""
    import fdsreader
    folder=Path(folder);meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
    sim=fdsreader.Simulation(str(folder))
    for channel,q in enumerate(QUANTITIES):
        sl=next(s for s in sim.slices if s.quantity.name.upper()==q)
        array,coords=sl.to_global(return_coordinates=True)
        np.testing.assert_allclose(sl.times,meta['times'],rtol=0,atol=1e-6)
        # fdsreader infers coordinates from rounded SMV nodes. Our coordinates
        # retain the uniform grid specified in the input deck; no field values
        # are interpolated or rounded to accommodate the printed coordinates.
        for axis in 'xyz': np.testing.assert_allclose(coords[axis],meta['coordinates'][axis],atol=SMV_COORD_ATOL,rtol=0)
        for i in range(len(meta['times'])):
            frame=np.fromfile(frame_path(folder,meta,i),dtype='<f4').reshape(tuple(meta['dimensions'][::-1])+(7,))
            np.testing.assert_array_equal(frame[...,channel],array[i].transpose(2,1,0))
        sl.clear_cache() if hasattr(sl,'clear_cache') else None
        del array
    return True
