// Export portable measured evidence; never infer missing horizons or scaling.
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {readCheckpoint} from './chemistry_checkpoint.mjs';

const folders=process.argv.slice(2);
const outputIndex=folders.indexOf('--output');
const output=outputIndex<0?'docs/chemistry-acceptance-1.4.json':folders.splice(outputIndex,2)[1];
if(!output)throw Error('Missing report output');
if(!folders.length)throw Error('Usage: node scripts/report_chemistry_campaign.mjs <campaign directory> [...]');
const portable=p=>relative(process.cwd(),resolve(p)).replaceAll('\\','/');
const digest=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
function residual(system,x){
  const n=x.length;let r=0,a=0,b=0;
  for(let row=0;row<n;row++){
    let dot=0,sum=0;for(let col=0;col<n;col++){const v=system[row*(n+1)+col];dot+=v*x[col];sum+=Math.abs(v);}
    const rhs=system[row*(n+1)+n];r=Math.max(r,Math.abs(dot-rhs));a=Math.max(a,sum);b=Math.max(b,Math.abs(rhs));
  }
  return r/Math.max(1e-30,a*Math.max(...x.map(Math.abs))+b);
}
const measurements=folders.map(folder=>{
  const manifest=resolve(folder,'chemistry-campaign.json'),c=readCheckpoint(manifest);
  const snapshots=(c.precisionProbes??[]).filter(p=>p.inspection).map(p=>p.inspection);
  if(new Set(snapshots).size!==snapshots.length)throw Error('Diagnostic matrix path reused; cannot audit historical probes');
  const failure=c.failure?JSON.parse(readFileSync(c.failure.validationPath,'utf8')):null;
  const stages={};let wallMs=0,readbacks=0,submissions=0;
  for(const r of c.results){wallMs+=r.profile.wallMs;readbacks+=r.profile.statusReads;submissions+=r.profile.submissions;
    for(const [stage,ms] of Object.entries(r.profile.gpuMs??{}))stages[stage]=(stages[stage]??0)+ms;}
  const probes=(c.precisionProbes??[]).map(p=>{
    if(p.error)return {id:p.id,status:'INCOMPLETE',error:p.error};
    const systems=JSON.parse(readFileSync(p.inspection,'utf8')).systems;
    return {id:p.id,reports:p.reports,singleWallMs:p.single.wallMs,doubleSingleWallMs:p.extended.wallMs,
      singleBackwardErrors:p.single.systems.map((s,i)=>s.failed?null:residual(systems[i],s.solution)),
      doubleSingleBackwardErrors:p.extended.systems.map((s,i)=>s.failed?null:residual(systems[i],s.solution)),
      singleBufferBytes:p.single.storageBytes,doubleSingleBufferBytes:p.extended.storageBytes};
  });
  let resources=null,reproduction=null;
  if(c.results.length){
    const last=readCheckpoint(resolve(folder,c.results.at(-1).id+'.checkpoint.json'));
    const cp=last.checkpoint;
    reproduction={caseIds:last.caseIds,checkpoint:cp,
      lastInspection:JSON.parse(readFileSync(c.results.at(-1).inspectionPath??resolve(folder,c.results.at(-1).id+'.inspection.json'),'utf8'))};
    const n=cp.initial.length,s=cp.sampleTimes.length;
    const mechanismBytes=JSON.parse(readFileSync('src/gpu/chemistry/data/mechanism.json','utf8')).data.length*4;
    const sizes=[n*54*4,n*270*4,n*2970*4,n*8*4,n*40*4,(4+s)*4,n*s*54*4,64,576,512,Math.min(n,4)*3342*4];
    resources={reactors:n,samples:s,declaredBufferBytes:sizes.reduce((a,b)=>a+b,mechanismBytes),
      declaredWorkgroupBytes:c.linearSolver==='refined-lu'?13212:12780,
      source:'GPUBuffer descriptor sizes plus shared mechanism; excludes driver/compiler/private allocations',browserPeakRamBytes:null};
  }
  return {directory:portable(folder),manifestSha256:digest(manifest),sourceSha256:c.sourceSha256,integrator:c.version,
    mechanismSha256:c.mechanismSha256,adapter:c.adapter,linearSolver:c.linearSolver,status:c.status,criteria:c.criteria,
    budget:c.budget,pointwise:c.pointwise,wallMs,gpuStageMs:stages,statusReads:readbacks,submissions,
    slices:c.results.map(r=>({id:r.id,time:r.physicalTime,stopReason:r.stopReason,wallMs:r.profile.wallMs,rejections:r.rejections})),
    failure:failure?{validationSha256:digest(c.failure.validationPath),reactors:failure.reactors.map(({samples,...r})=>r)}:null,
    resources,reproduction,fullChemistryPrecision:'float32',precisionProbeIsFullChemistry:false,precisionProbes:probes,error:c.error};
});
const evidence={date:new Date().toISOString(),units:{wall:'ms',gpu:'ms',physicalTime:'s'},
  status:measurements.some(m=>m.status==='FAIL')?'FAIL':measurements.every(m=>m.status==='PASS')?'PASS':'INCOMPLETE',measurements};
writeFileSync(output,JSON.stringify(evidence,null,2)+'\n');
console.log(JSON.stringify(measurements.map(m=>({solver:m.linearSolver,status:m.status,wallMs:m.wallMs,gpuStageMs:m.gpuStageMs,failures:m.failure?.reactors.map(r=>r.metrics)})),null,2));
