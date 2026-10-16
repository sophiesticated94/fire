"""Streaming space-time diagnostics. No automatic scientific threshold selection."""
from collections import OrderedDict
import json
from pathlib import Path
import numpy as np
from .validation import compare,frame_path
from .progressive import QUANTITIES
from .meshes import interface_mask
from .policy import VALIDATION_VERSION,validation_policy

FLOORS=np.array([50,10,1e-7,1,.05,.05,.05],dtype=float)

class FieldReader:
    def __init__(self,folder,meta):
        self.folder=Path(folder);self.meta=meta;self.times=np.asarray(meta['times'],dtype=float);self.cache=OrderedDict()
        if len(self.times)<2 or not np.isfinite(self.times).all() or np.any(np.diff(self.times)<=0):raise ValueError('Invalid field time axis')
        self.shape=tuple(meta['dimensions'][::-1])+(7,)
    def frame(self,i):
        if i not in self.cache:
            data=np.fromfile(frame_path(self.folder,self.meta,i),dtype='<f4')
            if data.size!=np.prod(self.shape) or not np.isfinite(data).all():raise ValueError('Invalid field frame')
            self.cache[i]=data.reshape(self.shape)
            while len(self.cache)>2:self.cache.popitem(last=False)
        return self.cache[i]
    def at(self,t):
        if t<self.times[0]-1e-5 or t>self.times[-1]+1e-5:raise ValueError('Field time coverage incomplete; extrapolation forbidden')
        hi=min(int(np.searchsorted(self.times,t)),len(self.times)-1)
        if abs(self.times[hi]-t)<=1e-5:return self.frame(hi).astype(np.float64)
        lo=max(0,hi-1)
        if hi==lo:raise ValueError('Cannot extrapolate')
        w=(t-self.times[lo])/(self.times[hi]-self.times[lo])
        return self.frame(lo).astype(np.float64)*(1-w)+self.frame(hi)*w

def normalized_metrics(diff2,reference2,count):
    if count<=0:return []
    reference=np.sqrt(reference2/count);rms=np.sqrt(diff2/count)
    denominator=np.maximum(reference,FLOORS);denominator[3]=1
    return [dict(channel=q,rms=float(rms[i]),referenceRms=float(reference[i]),error=float(rms[i]/denominator[i])) for i,q in enumerate(QUANTITIES)]

def stream_metrics(reference,candidate,r,c):
    a=FieldReader(reference,r);b=FieldReader(candidate,c)
    duration=float(r['config']['duration']);times=np.arange(0,duration+1e-6,.1)
    layout=c.get('profile',{}).get('layout','single' if c.get('profile',{}).get('ranks',1)==1 else f"z{c['profile']['ranks']}")
    mask=interface_mask(c['dimensions'],layout)
    accum={key:[np.zeros(7),np.zeros(7),0] for key in ('full','late','interfacesFull','interfacesLate')}
    sums=[np.zeros(a.shape),np.zeros(a.shape),np.zeros(a.shape),np.zeros(a.shape)];late_count=0
    for t in times:
        x=a.at(t);y=b.at(t);x[...,0]-=r['config']['ambient'];y[...,0]-=c['config']['ambient']
        late=t>=duration/2-1e-6
        for key,is_interface in [('full',False),('interfacesFull',True)]+([('late',False),('interfacesLate',True)] if late else []):
            xx=x[mask] if is_interface else x.reshape(-1,7);yy=y[mask] if is_interface else y.reshape(-1,7)
            if not xx.size:continue
            accum[key][0]+=np.square(xx-yy).sum(axis=0);accum[key][1]+=np.square(xx).sum(axis=0);accum[key][2]+=xx.shape[0]
        if late:
            sums[0]+=x;sums[1]+=y;sums[2]+=x*x;sums[3]+=y*y;late_count+=1
    std_a=np.sqrt(np.maximum(0,sums[2]/late_count-(sums[0]/late_count)**2))
    std_b=np.sqrt(np.maximum(0,sums[3]/late_count-(sums[1]/late_count)**2))
    variance=normalized_metrics(np.square(std_a-std_b).reshape(-1,7).sum(axis=0),np.square(std_a).reshape(-1,7).sum(axis=0),int(np.prod(a.shape[:-1])))
    return dict(times=times.tolist(),**{k:normalized_metrics(*v) for k,v in accum.items()},variability=variance)

def series_metrics(reference,candidate):
    results={}
    if set(reference)!=set(candidate):raise ValueError('Diagnostic channel coverage differs')
    if not reference:return results
    for series in (reference,candidate):
        t=np.asarray(series.get('Time',[]),dtype=float)
        if not len(t) or not np.isfinite(t).all() or np.any(np.diff(t)<=0):raise ValueError('Invalid diagnostic time axis')
    for key,values in reference.items():
        if key=='Time' or key not in candidate:continue
        t=np.asarray(reference['Time']);other_t=np.asarray(candidate.get('Time',[]))
        x=np.asarray(values,dtype=float);y=np.asarray(candidate[key],dtype=float)
        if not np.isfinite(x).all() or not np.isfinite(y).all():raise ValueError('Non-finite diagnostic series')
        if not len(other_t) or len(t)!=len(x) or len(other_t)!=len(y):raise ValueError('Invalid diagnostic series')
        if t[0]<other_t[0]-1e-5 or t[-1]>other_t[-1]+1e-5:raise ValueError('Diagnostic series coverage incomplete')
        y=np.interp(t,other_t,y)
        results[key]=dict(rms=float(np.sqrt(np.mean((x-y)**2))),referenceMean=float(x.mean()),candidateMean=float(y.mean()),
                          referenceStd=float(x.std()),candidateStd=float(y.std()),referenceRange=[float(x.min()),float(x.max())],candidateRange=[float(y.min()),float(y.max())])
    return results

def compare_v3(reference,candidate,scratch_root=None):
    from .run_data import open_run
    with open_run(reference,scratch_root,fields_only=True) as reference,open_run(candidate,scratch_root,fields_only=True) as candidate:
        r=json.loads((reference/'result.json').read_text(encoding='utf-8'));c=json.loads((candidate/'result.json').read_text(encoding='utf-8'))
        if not r.get('complete',True) or not c.get('complete',True):raise ValueError('Incomplete results cannot be compared for promotion')
        legacy=compare(reference,candidate)
        temporal=stream_metrics(reference,candidate,r,c)
        if r.get('deviceUnits')!=c.get('deviceUnits') or r.get('seriesUnits')!=c.get('seriesUnits'):raise ValueError('Diagnostic units differ')
        devices=series_metrics(r.get('devices',{}),c.get('devices',{}))
        for name,metric in devices.items():metric['unit']=r.get('deviceUnits',{}).get(name)
        policy=validation_policy();checks=[]
        if policy['approved']:
            limits=policy['data']['temporalLimits']
            for window in ('full','late','interfacesFull','interfacesLate','variability'):
                for item in temporal[window]:
                    limit=limits.get(window,{}).get(item['channel'])
                    checks.append(limit is not None and item['error']<=float(limit))
            for name,limit in policy['data']['diagnosticLimits'].items():checks.append(name in devices and devices[name]['rms']<=float(limit))
            # Instrumented diagnostics are mandatory for promotion, even when
            # an old seven-field run can be fully re-evaluated diagnostically.
            checks.append(c.get('diagnosticsRecipe')=='flux-1' and r.get('diagnosticsRecipe')=='flux-1')
        eligible=bool(policy['approved'] and legacy['passed'] and checks and all(checks))
        return dict(validationVersion=VALIDATION_VERSION,policyHash=policy['hash'],status='approved' if eligible else ('rejected' if policy['approved'] else 'pending-review'),
                    legacy=legacy,temporal=temporal,devices=devices,hrr=series_metrics(r.get('series',{}),c.get('series',{})),
                    diagnosticsAvailable=c.get('diagnosticsRecipe')=='flux-1' and r.get('diagnosticsRecipe')=='flux-1',promotionEligible=eligible)
