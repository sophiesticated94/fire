// Bounded diagnostic run. Shares the existing campaign ledger; no new budget.
import {chromium} from '@playwright/test';
import {createServer} from 'vite';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync,existsSync,mkdirSync,openSync,closeSync,unlinkSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
import {atomicWrite,readCheckpoint,CampaignBudget} from './chemistry_checkpoint.mjs';
import {pointwise} from './chemistry_pointwise.mjs';

const args=process.argv.slice(2),arg=(n,d)=>{const i=args.indexOf(n);return i<0?d:args[i+1];};
const out=resolve(arg('--output','artifacts/gpu-v14/forensics'));
const wallMs=Number(arg('--wall-ms',180000)),stopTime=Number(arg('--stop-time',.0012));
const analyzeOnly=args.includes('--analyze-only');
const scheduleOnly=args.includes('--replay-schedule');
const pointwiseOnly=args.includes('--pointwise-only');
const reportOnly=args.includes('--report-only');
const refinement=Number(arg('--refinement',1));if(![1,2,4,8,16].includes(refinement))throw Error('Invalid reference refinement');
if(!(wallMs>0&&wallMs<=600000&&Number.isFinite(stopTime)&&stopTime>0))throw Error('Forensics allows at most 10 minutes per invocation');
mkdirSync(out,{recursive:true});
if(existsSync(resolve(out,'run.json'))&&!analyzeOnly&&!scheduleOnly&&!pointwiseOnly&&!reportOnly)throw Error('Use a new output directory to preserve previous evidence');
const budgetPath=resolve('artifacts/gpu-v14/chemistry-budget.json'),lock=budgetPath+'.lock';
const saved=readCheckpoint(budgetPath);
if(saved.limitMs!==8*3600000)throw Error('Unexpected existing campaign limit');
if(existsSync(lock)){
 const pid=Number(readFileSync(lock,'utf8'));
 if(!Number.isInteger(pid)||pid<1)throw Error('Unrecognized chemistry lock owner');
 try{process.kill(pid,0);throw Error('Another campaign owns the chemistry budget');}
 catch(e){if(e.code!=='ESRCH')throw e;unlinkSync(lock);}
}
const fd=openSync(lock,'wx');writeFileSync(fd,String(process.pid));closeSync(fd);
const budget=new CampaignBudget(saved,saved.limitMs),python=resolve('tools/chemistry-venv/Scripts/python.exe');
const sourceFiles=['src/gpu/chemistry/Gri30.ts','src/gpu/chemistry/ImplicitTile.ts','src/gpu/chemistry/ChemistryCheckpoint.ts','src/gpu/chemistry/GpuImplicitTile.ts','src/gpu/chemistry/ChemistryTrace.ts','src/gpu/chemistry/CompensatedState.ts','src/gpu/chemistry/AccurateEnthalpy.ts','src/gpu/chemistry/TileShaders.ts','src/gpu/chemistry/kinetics.wgsl','src/gpu/chemistry/enthalpy.wgsl','src/gpu/chemistry/data/mechanism.json','src/gpu/chemistry/data/gri30.yaml','src/gpu/chemistry/data/provenance.json','tests/gpu/reactor-fixtures.json','requirements-chemistry.txt','scripts/chemistry_forensics.py','scripts/chemistry_forensics.mjs','scripts/chemistry_schedule_reference.py','scripts/chemistry_ignition_reference.py','scripts/chemistry_pointwise.mjs','scripts/report_chemistry_forensics.py'];
const sourceSha256=createHash('sha256').update(sourceFiles.map(f=>readFileSync(f,'utf8').replaceAll('\r\n','\n')).join('\n')).digest('hex');
let browser,server,page,result,hardware,adapter,error,prior,initial,gpuInitial,cancelled=false;
const chunks=[];
const save=(reserve=5000)=>atomicWrite(budgetPath,budget.snapshot(Math.min(reserve,budget.remaining())));
const timer=setInterval(()=>{save();if(budget.remaining()<5000||cancelled)page?.evaluate(()=>window.forensicAbort?.abort()).catch(()=>{});},1000);
process.on('SIGINT',()=>{cancelled=true;});process.on('SIGTERM',()=>{cancelled=true;});
try{
 if(budget.remaining()<(reportOnly?5000:analyzeOnly||pointwiseOnly||scheduleOnly?10000:wallMs+10000))throw Error('Insufficient remaining budget for this diagnostic request');
 if(reportOnly){
  const repairs=args.flatMap((v,i)=>v==='--repair'?['--repair',resolve(args[i+1])]:[]);
  save(Math.min(60000,budget.remaining()));
  const r=spawnSync(python,['scripts/report_chemistry_forensics.py',out,resolve(arg('--report-output','docs/chemistry-forensics-1.4.json')),...repairs],{encoding:'utf8',timeout:Math.max(1,Math.min(60000,budget.remaining()-1000)),maxBuffer:1024*1024});
  if(r.status!==0)throw Error(r.stderr);console.log(r.stdout.trim());
 }
 else if(pointwiseOnly){await pointwise(out,python,save);}
 else if(scheduleOnly){
  save(Math.min(610000,budget.remaining()));
  const audit=spawnSync(python,['scripts/chemistry_schedule_reference.py',resolve(out,'chemistry-divergence.json'),resolve(out,`chemistry-schedule-r${refinement}.json`),'--refinement',String(refinement),'--wall-seconds','590'],{encoding:'utf8',timeout:Math.max(1,Math.min(610000,budget.remaining()-5000)),maxBuffer:1024*1024});
  if(audit.status!==0)throw Error('Prescribed schedule audit: '+audit.stderr);
  console.log(audit.stdout.trim());
 }else{
 if(analyzeOnly){
  prior=readCheckpoint(resolve(out,'run.json'));adapter=prior.adapter;hardware=prior.hardware;
  chunks.push(...prior.chunks);
  initial=readCheckpoint(resolve(out,'checkpoint.json')).checkpoint.initial[0];
  const first=readCheckpoint(resolve(out,chunks[0])).records[0];
  if(first.control[19]!==0)throw Error('Initial uploaded state is unavailable');
  gpuInitial=first.state;
 }else{
 save(30000);
 const hw=spawnSync(python,['scripts/gpu_hardware.py'],{encoding:'utf8',timeout:30000});
 if(hw.status!==0)throw Error(hw.stderr);hardware=JSON.parse(hw.stdout);
 server=await createServer({mode:'gputest',server:{host:'127.0.0.1',port:5177,strictPort:true,hmr:false}});await server.listen();
 browser=await chromium.launch({channel:'msedge',headless:true,args:['--use-angle=d3d11','--force-high-performance-gpu','--use-webgpu-power-preference=force-high-performance','--enable-webgpu-developer-features']});
 page=await browser.newPage();
 await page.exposeFunction('saveTrace',chunk=>{
  if(chunk.dropped)throw Error('Trace overflow; diagnostic is incomplete');
  const name=`trace-${chunks.length}.json`;atomicWrite(resolve(out,name),chunk);chunks.push(name);
 });
 await page.goto('http://127.0.0.1:5177/tests/gpu/harness.html');await page.waitForFunction(()=>!!window.lab);
 adapter=await page.evaluate(async()=>{
  const a=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});
  if(!a)throw Error('WebGPU unavailable');
  const d=await a.requestDevice({requiredFeatures:a.features.has('timestamp-query')?['timestamp-query']:[],requiredLimits:{maxStorageBuffersPerShaderStage:8}});
  window.chem=new window.lab.Gri30(d);window.chemDevice=d;
  return {vendor:a.info.vendor,device:a.info.device,architecture:a.info.architecture};
 });
 if(adapter.vendor!=='nvidia'||adapter.device!=='0x28a1'||!hardware.adapters.some(a=>a.vendor==='0x10de'&&a.device===adapter.device))throw Error('RTX 4050 not confirmed');
 save();
 result=await page.evaluate(async({wallMs,stopTime})=>{
  const f=window.lab.reactorFixtures.cases[8];window.forensicAbort=new AbortController();
  const r=await window.chem.integrate([f.initial],f.horizon,window.forensicAbort.signal,{
   implementation:'gpu',maxWallMs:wallMs,maxAttempts:16777216,traceCapacity:2048,
   sampleTimes:f.points.map(p=>p.time),onTrace:chunk=>window.saveTrace(chunk),
   onProgress:p=>{if(p.time>=stopTime)window.forensicAbort.abort();}
  });
  // Chunks have already been durably streamed; do not duplicate the tail.
  return {...r,trace:undefined,initial:f.initial};
 },{wallMs,stopTime});
 atomicWrite(resolve(out,'checkpoint.json'),{caseIds:[8],checkpoint:result.checkpoint});
 initial=result.initial;gpuInitial=result.gpuInitial;
 }
 const input={initial,gpuInitial,traceFiles:chunks.map(f=>({path:resolve(out,f),sha256:createHash('sha256').update(readFileSync(resolve(out,f))).digest('hex')}))};
 writeFileSync(resolve(out,'trace-input.json'),JSON.stringify(input));
 save(Math.min(120000,budget.remaining()));
 const audit=spawnSync(python,['scripts/chemistry_forensics.py',resolve(out,'trace-input.json'),resolve(out,'chemistry-divergence.json')],{encoding:'utf8',timeout:Math.max(1,Math.min(120000,budget.remaining()-5000)),maxBuffer:8*1024*1024});
 if(audit.status!==0)throw Error('Independent BE audit: '+audit.stderr);
 console.log(audit.stdout.trim());
 }
}catch(e){error=String(e);console.error(error);process.exitCode=2;}
finally{
 clearInterval(timer);await page?.close().catch(()=>{});await browser?.close().catch(()=>{});await server?.close();
 atomicWrite(resolve(out,reportOnly?'report-run.json':pointwiseOnly?'pointwise-run.json':scheduleOnly?`schedule-r${refinement}-run.json`:analyzeOnly?'analysis-run.json':'run.json'),{sourceSha256,sourceFiles,adapter,hardware,error:error??null,chunks,stopTime,
  gpuSourceSha256:prior?.sourceSha256??(scheduleOnly||reportOnly?undefined:sourceSha256),
  result:result?{profile:result.profile,diagnostics:result.diagnostics,stopReason:result.stopReason}:null,
  historicalAcceptanceStatus:'FAIL',budget:budget.snapshot()});
 atomicWrite(budgetPath,budget.snapshot());unlinkSync(lock);
}
