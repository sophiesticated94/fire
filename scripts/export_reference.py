"""Independent check using the original NIST fds2ascii executable."""
from pathlib import Path
import json
import subprocess
import sys
import numpy as np

root=Path(__file__).resolve().parent.parent
folder=Path(sys.argv[1]).resolve()
meta=json.loads((folder/'result.json').read_text(encoding='utf-8'))
end=meta['times'][-1]
stdin=f'ignis\n2\n1\nn\n{end-0.0001} {end+0.0001}\n7\n1\n2\n3\n4\n5\n6\n7\nreference.csv\n'
exe=root/'tools/fds/firemodels/FDS6/bin/fds2ascii.exe'
r=subprocess.run([str(exe)],cwd=folder,input=stdin,text=True,capture_output=True,timeout=30)
(folder/'reference.log').write_text(r.stdout+r.stderr,encoding='utf-8')
print(r.stdout[-1800:])
if r.returncode: raise RuntimeError(r.stderr)
p=folder/'reference.csv'
if not p.exists(): raise RuntimeError('NIST fds2ascii did not generate reference.csv')
print(p)
table=np.loadtxt(p,delimiter=',',skiprows=2)
nx,ny,nz=meta['dimensions']
raw=table[:,3:].reshape(nz+1,ny+1,nx+1,7)[1:,1:,1:]
index=len(meta['times'])-1
transport=np.fromfile(folder/'frames'/f'{index:05d}.bin',dtype='<f4').reshape(nz,ny,nx,7)
np.testing.assert_allclose(raw,transport,rtol=6e-5,atol=1e-6)
report={'source':'NIST fds2ascii FDS 6.11.1','time':end,'cells':nx*ny*nz,'maxAbsoluteError':{c['name']:float(np.abs(raw[...,i]-transport[...,i]).max()) for i,c in enumerate(meta['channels'])},'tolerance':'rtol 6e-5, atol 1e-6 (ASCII precision)','passed':True}
(folder/'reference-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
