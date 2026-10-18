"""Export bounded evidence, keeping diagnosis separate from chemistry acceptance."""
import argparse
import hashlib
import json
from pathlib import Path


def load(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    return data.get('payload',data)


def maxima(rows,key):
    return {k:max((row[key][k] for row in rows),default=0.) for k in ['temperature','species','radicals']}


def build(directory,repairs):
    directory=Path(directory)
    divergence=load(directory/'chemistry-divergence.json')
    baseline=load(directory/'chemistry-schedule.json')
    refined=load(directory/'chemistry-schedule-r8.json')
    pointwise=load(directory/'pointwise-ignition.json')
    run=load(directory/'run.json')
    old=baseline['prescribedSchedule'];new=refined['prescribedSchedule']
    base_errors=maxima(old['rows'],'errorAgainstReactorNet')
    fine_errors=maxima(new['rows'],'errorAgainstReactorNet')
    implementation_errors=maxima(old['rows'],'errorAgainstGPU')
    identified=(divergence.get('completeAcceptedCoverage',False) and old['status']=='PASS' and new['status']=='PASS' and
                len(old['rows'])==len(new['rows'])==len(divergence['observations']) and
                base_errors['temperature']>1 and fine_errors['temperature']<=1 and
                implementation_errors['temperature']<=1)
    matrix_status='INCOMPLETE' if any(x['fdSensitivityWeighted']>.001 for x in pointwise['states']) else pointwise.get('jacobianStatus','INCOMPLETE')
    repair_reports=[]
    for path in repairs:
        campaign=load(Path(path)/'chemistry-campaign.json')
        item={k:campaign.get(k) for k in ['version','sourceSha256','status','criteria','precision','localErrorTarget','adapter','budget','pointwise','stopTime','error']}
        item['results']=[{k:r[k] for k in ['physicalTime','profile','rejections','validation']} for r in campaign['results']]
        last=campaign['results'][-1] if campaign['results'] else None
        if last:
            validation=load(last['validationPath']);item['validation']=validation
            if last.get('effectiveSource'):
                item['effectiveSource']=last['effectiveSource']
                item['sourceInspectionRaw']=Path(last['inspectionPath']).read_text(encoding='utf-8')
            # Complete accepted state, controller and samples for independent
            # revalidation, even when a proposed repair fails before ignition.
            source=Path(last['validationPath'].replace('.validation.json','.input.json'))
            if source.exists():
                item['reproduction']=load(source)
                if item['precision'] is None:item['precision']=item['reproduction']['checkpoint']['precision']
        repair_reports.append(item)
    expected=[divergence['firstExceedance'],divergence['observations'][-1]]
    ledger=Path(__file__).resolve().parents[1]/'artifacts/gpu-v14/chemistry-budget.json'
    budget=load(ledger) if ledger.exists() else None
    current_status=repair_reports[-1]['status'] if repair_reports else 'FAIL'
    return dict(schema=1,acceptanceStatus=current_status,historicalAcceptanceStatus='FAIL',
        diagnosisStatus='IDENTIFIED' if identified else 'UNRESOLVED',
        diagnosisScope='Dominant temperature trajectory error in the measured ignition window; not all GRI30 numerical errors.',
        dominantCause='Accumulated backward Euler time discretization under local-only error control' if identified else None,
        solverMechanism=dict(species=53,reactions=325),
        campaignBudgetSnapshotBeforeExport={k:budget[k] for k in ['limitMs','usedMs']} if budget else None,
        adapter=run['adapter'],sourceSha256=run['sourceSha256'],
        firstExceedance=divergence['firstExceedance'],firstSourceExceedance=divergence.get('firstSourceExceedance'),
        initialAudit={**divergence['initialAudit'],
            'gpuTargetEnthalpy':divergence['probes'][0]['targetEnthalpy'],
            'gpuTargetBiasJkg':divergence['probes'][0]['targetEnthalpy']-divergence['initialAudit']['enthalpyFloat32']},
        units=dict(time='s',profiles='ms',enthalpy='J/kg',speciesRHS='s^-1',
            singleStepError='weighted by integrator tolerance',trajectoryError='weighted by acceptance limit'),
        window=dict(steps=len(divergence['observations']),end=divergence['observations'][-1]['time'],
                    baselineGPU=maxima(divergence['observations'],'metrics'),
                    float64SameSchedule=base_errors,float64Refined8=fine_errors,gpuVsFloat64BE=implementation_errors),
        pointwise=dict(rhsStatus='FAIL' if any(x['rhsWeighted']>.001 for x in pointwise['states']) else 'PASS',
                       jacobianStatus=matrix_status,threshold=.001,
                       measurements=[{k:x[k] for k in ['time','rhsWeighted','jacobianWeighted','fdSensitivityWeighted']} for x in pointwise['states']]),
        repairs=repair_reports,
        reproduction=dict(initial=divergence['initialAudit']['original'],gpuInitial=divergence['initialAudit']['float32'],
            schedule=[[x['time'],x['dt']] for x in divergence['observations']],expected=expected,
            singleSteps=divergence['probes'],pointwiseInput=load(directory/'pointwise-input.json')),
        rawTrace=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(directory.glob('trace-*.json')) if p.stem.removeprefix('trace-').isdigit()],
        limitations=['The diagnostic window is not a full 0.5 s reactor acceptance.',
                     'Finite-difference Jacobian sensitivity prevents attributing all matrix discrepancies to GPU AD.',
                     'Compensated-state is not full double-single chemistry; rates, coefficients, Jacobian and LU remain float32.',
                     'Full 0D, performance promotion, scaling and 3D burner remain blocked.'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('output',type=Path);p.add_argument('--repair',type=Path,action='append',default=[])
    args=p.parse_args();report=build(args.directory,args.repair)
    args.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['acceptanceStatus','diagnosisStatus','window']}))
