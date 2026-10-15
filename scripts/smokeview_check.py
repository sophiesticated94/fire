"""Attempt the official Smokeview batch reader (unsupported on some Windows builds)."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parent.parent
case=Path(sys.argv[1]).resolve()
out=root/'artifacts/smokeview'
out.mkdir(parents=True,exist_ok=True)
script=out/'verify.ssf'
script.write_text("LOADSLCF\nQUANTITY='TEMPERATURE' PB3D=T\nSETTIMEVAL\n1.0\n",encoding='ascii')
exe=root/'tools/fds/firemodels/SMV6/smokeview.exe'
result=subprocess.run([str(exe),'-htmlscript',str(script),'ignis'],cwd=case,capture_output=True,timeout=60)
(out/'export.log').write_bytes(result.stdout+result.stderr)
print(result.returncode)
print(result.stdout.decode(errors='replace')[-4000:])
print(result.stderr.decode(errors='replace')[-2000:])
if result.returncode or b'***error' in result.stdout.lower() or b'fatal' in result.stderr.lower():
    raise RuntimeError('Smokeview batch verification unavailable; inspect artifacts/smokeview/export.log. Use export_reference.py for independent NIST numeric checks.')
sys.exit(result.returncode)
