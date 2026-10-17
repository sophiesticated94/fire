"""Summarize measured GPU runs without promoting an unvalidated solver."""
import hashlib
import json
from pathlib import Path
import statistics
import re
import platform
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts/gpu-v14'


def sor(path):
    data = json.loads(path.read_text())
    groups = []
    for render in sorted({trial['render'] for trial in data['trials']}):
        for mode in ['reference', 'batched']:
            windows = []
            for trial in data['trials']:
                if trial['mode'] != mode or trial['render'] != render:
                    continue
                samples = [sample for cycle in trial['cycles'] for sample in cycle['samples']]
                physical = sum(cycle['physical'] for cycle in trial['cycles'])
                windows.append(dict(wallSeconds=trial['wallSeconds'], physicalSeconds=physical,
                    throughput=physical/trial['wallSeconds'], fps=trial['frames']/trial['wallSeconds'],
                    stepWallMs=statistics.median(s['wallMs'] for s in samples),
                    stepGpuMs=statistics.median(s['gpuMs'] for s in samples if s['gpuMs'] is not None),
                    pressureReadbacksMean=statistics.mean(s['pressureReadbacks'] for s in samples),
                    pressureWallMs=statistics.median(s['pressureWallMs'] for s in samples),
                    iterationsMean=statistics.mean(s['iterations'] for s in samples),
                    maxMassError=max(s['cumulativeMassError'] for s in samples),
                    maxDivergence=max(s['normalizedDivergence'] for s in samples),
                    allocatedBytes=max(s['allocatedBytes'] for s in samples)))
            rates = [w['throughput'] for w in windows]
            groups.append(dict(mode=mode, render=render, windows=windows,
                medianThroughput=statistics.median(rates), minThroughput=min(rates), maxThroughput=max(rates),
                medianFps=statistics.median(w['fps'] for w in windows)))
    vendor = {'nvidia':'0x10de', 'intel':'0x8086'}.get(data['adapter']['vendor'])
    matches = [adapter for adapter in data['native']['adapters'] if adapter['vendor']==vendor
               and (not data['adapter']['device'] or adapter['device']==data['adapter']['device'])]
    native_match = len(matches)==1 and any(
        'luid_'+matches[0]['luid'].lower() in sample['Name'].lower()
        and float(sample['UtilizationPercentage'])>0 for sample in data['native']['samples'])
    return dict(adapter=data['adapter'], nativeActivityMatch=native_match,
        rtxVerified=data['rtxVerified'],protocol=data.get('protocol'),
        native=data['native'], userAgent=data['userAgent'], fullReadbacks=data['fullReadbacks'],
        source=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), groups=groups)


def main():
    # Run only after the final sequential measurements. Historical exploratory
    # runs in artifacts are never implicitly combined with a different workload.
    reports = [sor(p) for p in [ART/'sor-nvidia.json', ART/'sor-intel.json', ART/'sor-nvidia-confirmation.json'] if p.exists()]
    assert len(reports)==3 and all(report['nativeActivityMatch'] for report in reports), 'Missing hardware evidence'
    assert all(report['rtxVerified'] for report in reports if report['adapter']['vendor']=='nvidia')
    for report in reports:
        assert report['fullReadbacks']==0
        for group in report['groups']:
            assert len(group['windows'])==3 and all(window['wallSeconds']>=30 for window in group['windows'])
    jacobian = json.loads((ART/'chemistry-jacobian.json').read_text())
    reactor = json.loads((ART/'reactor-gate.json').read_text())
    conditioning = json.loads((ART/'conditioning.json').read_text())
    comparison = json.loads((ART/'reactor-comparison.json').read_text())
    wind = json.loads((ART/'wind-conservation-nvidia.json').read_text())
    def check(log):
        raw = (ROOT/'artifacts'/log).read_bytes()
        text = raw.decode('utf-8', errors='replace')
        return dict(summary=re.findall(r'^.*(?:passed|failed|built in).*$', text, re.M)[-1:],
                    sha256=hashlib.sha256(raw).hexdigest())
    report = dict(date='2026-10-16', generatedAt=datetime.now().astimezone().isoformat(), model='gpu-flow-0.2', grid=[32,32,64],
        platform=platform.platform(), processor=platform.processor(),
        measuredSourceHashes=json.loads((ART/'sor-source.json').read_text()),
        confirmationSourceHashes=json.loads((ART/'sor-confirmation-source.json').read_text()),
        diagnosticsPrecision=dict(before=json.loads((ART/'wind-diagnostic-before.json').read_text()),
            after=dict(steps=len(wind['steps']),physicalTime=wind['steps'][-1]['time'],
                maxStepMassError=max(m['massError'] for m in wind['steps']),
                maxCumulativeMassError=max(m['cumulativeMassError'] for m in wind['steps']),
                maxWeightedEnergyError=max(abs(m['energyError'])/max(1,abs(m['environmentEnergy'])+m['time']) for m in wind['steps']))),
        benchmark=dict(workload='repeated >=0.5 physical seconds from reset, including reset wall time',
                       warmupWallSeconds=10, measuredWindows=3, minimumWindowWallSeconds=30),
        sor=reports, chemistry=dict(accepted=False, mechanismSpecies=53, mechanismReactions=325,
            rhsError=max(r['rhsError'] for r in jacobian['results']),
            jacobianError=max(r['jacError'] for r in jacobian['results']),
            maxConditionInfinity=max(r['conditionInfinity'] for r in conditioning['rows']),
            reactor=reactor, comparison=comparison,
            timing='exploratory reactor run overlapped CPU regression; not an isolated chemistry throughput benchmark',
            unmeasured=['full reactor horizons', 'ignition delay', 'OH peak', '512/4096/65536 full chemistry']),
        checks=dict(python=check('gpu-v14-python-final.log'), fdsBrowser=check('gpu-v14-fds-ui.log'),
                    gpuFlow=check('gpu-v14-flow-final.log'), build=check('gpu-v14-build.log'),
                    chemistrySmoke=check('gpu-v14-chemistry-smoke.log'),intelPressure=check('gpu-v14-intel-validation.log'),
                    intelWind=check('gpu-v14-intel-wind.log'),
                    chemistryHorizon='incomplete; wall limit; not accepted'))
    (ROOT/'docs/benchmark-gpu-1.4.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Saved docs/benchmark-gpu-1.4.json')


if __name__ == '__main__':
    main()
