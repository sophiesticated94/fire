"""FDS-6.11.1 native diagnostic outputs, separate from visualization channels.

TOTAL MASS FLUX includes the solver's flux limiter and diffusion. ENTHALPY
FLUX is sensible enthalpy relative to ambient plus conductive transport.
Radiative gauge flux is reported separately, never added as a scalar surrogate.
"""
import csv
import io
from pathlib import Path
import re
import zipfile
import numpy as np

RECIPE='flux-1'

def diagnostic_lines(bounds,cells):
    lines=[]
    for axis,a in enumerate('XYZ'):
        for index in range(1,8):
            k=round(cells[axis]*index/8);step=(bounds[2*axis+1]-bounds[2*axis])/cells[axis]
            position=bounds[2*axis]+k*step;box=list(bounds);box[2*axis]=box[2*axis+1]=position
            xb=','.join(f'{v:.8f}' for v in box);point=[(bounds[2*j]+bounds[2*j+1])/2 for j in range(3)];point[axis]=position
            for prefix,quantity in [('mdot',f'TOTAL MASS FLUX {a}'),('qdot',f'ENTHALPY FLUX {a}')]:
                lines.append(f"&DEVC ID='{prefix}_{a}{index}', XB={xb}, QUANTITY='{quantity}', SPATIAL_STATISTIC='AREA INTEGRAL' /")
            xyz=','.join(f'{v:.8f}' for v in point)
            for prefix,quantity in [('mass_local',f'TOTAL MASS FLUX {a}'),('enthalpy_local',f'ENTHALPY FLUX {a}')]:
                lines.append(f"&DEVC ID='{prefix}_{a}{index}', XYZ={xyz}, QUANTITY='{quantity}' /")
            orient=','.join('1.' if j==axis else '0.' for j in range(3))
            lines.append(f"&DEVC ID='radiative_{a}{index}', XYZ={xyz}, QUANTITY='RADIATIVE HEAT FLUX GAS', ORIENTATION={orient} /")
            for sign,label in [(-1,'lo'),(1,'hi')]:
                p=list(point);p[axis]+=sign*step/2;xyz=','.join(f'{v:.8f}' for v in p)
                for prefix,quantity in [('pressure','PRESSURE'),('divergence','DIVERGENCE')]:
                    lines.append(f"&DEVC ID='{prefix}_{a}{index}_{label}', XYZ={xyz}, QUANTITY='{quantity}' /")
    return lines

def profile_steps(folder):
    folder=Path(folder)
    if folder.suffix=='.zip':
        with zipfile.ZipFile(folder) as z:
            texts=[z.read(name).decode(errors='replace') if name in z.namelist() else '' for name in ('ignis_steps.csv','ignis.out','ignis_cpu.csv')]
    else:texts=[(folder/name).read_text(errors='replace') if (folder/name).exists() else '' for name in ('ignis_steps.csv','ignis.out','ignis_cpu.csv')]
    return profile_texts(*texts)


def profile_texts(step_text,text,cpu_text):
    steps=[];cpu=[];indices=[];physical=[]
    rows=csv.reader(io.StringIO(step_text));next(rows);names=[n.strip() for n in next(rows)]
    for row in rows:
        if not row:continue
        record=dict(zip(names,row))
        steps.append(float(record['Step Size']));cpu.append(float(record['CPU Time']))
        indices.append(int(record['Time Step']));physical.append(float(record['Simulation Time']))
    if not indices or indices[0]<1 or np.any(np.diff(indices)<=0) or not np.isfinite(steps+cpu+physical).all():raise ValueError('Invalid native step records')
    actual_steps=indices[-1];all_steps=indices[0]==1 and len(indices)==actual_steps
    dt=np.asarray(steps)
    def numbers(pattern):return [float(v.replace('D','E')) for v in re.findall(pattern,text)]
    def summary(values):
        a=np.asarray(values)
        return dict(count=len(a),min=float(a.min()),median=float(np.median(a)),max=float(a.max())) if len(a) else dict(count=0)
    histogram=[]
    if len(dt):
        counts,edges=np.histogram(dt,bins=min(20,len(dt)))
        histogram=[dict(low=float(a),high=float(b),count=int(n)) for a,b,n in zip(edges[:-1],edges[1:],counts)]
    result=dict(version='step-profile-2',steps=actual_steps,recordedSteps=len(indices),allStepsRecorded=all_steps,
                meanPhysicalStepSeconds=physical[-1]/actual_steps,nativeCpuSecondsAtEnd=cpu[-1],stepSize=summary(steps),histogram=histogram,
                cfl=summary(numbers(r'Maximum CFL Number\s*:\s*([\d.E+\-]+)')),
                vn=summary(numbers(r'Maximum VN Number\s*:\s*([\d.E+\-]+)')),
                pressureIterations=summary(numbers(r'Pressure Iterations:\s*(\d+)')),
                velocityError=summary(numbers(r'Maximum Velocity Error:\s*([\d.E+\-]+)')),
                pressureError=summary(numbers(r'Maximum Pressure Error:\s*([\d.E+\-]+)')),
                sampling='Step-size histogram and CFL/VN/errors cover diagnostic records, not unrecorded steps; see allStepsRecorded',subsystemsPerStepEstimated={})
    if cpu_text:
        with io.StringIO(cpu_text) as f:
            for row in csv.DictReader(f):
                for key,value in row.items():
                    if key.strip()=='Rank':continue
                    try:result['subsystemsPerStepEstimated'][key.strip()]=result['subsystemsPerStepEstimated'].get(key.strip(),0)+float(value)/actual_steps
                    except (ValueError,TypeError):pass
    result['subsystemsMeaning']='aggregate subsystem time divided by step count; MPI sums rank times; not measured individual step costs'
    return result
