/// <reference types="@webgpu/types" />
import {tileJacobian, tileLu, tileRefinedLu, tileController, tileApply, tileSummary} from './TileShaders';
import {CHEMISTRY_VERSION, CONTROL_STRIDE, TOLERANCES, validateCheckpoint, reactorProgress, type TileCheckpoint} from './ChemistryCheckpoint';
import type {IntegrationOptions} from './ImplicitTile';
import {TRACE_STRIDE,traceShader,decodeTrace} from './ChemistryTrace';
import {compensatedSources} from './CompensatedState';
import {accurateEnthalpy} from './AccurateEnthalpy';

export const REJECTION_REASONS = ['estimator','newton','damping','lu','positivity','thermodynamics','enthalpy','step-underflow','attempt-limit'] as const;
type Stage = 'jacobian'|'lu'|'controller'|'update'|'summary'|'inspection'|'enthalpy';

export class GpuImplicitTile {
  private pipelines = new Map<Stage,GPUComputePipeline>();
  private resources?: {key:string; buffers:GPUBuffer[]};
  private busy=false;private linearSolver='lu';private tracing=false;private precision='float32';
  constructor(readonly device:GPUDevice, readonly mechanism:GPUBuffer, readonly mechanismSha256:string,readonly mechanismLow:GPUBuffer) {}
  dispose(){if(this.busy)throw Error('Cannot dispose active chemistry');this.resources?.buffers.forEach(b=>b.destroy());this.resources=undefined;}

  async integrate(initial:number[][], duration:number, signal?:AbortSignal, options:IntegrationOptions={}) {
    const invocationStart=performance.now();
    if(this.busy)throw Error('Chemical tile is already active');
    options={...options,sampleTimes:options.sampleTimes?.slice(),checkpoint:options.checkpoint?structuredClone(options.checkpoint):undefined};initial=initial.map(s=>s.slice());
    if(!initial.length || initial.length>256 || !(duration>0) || !Number.isFinite(duration) ||
      initial.some(s=>s.length!==54 || s.some(x=>!Number.isFinite(x)) || s[0]<300 || s[0]>3000 ||
        s.slice(1).some(x=>x<0) || Math.abs(s.slice(1).reduce((a,b)=>a+b,0)-1)>1e-6))throw Error('Invalid chemical tile');
    const maxWallMs=options.maxWallMs??60000,maxAttempts=options.maxAttempts??65536;
    const traceCapacity=options.traceCapacity??0;
    const localErrorTarget=Math.fround(options.localErrorTarget??1);
    const precision=options.precision??'float32',compensated=precision==='compensated-state';
    if(!['float32','compensated-state'].includes(precision))throw Error('Invalid precision');
    if(compensated&&traceCapacity)throw Error('Passive trace currently supports float32; inspect compensated checkpoints instead');
    if(!(localErrorTarget>0 && localErrorTarget<=1))throw Error('Local BE error target must be in (0, 1]');
    if(!Number.isInteger(traceCapacity) || traceCapacity<0 || traceCapacity>16384 || (traceCapacity && (initial.length!==1 || options.inspection)))throw Error('Trace requires one reactor, capacity 1–16384, and no LU inspection');
    if(options.onTrace && traceCapacity<12)throw Error('Streaming trace capacity must be at least 12');
    if(!(maxWallMs>0) || !Number.isFinite(maxWallMs) || !Number.isInteger(maxAttempts) || maxAttempts<1 || maxAttempts>16777216)throw Error('Invalid chemistry budget');
    const samples=[...(options.sampleTimes??[]),duration].filter((t,i,a)=>i===a.indexOf(t));
    if(samples.some((t,i)=>!(t>0) || !Number.isFinite(t) || t>duration || (i>0 && !(Math.fround(t)>Math.fround(samples[i-1])))))throw Error('Invalid chemistry sample times');
    const linearSolver=options.linearSolver??'lu';if(!['lu','refined-lu'].includes(linearSolver))throw Error('Invalid linear solver');
    if(options.checkpoint)validateCheckpoint(options.checkpoint,initial,duration,samples,this.mechanismSha256,linearSolver,localErrorTarget,precision);
    if(this.precision!==precision){for(const name of ['jacobian','lu','controller','update','inspection'] as Stage[])this.pipelines.delete(name);this.precision=precision;}
    if(this.linearSolver!==linearSolver){this.pipelines.delete('lu');this.linearSolver=linearSolver;}
    if(this.tracing!==Boolean(traceCapacity)){this.pipelines.delete('inspection');this.tracing=Boolean(traceCapacity);}
    this.busy=true;
    const start=invocationStart,d=this.device,n=initial.length,bytes=n*54*4;
    const timestamp=d.features.has('timestamp-query');
    const profile={units:{wall:'ms',gpu:'ms',readback:'bytes'},compilationMs:0,allocationMs:0,submitCpuMs:0,mapWaitMs:0,
      readbackBytes:0,submissions:0,dispatches:0,statusReads:0,gpuMs:timestamp?{} as Record<Stage,number>:null,
      gpuTimingSource:timestamp?'timestamp-query':'unavailable',wallMs:0};
      const sources:Record<Stage,string>={enthalpy:accurateEnthalpy,jacobian:tileJacobian,lu:linearSolver==='refined-lu'?tileRefinedLu:tileLu,controller:tileController,update:tileApply,summary:tileSummary,inspection:`
@group(0) @binding(0) var<storage,read> states:array<f32>;
@group(0) @binding(1) var<storage,read> work:array<f32>;
@group(0) @binding(2) var<storage,read> jac:array<f32>;
@group(0) @binding(3) var<storage,read> status:array<f32>;
@group(0) @binding(4) var<storage,read> control:array<f32>;
@group(0) @binding(5) var<storage,read_write> snapshot:array<f32>;
@compute @workgroup_size(64) fn main(@builtin(workgroup_id) g:vec3u,@builtin(local_invocation_index) lane:u32){
 let cell=g.x;let c=cell*40u;let b=cell*3342u;
 if(control[c+8u]!=1. || control[c+19u]!=1.){return;}
 for(var i=lane;i<2970u;i+=64u){snapshot[b+i]=jac[cell*2970u+i];}
 if(lane<54u){snapshot[b+2970u+lane]=states[cell*54u+lane];}
 for(var i=lane;i<270u;i+=64u){snapshot[b+3024u+i]=work[cell*270u+i];}
 if(lane<40u){snapshot[b+3294u+lane]=control[c+lane];}
 if(lane<8u){snapshot[b+3334u+lane]=status[cell*8u+lane];}
}`};
    let query:GPUQuerySet|undefined;
    try{
      if(traceCapacity)sources.inspection=traceShader;
      if(compensated){
        // Each damping trial needs its own Jacobian for J(high)*low. No reuse
        // of a matrix from a previous trial or approximate Newton promotion.
        const branch=sources.jacobian.indexOf(' if(phase==3.){');
        const resume=sources.jacobian.indexOf(' let f=evaluate(cell,i32(lane));');
        if(branch<0||resume<branch)throw Error('Jacobian template changed');
        sources.jacobian=sources.jacobian.slice(0,branch)+sources.jacobian.slice(resume);
        Object.assign(sources,compensatedSources(linearSolver==='refined-lu'));
        sources.inspection=sources.inspection.replace('let b=cell*3342u;', 'let b=cell*3670u;')
          .replace('for(var i=lane;i<2970u;i+=64u)', 'for(var i=lane;i<328u;i+=64u){snapshot[b+3342u+i]=low[cell*328u+i];}for(var i=lane;i<2970u;i+=64u)')
          +'\n@group(0) @binding(6) var<storage,read> low:array<f32>;';
      }
      for(const name of Object.keys(sources) as Stage[])if(!this.pipelines.has(name)){
        const t=performance.now(),module=d.createShaderModule({code:sources[name],label:`GRI30 ${name}`});
        const info=await module.getCompilationInfo(),errors=info.messages.filter(m=>m.type==='error');
        if(errors.length)throw Error(`${name}: ${errors.map(m=>`${m.lineNum}: ${m.message}`).join('\n')}`);
        this.pipelines.set(name,await d.createComputePipelineAsync({layout:'auto',compute:{module,entryPoint:'main'}}));profile.compilationMs+=performance.now()-t;
      }
      const sizes=[bytes,n*270*4,n*2970*4,n*8*4,n*CONTROL_STRIDE*4,(4+samples.length)*4,Math.max(4,n*samples.length*54*4*(compensated?2:1)),64,576,512,traceCapacity?(4+traceCapacity*TRACE_STRIDE)*4:Math.min(n,4)*(compensated?3670:3342)*4,compensated?n*328*4:4];
      if(sizes.slice(0,8).some(s=>s>d.limits.maxStorageBufferBindingSize || s>d.limits.maxBufferSize))throw Error('Chemical tile exceeds adapter buffer limits');
      const alloc=performance.now(),key=sizes.join(',');
      if(this.resources?.key!==key){
        this.resources?.buffers.forEach(b=>b.destroy());this.resources=undefined;
        const buffers:GPUBuffer[]=[];
        try{for(let i=0;i<sizes.length;i++)buffers.push(d.createBuffer({size:sizes[i],usage:i===8?GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ:i===9?GPUBufferUsage.QUERY_RESOLVE|GPUBufferUsage.COPY_SRC:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC|GPUBufferUsage.COPY_DST}));}
        catch(e){buffers.forEach(b=>b.destroy());throw e;}
        this.resources={key,buffers};
      }
      const [states,work,jac,status,control,schedule,trajectory,summary,staging,resolve,inspectionBuffer,low]=this.resources.buffers;
      const lowValues=new Float32Array(compensated?n*328:1);
      const controls=new Float32Array(n*CONTROL_STRIDE),scratch=new Float32Array(n*270),flat=new Float32Array(initial.flat());
      for(let cell=0;cell<n;cell++){
        const c=cell*CONTROL_STRIDE;controls[c+1]=Math.min(1e-6,samples[0]);controls[c+2]=controls[c+1];controls[c+8]=1;controls[c+12]=1;controls[c+39]=localErrorTarget;
        scratch.set(flat.subarray(cell*54,(cell+1)*54),cell*270);scratch.set(flat.subarray(cell*54,(cell+1)*54),cell*270+54);
      }
      const cp=options.checkpoint;
      if(cp){
        controls.set(cp.control);
        for(let cell=0;cell<n;cell++){
          const high=compensated?cp.acceptedHigh![cell]:cp.accepted[cell];
          flat.set(high,cell*54);scratch.set(high,cell*270);scratch.set(high,cell*270+54);
          if(compensated)for(const offset of [0,54,108])lowValues.set(cp.acceptedLow![cell],cell*328+offset);
          if(compensated)lowValues[cell*328+271]=cp.targetEnthalpyLow![cell];
          const c=cell*CONTROL_STRIDE;
          if(controls[c+8]!==5 && controls[c+8]!==6){controls[c+8]=1;controls[c+9]=0;controls[c+10]=0;controls[c+11]=0;controls[c+2]=Math.min(controls[c+1],Math.fround(samples[controls[c+20]])-controls[c]+controls[c+27]);}
        }
      }
      d.queue.writeBuffer(states,0,flat);d.queue.writeBuffer(work,0,scratch);d.queue.writeBuffer(control,0,controls);
      d.queue.writeBuffer(status,0,new Float32Array(n*8));
      d.queue.writeBuffer(low,0,lowValues);
      if(traceCapacity)d.queue.writeBuffer(inspectionBuffer,0,new Float32Array(4));
      d.queue.writeBuffer(schedule,0,new Float32Array([n,samples.length,maxAttempts,duration,...samples]));
      const historyLength=n*samples.length*54,history=new Float32Array(historyLength*(compensated?2:1));
      if(cp)for(let i=0;i<historyLength;i++){history[i]=cp.trajectory[i];if(compensated)history[historyLength+i]=cp.trajectory[i]-history[i];}
      d.queue.writeBuffer(trajectory,0,history);
      const lowEntries:[number,GPUBuffer][]=compensated?[[7,low]]:[];
      const bind=(stage:Stage,entries:[number,GPUBuffer][])=>d.createBindGroup({layout:this.pipelines.get(stage)!.getBindGroupLayout(0),entries:entries.map(([binding,buffer])=>({binding,resource:{buffer}}))});
      const binds:Record<Stage,GPUBindGroup>={
        enthalpy:bind('enthalpy',[[0,this.mechanism],[1,this.mechanismLow],[2,states],[3,low],[4,jac],[5,control]]),
        jacobian:bind('jacobian',[[0,this.mechanism],[1,states],[2,jac],[3,control]]),
        lu:bind('lu',[[0,jac],[1,states],[2,work],[3,control],[5,status],...lowEntries]),
        controller:bind('controller',[[0,states],[1,work],[2,jac],[3,status],[4,control],[5,schedule],[6,trajectory],...lowEntries]),
        update:bind('update',[[0,states],[1,work],[4,control],...lowEntries]),
        summary:bind('summary',[[0,control],[1,summary],[2,schedule]]),
        inspection:bind('inspection',[[0,states],[1,work],[2,jac],[3,status],[4,control],[5,inspectionBuffer],...(compensated?[[6,low] as [number,GPUBuffer]]:[])])};
      if(timestamp)query=d.createQuerySet({type:'timestamp',count:64});
      profile.allocationMs=performance.now()-alloc;
      const submit=(encoder:GPUCommandEncoder)=>{const t=performance.now();d.queue.submit([encoder.finish()]);profile.submitCpuMs+=performance.now()-t;profile.submissions++;};
      let lastBatchMs=0,lastCheckpoint=performance.now(),stats=new Float32Array(16),stopReason='wall-limit',tracePending=0,traceOffset=0;
      const readBuffer=async(buffer:GPUBuffer,size:number)=>{
        const temp=d.createBuffer({size,usage:GPUBufferUsage.MAP_READ|GPUBufferUsage.COPY_DST});
        try{const e=d.createCommandEncoder();e.copyBufferToBuffer(buffer,0,temp,0,size);submit(e);
          const t=performance.now();await temp.mapAsync(GPUMapMode.READ);profile.mapWaitMs+=performance.now()-t;profile.readbackBytes+=size;
          const value=new Float32Array(temp.getMappedRange().slice(0));temp.unmap();return value;
        }finally{temp.destroy();}
      };
      const checkpoint=async():Promise<TileCheckpoint>=>{
        const ctl=await readBuffer(control,control.size),w=await readBuffer(work,work.size),tr=await readBuffer(trajectory,trajectory.size);
        const lo=compensated?await readBuffer(low,low.size):null;
        const acceptedHigh=Array.from({length:n},(_,i)=>Array.from(w.subarray(i*270,i*270+54)));
        const acceptedLow=compensated?Array.from({length:n},(_,i)=>Array.from(lo!.subarray(i*328+54,i*328+108))):undefined;
        return {schema:4,integrator:CHEMISTRY_VERSION,mechanismSha256:this.mechanismSha256,precision,linearSolver,localErrorTarget,tolerances:TOLERANCES,
          initial,accepted:acceptedHigh.map((s,i)=>s.map((v,j)=>v+(acceptedLow?.[i][j]??0))),acceptedHigh:compensated?acceptedHigh:undefined,acceptedLow,
          targetEnthalpyLow:compensated?Array.from({length:n},(_,i)=>lo![i*328+271]):undefined,
          control:Array.from(ctl),sampleTimes:samples,trajectory:Array.from(tr.subarray(0,historyLength),(v,i)=>v+(compensated?tr[historyLength+i]:0)),duration};
      };
      const flushTrace=async()=>{
        const chunk=decodeTrace(await readBuffer(inspectionBuffer,inspectionBuffer.size),traceCapacity);
        chunk.records.forEach(r=>r.sequence+=traceOffset);
        await options.onTrace?.(chunk);traceOffset+=chunk.total;tracePending=0;
        d.queue.writeBuffer(inspectionBuffer,0,new Float32Array(4));
      };
      const gpuInitial=traceCapacity?Array.from(await readBuffer(states,states.size)):null;
      while(true){
        if(signal?.aborted){stopReason='cancelled';break;}
        // Reserve measured execution plus checkpoint overhead before submitting.
        if(performance.now()-start+Math.max(1000,lastBatchMs*2)>=maxWallMs)break;
        const begin=performance.now(),encoder=d.createCommandEncoder(),stages:Stage[]=[];
        const dispatch=(name:Stage,count:number)=>{
          const index=stages.length*2;const pass=encoder.beginComputePass(query?{timestampWrites:{querySet:query,beginningOfPassWriteIndex:index,endOfPassWriteIndex:index+1}}:{});
          pass.setPipeline(this.pipelines.get(name)!);pass.setBindGroup(0,binds[name]);pass.dispatchWorkgroups(count);pass.end();stages.push(name);profile.dispatches++;
        };
        // At most 31 dispatches including diagnostic snapshots.
        for(let epoch=0;epoch<(compensated?5:options.inspection||traceCapacity?6:7);epoch++){dispatch('jacobian',n);if(compensated)dispatch('enthalpy',n);dispatch('lu',n);if(options.inspection||traceCapacity)dispatch('inspection',Math.min(n,4));dispatch('controller',n);dispatch('update',n);}
        dispatch('summary',1);encoder.copyBufferToBuffer(summary,0,staging,0,64);
        if(query){encoder.resolveQuerySet(query,0,stages.length*2,resolve,0);encoder.copyBufferToBuffer(resolve,0,staging,64,stages.length*16);}
        submit(encoder);
        const wait=performance.now();await staging.mapAsync(GPUMapMode.READ);profile.mapWaitMs+=performance.now()-wait;
        try{
          stats=new Float32Array(staging.getMappedRange(0,64).slice(0));
          if(query){const times=new BigUint64Array(staging.getMappedRange(64,stages.length*16).slice(0));stages.forEach((name,i)=>{profile.gpuMs![name]=(profile.gpuMs![name]??0)+Number(times[i*2+1]-times[i*2])/1e6;});}
        }finally{staging.unmap();}
        profile.statusReads++;profile.readbackBytes+=64+(query?stages.length*16:0);lastBatchMs=performance.now()-begin;
        if(traceCapacity)tracePending+=6;
        if(options.onTrace && tracePending+6>traceCapacity)await flushTrace();
        if(stats.some(x=>!Number.isFinite(x)))throw Error('Non-finite chemistry summary');
        options.onProgress?.({time:stats[0],dt:stats[4]+stats[5]===n?0:stats[14],attempts:stats[2],rejected:stats[3],wallMs:performance.now()-start});
        if(stats[5]>0){stopReason='reactor-failure';break;}
        if(stats[4]===n){stopReason='completed';break;}
        if(options.onCheckpoint && performance.now()-lastCheckpoint>=60000){await options.onCheckpoint(await checkpoint());lastCheckpoint=performance.now();}
      }
      const saved=await checkpoint();await options.onCheckpoint?.(saved);
      const reasons=Object.fromEntries(REJECTION_REASONS.map((name,r)=>[name,saved.control.reduce((a,x,i)=>a+(i%40===28+r?x:0),0)]));
      const accepted=saved.accepted.flat(),complete=saved.control.every((x,i)=>i%40!==8 || x===5);
      if(stopReason==='reactor-failure'){const failed=Array.from({length:n},(_,i)=>saved.control.slice(i*40,(i+1)*40)).find(p=>p[8]===6);stopReason=failed?.[15]===8?'step-underflow':failed?.[15]===9?'attempt-limit':'numerical-failure';}
      const diagnostics={time:Math.min(...Array.from({length:n},(_,i)=>saved.control[i*40]-saved.control[i*40+27])),attempts:saved.control.filter((_,i)=>i%40===12).reduce((a,b)=>a+b,0),
        rejected:saved.control.filter((_,i)=>i%40===13).reduce((a,b)=>a+b,0),newtonIterations:saved.control.filter((_,i)=>i%40===24).reduce((a,b)=>a+b,0),maxAcceptedLinearResidual:Math.max(...saved.control.filter((_,i)=>i%40===16)),
        maxAttemptedLinearResidual:Math.max(...saved.control.filter((_,i)=>i%40===17)),maxPivotRatio:Math.max(...saved.control.filter((_,i)=>i%40===18)),enthalpyFraction:Math.max(...saved.control.filter((_,i)=>i%40===7)),complete,rejections:reasons,pivotRatioOverflow:saved.control.some((x,i)=>i%40===38 && x>0),acceptedSteps:saved.control.filter((_,i)=>i%40===14).reduce((a,b)=>a+b,0),dampingEvaluations:saved.control.filter((_,i)=>i%40===25).reduce((a,b)=>a+b,0),maxAttemptedPositivityCorrection:Math.max(...saved.control.filter((_,i)=>i%40===37))};
      let inspection:unknown=null;
      if(options.inspection)inspection={description:'Exact snapshot immediately after LU, before controller/damping mutations.',stride:compensated?3670:3342,count:Math.min(n,4),layout:{jacobian:0,trial:2970,scratch:3024,control:3294,status:3334,low:compensated?3342:null,lowCount:compensated?328:0},values:Array.from(await readBuffer(inspectionBuffer,inspectionBuffer.size))};
      let trace=traceCapacity?decodeTrace(await readBuffer(inspectionBuffer,inspectionBuffer.size),traceCapacity):null;
      if(trace){trace.records.forEach(r=>r.sequence+=traceOffset);if(options.onTrace)await options.onTrace(trace);}
      profile.wallMs=performance.now()-start;
      return {states:accepted,diagnostics,stopReason:complete?'completed':stopReason,checkpoint:saved,profile,inspection,trace,gpuInitial,
        progress:Array.from({length:n},(_,i)=>reactorProgress(saved.control.slice(i*40,(i+1)*40))),trajectory:saved.trajectory,sampleTimes:samples,
        status:[diagnostics.time,diagnostics.attempts,diagnostics.rejected,diagnostics.newtonIterations,0,diagnostics.maxAcceptedLinearResidual,diagnostics.maxPivotRatio,0,diagnostics.enthalpyFraction,Number(complete)],
        maxAttemptedLinear:diagnostics.maxAttemptedLinearResidual,wallMs:profile.wallMs,workgroupBytes:linearSolver==='refined-lu'?13212:12780,
        allocatedBytes:this.resources!.buffers.reduce((sum,b)=>sum+b.size,0)+this.mechanism.size+this.mechanismLow.size,blocks:profile.statusReads};
    }finally{query?.destroy();this.busy=false;}
  }
}

