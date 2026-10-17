// Sequential native RTX campaign. No CPU chemistry fallback, no skipped cells.
import {createHash,randomUUID} from 'node:crypto';
import {chromium} from '@playwright/test';
import {createServer} from 'vite';
import {readFileSync,existsSync,mkdirSync,writeFileSync,openSync,closeSync,unlinkSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';
import {atomicWrite,readCheckpoint,CampaignBudget} from './chemistry_checkpoint.mjs';

const args=process.argv.slice(2),arg=(name,fallback)=>{const i=args.indexOf(name);return i<0?fallback:args[i+1];};
const out=resolve(arg('--output','artifacts/gpu-v14/campaign'));
const limit=Number(arg('--budget-ms',8*3600000));
if(!(limit>0 && limit<=8*3600000))throw Error('Campaign budget must be in (0, 8h]');
const linearSolver=arg('--linear-solver','lu');if(!['lu','refined-lu'].includes(linearSolver))throw Error('Invalid linear solver');
const python=resolve('tools/chemistry-venv/Scripts/python.exe');
const caseOrder=[8,0,7,9,4,5,6,1,2,3];
const fixtures=JSON.parse(readFileSync('tests/gpu/reactor-fixtures.json','utf8')).cases;
const provenance=JSON.parse(readFileSync('src/gpu/chemistry/data/provenance.json','utf8'));
const budgetPath=resolve(arg('--budget-file','artifacts/gpu-v14/chemistry-budget.json'));mkdirSync(resolve(budgetPath,'..'),{recursive:true});
const lockPath=budgetPath+'.lock';
if(existsSync(lockPath)){const pid=Number(readFileSync(lockPath,'utf8'));let live=true;try{process.kill(pid,0);}catch{live=false;}if(live)throw Error('Another chemistry campaign owns this budget');unlinkSync(lockPath);}
const lockFd=openSync(lockPath,'wx');writeFileSync(lockFd,String(process.pid));closeSync(lockFd);
const sourceSha256=createHash('sha256').update(['src/gpu/chemistry/Gri30.ts','src/gpu/chemistry/ChemistryBatch.ts','src/gpu/chemistry/GpuImplicitTile.ts','src/gpu/chemistry/TileShaders.ts','src/gpu/chemistry/ImplicitTile.ts','src/gpu/chemistry/ChemistryCheckpoint.ts','src/gpu/chemistry/LinearPrecisionProbe.ts','scripts/inspect_chemistry_lu.py','scripts/chemistry_checkpoint.mjs','tests/gpu/reactor-fixtures.json','src/gpu/chemistry/data/mechanism.json','requirements-chemistry.txt','src/gpu/chemistry/kinetics.wgsl','src/gpu/chemistry/enthalpy.wgsl','scripts/chemistry_campaign.mjs','scripts/validate_gpu_chemistry.py'].map(p=>readFileSync(p,'utf8').replaceAll('\r\n','\n')).join('\n')).digest('hex');
const checkpointPath=resolve(out,'campaign.checkpoint.json');mkdirSync(out,{recursive:true});
let saved=existsSync(checkpointPath)?readCheckpoint(checkpointPath):null;
if(saved && (saved.mechanismSha256!==provenance.sha256 || saved.version!=='gri30-gpu-state-machine-2' || saved.budget.limitMs!==limit || saved.linearSolver!==linearSolver || saved.sourceSha256!==sourceSha256))throw Error('Campaign identity mismatch');
const ledger=existsSync(budgetPath)?readCheckpoint(budgetPath):saved?.budget;if(ledger&&ledger.limitMs!==limit)throw Error('Budget limit mismatch');
const budget=new CampaignBudget(ledger,limit);
let cancelled=false;process.on('SIGINT',()=>cancelled=true);process.on('SIGTERM',()=>cancelled=true);
const state=saved??{version:'gri30-gpu-state-machine-2',mechanismSha256:provenance.sha256,sourceSha256,linearSolver,stage:'0d',scale:1,tile:0,caseIndex:0,results:[],validated:[],statuses:{kinetics:'INCOMPLETE',reactors:'INCOMPLETE',1:'INCOMPLETE',512:'INCOMPLETE',4096:'INCOMPLETE',65536:'INCOMPLETE'},budget:null};
function save(reserve=0){state.budget=budget.snapshot(Math.min(reserve,budget.remaining()));atomicWrite(budgetPath,state.budget);atomicWrite(checkpointPath,state);}
function report(){
  const overall=Object.values(state.statuses).includes('FAIL')?'FAIL':Object.values(state.statuses).every(x=>x==='PASS')?'PASS':'INCOMPLETE';
  atomicWrite(resolve(out,'chemistry-campaign.json'),{version:state.version,mechanismSha256:provenance.sha256,sourceSha256,status:overall,criteria:state.statuses,budget:budget.snapshot(),adapter:state.adapter,hardware:state.hardware,linearSolver,pointwise:state.pointwise,precisionProbes:state.precisionProbes??[],failure:state.failure??null,results:state.results,error:state.error??null});
  atomicWrite(resolve(out,'chemistry-profile.json'),{units:{wall:'ms',gpu:'ms'},profiles:state.results.map(x=>({id:x.id,profile:x.profile,rejections:x.rejections}))});
  atomicWrite(resolve(out,'chemistry-scale.json'),{status:overall,scales:[1,512,4096,65536].map(n=>({reactors:n,status:state.statuses[n]})),measurements:state.results.filter(x=>x.stage==='scale')});
  atomicWrite(resolve(out,'reactor-validation.json'),{status:state.statuses.reactors,validated:state.validated});
  state.overall=overall;
  console.log(JSON.stringify({status:overall,criteria:state.statuses,usedMs:budget.elapsed(),output:out}));
}
let server,browser,page;const cancelPoll=setInterval(()=>{try{atomicWrite(budgetPath,budget.snapshot(Math.min(5000,budget.remaining())));}catch(error){state.error='Budget heartbeat failed: '+String(error);cancelled=true;}if(cancelled||existsSync(resolve(out,'cancel'))||budget.remaining()<5000){cancelled=true;page?.evaluate(()=>window.campaignAbort?.abort()).catch(()=>{});}},1000);
try{
  if(budget.remaining()<10000)throw Error('Campaign budget exhausted before GPU startup');
  save(Math.min(60000,budget.remaining()));
  server=await createServer({mode:'gputest',server:{host:'127.0.0.1',port:5176,strictPort:true,hmr:false}});await server.listen();
  browser=await chromium.launch({channel:'msedge',headless:true,args:['--use-angle=d3d11','--force-high-performance-gpu','--use-webgpu-power-preference=force-high-performance','--enable-webgpu-developer-features']});
  page=await browser.newPage();page.on('console',m=>{if(m.type()==='error')console.error(m.text());});
  await page.goto('http://127.0.0.1:5176/tests/gpu/harness.html');await page.waitForFunction(()=>!!window.lab);
  const adapter=await page.evaluate(async()=>{
    const a=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});if(!a)throw Error('WebGPU unavailable');
    const d=await a.requestDevice({requiredFeatures:a.features.has('timestamp-query')?['timestamp-query']:[],requiredLimits:{maxStorageBuffersPerShaderStage:8}});
    window.chem=new window.lab.Gri30(d);window.chemDevice=d;
    return {vendor:a.info.vendor,architecture:a.info.architecture,device:a.info.device,description:a.info.description};
  });state.adapter=adapter;
  save(Math.min(30000,budget.remaining()));
  const hw=spawnSync(python,['scripts/gpu_hardware.py'],{encoding:'utf8',timeout:30000});
  if(hw.status!==0)throw Error('DXGI verification failed: '+hw.stderr);
  state.hardware=JSON.parse(hw.stdout);
  if(adapter.vendor!=='nvidia' || adapter.device!=='0x28a1' || !state.hardware.adapters.some(a=>a.vendor==='0x10de'&&a.device===adapter.device))throw Error('RTX 4050 adapter is not confirmed');
  save(30000);
  // Pointwise RHS/Jacobian gate is measured afresh on this device.
  if(state.statuses.kinetics!=='PASS'){
    const point=await page.evaluate(async()=>{
      const fixtures=window.lab.chemistryFixtures,values=await window.chem.evaluate(fixtures.map(f=>f.state));
      return {values,fixtures};
    });
    let rhsError=0,jacError=0;
    for(let cell=0;cell<point.fixtures.length;cell++){
      const f=point.fixtures[cell];
      for(let row=0;row<54;row++){
        const ref=f.jacobian.slice(row*54,(row+1)*54),rowMax=Math.max(...ref.map(Math.abs));
        rhsError=Math.max(rhsError,Math.abs(point.values[cell*2970+row*55+54]-f.rhs[row])/Math.max(Math.abs(f.rhs[row]),1e-8));
        for(let col=0;col<54;col++)jacError=Math.max(jacError,Math.abs(point.values[cell*2970+row*55+col]-ref[col])/Math.max(Math.abs(ref[col]),rowMax*1e-6,1e-8));
      }
    }
    state.statuses.kinetics=rhsError<=.001&&jacError<=.001?'PASS':'FAIL';state.pointwise={rhsError,jacError};save();
  }
  while(!cancelled && !existsSync(resolve(out,'cancel')) && budget.remaining()>10000 && !Object.values(state.statuses).includes('FAIL')){
    const scaling=state.stage==='scale';
    const size=scaling?state.scale:fixtures.length;
    const start=scaling?state.tile*256:0;
    if(start>=size){
      state.statuses[state.scale]='PASS';const next={1:512,512:4096,4096:65536}[state.scale];
      if(!next)break;state.scale=next;state.tile=0;state.caseIndex=0;save();continue;
    }
    // Group by horizon/sample schedule while retaining every global reactor ID.
    // Tile IDs are fixed; different case groups receive independent GPU steps.
    const caseId=caseOrder[state.caseIndex];
    const ids=Array.from({length:Math.min(256,size-start)},(_,i)=>start+i).filter(i=>caseOrder[i%fixtures.length]===caseId);
    const f=fixtures[caseId];
    const id=`${state.stage}-${state.scale}-${state.tile}-${caseId}-${state.refinement??0}`;
    const tilePath=resolve(out,id+'.checkpoint.json');
    const sliceId=id+'-'+randomUUID(),inspectionPath=resolve(out,sliceId+'.inspection.json');
    if(!ids.length){state.caseIndex++;if(state.caseIndex===fixtures.length){state.caseIndex=0;state.tile++;}continue;}
    const baseSamples=f.points.map(p=>p.time);
    const sampleTimes=state.refinementSamples??baseSamples;
    const old=existsSync(tilePath)?readCheckpoint(tilePath):null;
    const wallMs=Math.min(30000,Math.max(1,budget.remaining()-5000));save(wallMs+5000);
    const result=await page.evaluate(async({caseId,count,horizon,sampleTimes,wallMs,checkpoint,linearSolver})=>{
      const f=window.lab.reactorFixtures.cases[caseId];window.campaignAbort=new AbortController();
      return await window.chem.integrate(Array.from({length:count},()=>f.initial),horizon,window.campaignAbort.signal,
        {implementation:'gpu',linearSolver,sampleTimes,maxWallMs:wallMs,maxAttempts:16777216,checkpoint,inspection:true});
    },{caseId,count:ids.length,horizon:f.horizon,sampleTimes,wallMs,checkpoint:old?.checkpoint,linearSolver});
    atomicWrite(tilePath,{caseIds:ids.map(()=>caseId),reactorIds:ids,checkpoint:result.checkpoint});
    writeFileSync(inspectionPath,JSON.stringify(result.inspection));
    let linearVerified=false;
    try{
    const luPath=resolve(out,sliceId+'.lu.json');
    save(Math.min(60000,budget.remaining()));
    const luCheck=spawnSync(python,['scripts/inspect_chemistry_lu.py',inspectionPath,luPath],{encoding:'utf8',timeout:Math.max(1,Math.min(60000,budget.remaining()-1000))});
    if(luCheck.status!==0)throw Error('LU inspection failed: '+luCheck.stderr);
    const inspected=JSON.parse(readFileSync(luPath,'utf8'));
    linearVerified=inspected.reports.length===Math.min(ids.length,4) && inspected.reports.every(r=>r.gpuLuFailed || !r.linearSolveRequired || (Number.isFinite(r.independentBackwardError) && r.independentBackwardError<=1e-5));
    const precision=await page.evaluate(async(systems)=>{
      const l=window.lab,d=window.chemDevice;
      return {single:await l.probeLinearPrecision(d,systems,54,'float32'),extended:await l.probeLinearPrecision(d,systems,54,'double-single')};
    },inspected.systems);
    state.precisionProbes??=[];state.precisionProbes.push({id,sliceId,inspection:luPath,reports:inspected.reports,...precision});
    }catch(error){state.precisionProbes??=[];state.precisionProbes.push({id,sliceId,error:String(error),status:'INCOMPLETE'});}
    const validationPath=resolve(out,sliceId+'.validation.json'),inputPath=resolve(out,sliceId+'.input.json');
    writeFileSync(inputPath,JSON.stringify({caseIds:ids.map(()=>caseId),checkpoint:result.checkpoint}));
    save(Math.min(60000,budget.remaining()));
    const check=spawnSync(python,['scripts/validate_gpu_chemistry.py',inputPath,validationPath],{encoding:'utf8',timeout:Math.max(1,Math.min(60000,budget.remaining()-1000))});
    if(check.status!==0)throw Error('Independent validation failed to execute: '+check.stderr);
    const validation=JSON.parse(readFileSync(validationPath,'utf8'));
    state.results.push({id,sliceId,inspectionPath,validationPath,stage:state.stage,reactorIds:ids,profile:result.profile,stopReason:result.stopReason,rejections:result.diagnostics.rejections,physicalTime:result.diagnostics.time,validation:validation.status});
    if(validation.status==='FAIL'){
      // Independent re-evaluation confirms numerical discrepancies; resource
      // failures or incomplete horizons never become a numerical FAIL here.
      save(Math.min(60000,budget.remaining()));
      const confirm=spawnSync(python,['scripts/validate_gpu_chemistry.py',inputPath,validationPath+'.confirmation.json'],{encoding:'utf8',timeout:Math.max(1,Math.min(60000,budget.remaining()-1000))});
      if(confirm.status!==0 || JSON.parse(readFileSync(validationPath+'.confirmation.json','utf8')).status!=='FAIL')throw Error('Numerical mismatch could not be confirmed');
      state.statuses[scaling?state.scale:'reactors']='FAIL';state.failure={id,validationPath,stopReason:result.stopReason};save();break;
    }
    if(!['completed','wall-limit','cancelled'].includes(result.stopReason)){state.error='Integrator stopped: '+result.stopReason;save();break;}
    console.log(JSON.stringify({id,time:result.diagnostics.time,horizon:f.horizon,rejected:result.diagnostics.rejected,wallMs:result.profile.wallMs,remainingMs:budget.remaining()}));
    if(result.stopReason==='completed'){
      if(!linearVerified)throw Error('Independent LU acceptance was not established; cannot promote this result');
      if(!scaling && !f.ignitionCensored){
        const current=validation.reactors[0],prior=state.refinementBaseline;
        const stable=prior && Math.abs(current.ignitionTime-prior.ignitionTime)/Math.max(1e-30,prior.ignitionTime)<.01 && Math.abs(current.OHPeak-prior.OHPeak)/Math.max(1e-12,prior.OHPeak)<.01;
        if(!stable){
          const samples=current.samples,peak=current.OHPeak;
          const refined=new Set(sampleTimes);
          for(let i=1;i<samples.length;i++)if((samples[i].state[0]>=f.T+200&&samples[i-1].state[0]<=f.T+800)||samples[i].OH>=peak*.5||samples[i-1].OH>=peak*.5)refined.add((samples[i-1].time+samples[i].time)/2);
          state.refinement=(state.refinement??0)+1;if(state.refinement>3){state.error='Sampling did not converge within three refinements';save();break;}
          state.refinementBaseline={ignitionTime:current.ignitionTime,OHPeak:current.OHPeak};state.refinementSamples=[...refined].sort((a,b)=>a-b);save();continue;
        }
      }
      state.validated.push({id,validationPath,samplingConverged:!scaling});state.refinement=0;delete state.refinementBaseline;delete state.refinementSamples;
      state.caseIndex++;
      if(state.caseIndex===fixtures.length){
        state.caseIndex=0;
        if(!scaling){state.statuses.reactors='PASS';state.stage='scale';state.scale=1;state.tile=0;}
        else state.tile++;
      }
    }
    save();report();
  }
}catch(error){state.error=String(error);console.error(error);}
finally{
  clearInterval(cancelPoll);
  if(page)await page.close().catch(()=>{});if(browser)await browser.close().catch(()=>{});if(server)await server.close();
  save();report();atomicWrite(budgetPath,budget.snapshot());unlinkSync(lockPath);process.exitCode=state.overall==='PASS'?0:state.overall==='FAIL'?1:2;
}
