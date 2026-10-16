"""Pinned upstream Windows builds with explicit, reproducible CPU variants.

Run from an initialized Intel 2025.2 / VS2022 developer shell. Installation
is deliberately separate: preflight reports missing prerequisites and space.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.engine import ROOT,solver_path
from backend.profiles import fingerprint
from backend.progressive import atomic_json

REVISION='ff928dbf68a2623ced3a007be75391c6dc6c9f90'
VARIANTS={'precise-o2':'/fp:precise','avx2-o3':'/fp:precise /O3 /QxCORE-AVX2 /Qopt-report:5'}


def capture(args,cwd=None):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,errors='replace')
    return dict(code=p.returncode,stdout=p.stdout,stderr=p.stderr)


def preflight(root):
    missing=[];tools={k:shutil.which(k) for k in ('ifx','make','git','link')}
    for name,path in tools.items():
        if not path:missing.append(f'{name} not found in initialized developer PATH')
    compiler=capture([tools['ifx'],'/QV']) if tools['ifx'] else None
    if compiler and '2025.2' not in compiler['stdout']+compiler['stderr']:missing.append('Expected Intel ifx 2025.2')
    vs=os.environ.get('VisualStudioVersion','')
    if not vs.startswith('17.'):missing.append('Initialize supported Visual Studio 2022 (17.x) C++ developer shell')
    dependencies={}
    for name,relative in [('I_MPI_ROOT','lib/impi.lib'),('MKLROOT','include/mkl.fi'),('HYPRE_HOME','lib/HYPRE.lib'),('SUNDIALS_HOME','lib/sundials_cvode_static.lib')]:
        directory=Path(os.environ.get(name,'__missing__'));path=directory/relative
        dependencies[name]=str(directory.resolve()) if path.is_file() else None
        if not path.is_file():missing.append(f'{name}: missing {relative}')
    for name,relative,version in [('HYPRE_HOME','include/HYPRE_config.h','3.0.0'),('SUNDIALS_HOME','include/sundials/sundials_config.h','7.5.0')]:
        header=Path(os.environ.get(name,'__missing__'))/relative
        if not header.is_file() or version not in header.read_text(errors='replace'):missing.append(f'{name}: expected version {version} in {relative}')
    launcher=Path(os.environ.get('I_MPI_ROOT','__missing__'))/'bin/mpiexec.exe'
    mpi=capture([str(launcher),'-version']) if launcher.is_file() else None
    if not mpi or '2021.16' not in mpi['stdout']+mpi['stderr']:missing.append('Expected developer Intel MPI 2021.16')
    free=shutil.disk_usage(root).free
    # Build scratch + first research data + minimum OS reserve. Installers,
    # extracted payloads and VS components require their own explicit sizing.
    required=3*1024**3+4*1024**3+3*1024**3
    if free<required:missing.append('Need 10 GiB free before a build, excluding installer payloads')
    return dict(ready=not missing,missing=missing,tools=tools,compiler=compiler,mpi=mpi,visualStudio=vs,dependencies=dependencies,
                freeBytes=free,requiredBytes=required,revision=REVISION,variants=VARIANTS,
                installStatus='not-installed-by-this-tool',thirdPartyVersions=dict(hypre='3.0.0',sundials='7.5.0',intelMPI='2021.16'))


def build(source,output,variant,report):
    if not report['ready']:raise RuntimeError('Preflight failed; see report')
    source=source.resolve();output=output.resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('Output directory must be empty')
    if not source.exists():
        subprocess.run(['git','clone','--filter=blob:none','--no-checkout','https://github.com/firemodels/fds.git',str(source)],check=True)
        subprocess.run(['git','checkout','--detach',REVISION],cwd=source,check=True)
    if capture(['git','rev-parse','HEAD'],source)['stdout'].strip()!=REVISION:raise ValueError('Wrong FDS revision')
    if capture(['git','status','--porcelain'],source)['stdout'].strip():raise ValueError('Source must be clean')
    output.mkdir(parents=True,exist_ok=True);stock=solver_path()
    if not stock:raise FileNotFoundError('Installed stock FDS required for runtime DLLs')
    for dll in stock.parent.glob('*.dll'):shutil.copy2(dll,output/dll.name)
    library_hashes={}
    for name,directory in report['dependencies'].items():
        for path in Path(directory).rglob('*.lib'):library_hashes[f'{name}/{path.relative_to(directory).as_posix()}']=fingerprint(path)
    original=(source/'Build/makefile').read_text()
    # Keep upstream compiler/link targets and their physical feature macros.
    # Per-variant additions affect CPU code generation, not FDS input/stability.
    makefile=original.replace('/wrap-margin-',f'/wrap-margin- {VARIANTS[variant]}')
    for target,binary in [('impi_intel_win_openmp','fds_openmp.exe'),('impi_intel_win','fds.exe')]:
        work=output/target;work.mkdir();(work/'makefile').write_text(makefile)
        command=['make','-f','makefile',target,f'VPATH={(source/"Source").as_posix()}','COMP_FC=ifx',
                 'GIT_HASH='+REVISION,'GIT_STAT=','GIT_BRANCH=detached','GIT_DATE='+capture(['git','log','-1','--format=%cd'],source)['stdout'].strip()]
        with (work/'build.log').open('w') as log:
            subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)
        generated=work/(target+'.exe')
        shutil.copy2(generated,output/binary)
    atomic_json(output/'build-manifest.json',dict(revision=REVISION,variant=variant,extraFlags=VARIANTS[variant],preflight=report,
                 sourceMakefileSha256=fingerprint(source/'Build/makefile'),libraries=library_hashes,
                 binaries={p.name:fingerprint(p) for p in output.glob('*.exe')},productionApproved=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'tools/fds-source-6.11.1')
    p.add_argument('--output',type=Path,default=ROOT/'tools/fds-builds/precise-o2');p.add_argument('--variant',choices=list(VARIANTS),default='precise-o2')
    p.add_argument('--preflight',action='store_true');p.add_argument('--report',type=Path,default=ROOT/'artifacts/build-preflight-v3.json');a=p.parse_args()
    report=preflight(ROOT);a.report.parent.mkdir(parents=True,exist_ok=True);atomic_json(a.report,report)
    print(json.dumps(report,indent=2))
    if not a.preflight:build(a.source,a.output,a.variant,report)
