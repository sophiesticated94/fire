/// <reference types="@webgpu/types" />
import kinetics from './kinetics.wgsl?raw';
import enthalpy from './enthalpy.wgsl?raw';

// Kernels deliberately separate rate evaluation from cooperative LU. Dense AD
// private arrays never remain live across workgroup barriers in the LU shader.
export const referenceLu=`
@group(0) @binding(0) var<storage,read> jac:array<f32>;
@group(0) @binding(1) var<storage,read> states:array<f32>;
@group(0) @binding(2) var<storage,read> base:array<f32>;
@group(0) @binding(3) var<storage,read> hTarget:array<f32>;
@group(0) @binding(4) var<storage,read_write> delta:array<f32>;
@group(0) @binding(5) var<storage,read_write> status:array<f32>;
@group(0) @binding(6) var<storage,read> parameters:array<f32>;
var<workgroup> a:array<f32,2970>;
var<workgroup> scale:array<f32,54>;
var<workgroup> solution:array<f32,54>;
var<workgroup> errors:array<f32,54>;
var<workgroup> original:array<f32,54>;
var<workgroup> pivot:u32;var<workgroup> failed:u32;var<workgroup> norm:f32;
var<workgroup> bNorm:f32;var<workgroup> xNorm:f32;
var<workgroup> hScale:f32;var<workgroup> largest:f32;var<workgroup> smallest:f32;
@compute @workgroup_size(64) fn main(@builtin(workgroup_id) group:vec3u,@builtin(local_invocation_index) lane:u32){
 let cell=group.x;let jbase=cell*2970u;let offset=cell*54u;let state=cell*8u;let dt=parameters[0];
 if(lane<54u){scale[lane]=select(1e-12,1e-3,lane==0u)+1e-5*max(abs(states[offset+lane]),abs(base[offset+lane]));}
 if(lane==0u){failed=0u;largest=0.;smallest=1e30;}workgroupBarrier();
 if(lane==0u){hScale=max(1.,abs(jac[jbase])*scale[0]);}workgroupBarrier();
 if(lane<54u){let row=lane;let rowScale=select(scale[row],hScale,row==0u);var residual=states[offset+row]-base[offset+row]-dt*jac[jbase+row*55u+54u];if(row==0u){residual=jac[jbase+54u]-hTarget[cell];}
  original[row]=-residual/rowScale;
  for(var col=0u;col<54u;col++){var value=select(0.,1.,row==col)-dt*jac[jbase+row*55u+col];if(row==0u){value=jac[jbase+col];}a[row*55u+col]=value*scale[col]/rowScale;}a[row*55u+54u]=original[row];errors[row]=original[row]*original[row];
 }
 workgroupBarrier();if(lane==0u){norm=0.;bNorm=0.;for(var r=0u;r<54u;r++){norm+=errors[r];bNorm=max(bNorm,abs(original[r]));}norm=sqrt(norm/54.);status[state]=norm;}
 workgroupBarrier();
 if(workgroupUniformLoad(&norm)<=.1){if(lane<54u){delta[offset+lane]=0.;}if(lane==0u){status[state+1u]=0.;status[state+2u]=0.;}return;}
 for(var col=0u;col<54u;col++){
  if(lane==0u){pivot=col;var v=abs(a[col*55u+col]);for(var r=col+1u;r<54u;r++){if(abs(a[r*55u+col])>v){v=abs(a[r*55u+col]);pivot=r;}}if(!(v>1e-30)){failed=1u;}largest=max(largest,v);smallest=min(smallest,v);}
  workgroupBarrier();if(workgroupUniformLoad(&failed)>0u){if(lane==0u){status[state+1u]=1.;}return;}
  let picked=workgroupUniformLoad(&pivot);if(lane<55u){let old=a[col*55u+lane];a[col*55u+lane]=a[picked*55u+lane];a[picked*55u+lane]=old;}workgroupBarrier();
  if(lane>col&&lane<54u){let factor=a[lane*55u+col]/a[col*55u+col];for(var k=col+1u;k<55u;k++){a[lane*55u+k]-=factor*a[col*55u+k];}a[lane*55u+col]=factor;}workgroupBarrier();
 }
 if(lane==0u){for(var row=53i;row>=0i;row--){var v=a[u32(row)*55u+54u];for(var col=u32(row)+1u;col<54u;col++){v-=a[u32(row)*55u+col]*solution[col];}solution[u32(row)]=v/a[u32(row)*55u+u32(row)];}xNorm=0.;for(var r=0u;r<54u;r++){xNorm=max(xNorm,abs(solution[r]));}status[state+3u]=largest/smallest;}workgroupBarrier();
 if(lane<54u){let row=lane;let rowScale=select(scale[row],hScale,row==0u);var lhs=0.;var rowNorm=0.;for(var col=0u;col<54u;col++){var value=select(0.,1.,row==col)-dt*jac[jbase+row*55u+col];if(row==0u){value=jac[jbase+col];}let scaled=value*scale[col]/rowScale;lhs+=scaled*solution[col];rowNorm+=abs(scaled);}errors[row]=abs(lhs-original[row])/max(1e-30,rowNorm*xNorm+bNorm);delta[offset+row]=solution[row]*scale[row];}
 workgroupBarrier();if(lane==0u){var worst=0.;for(var r=0u;r<54u;r++){worst=max(worst,errors[r]);}status[state+2u]=worst;status[state+1u]=select(1.,0.,worst<=1e-5);}
}`;

const apply=`
@group(0) @binding(0) var<storage,read> previous:array<f32>;
@group(0) @binding(1) var<storage,read> delta:array<f32>;
@group(0) @binding(2) var<storage,read_write> states:array<f32>;
@group(0) @binding(3) var<storage,read> parameters:array<f32>;
@compute @workgroup_size(64) fn main(@builtin(workgroup_id) group:vec3u,@builtin(local_invocation_index) lane:u32){
 let offset=group.x*54u;var alpha=parameters[1];for(var j=1u;j<54u;j++){if(delta[offset+j]<0.&&previous[offset+j]+alpha*delta[offset+j] < -1e-12){alpha=min(alpha,.99*previous[offset+j]/(-delta[offset+j]));}}
 if(lane<54u){let value=previous[offset+lane]+alpha*delta[offset+lane];states[offset+lane]=select(max(0.,value),value,lane==0u);}
}`;

export interface IntegrationOptions {
 maxAttempts?:number;maxWallMs?:number;
 implementation?:'reference'|'gpu';
 sampleTimes?:number[];
 checkpoint?:import('./ChemistryCheckpoint').TileCheckpoint;
 onCheckpoint?:(checkpoint:import('./ChemistryCheckpoint').TileCheckpoint)=>Promise<void>|void;
 inspection?:boolean;
 precision?:'float32';
 linearSolver?:'lu'|'refined-lu';
 onProgress?:(progress:{time:number;dt:number;attempts:number;rejected:number;wallMs:number})=>void;
}
export class ImplicitTile {
 private ready?:Promise<void>;private pipelines:Record<string,GPUComputePipeline>={};
 constructor(readonly device:GPUDevice,readonly mechanism:GPUBuffer){}
 private async compile(){
  const jac=`@group(0) @binding(0) var<storage,read> mechanism:array<f32>;@group(0) @binding(1) var<storage,read> states:array<f32>;@group(0) @binding(2) var<storage,read_write> output:array<f32>;
   @compute @workgroup_size(64) fn main(@builtin(workgroup_id) group:vec3u,@builtin(local_invocation_index) lane:u32){if(lane>=54u){return;}let cell=group.x;let f=evaluate(cell,i32(lane));let h=enthalpy(cell,i32(lane));for(var row=0u;row<54u;row++){output[cell*2970u+row*55u+lane]=select(f[row].y,h.y,row==0u);if(lane==0u){output[cell*2970u+row*55u+54u]=select(f[row].x,h.x,row==0u);}}}
   ${kinetics}\n${enthalpy}`;
  for(const [name,code] of Object.entries({jac,lu:referenceLu,apply})){
   const module=this.device.createShaderModule({code});const info=await module.getCompilationInfo();const errors=info.messages.filter(m=>m.type==='error');if(errors.length)throw Error(name+': '+errors.map(m=>`${m.lineNum}: ${m.message}`).join('\n'));
   this.pipelines[name]=await this.device.createComputePipelineAsync({layout:'auto',compute:{module,entryPoint:'main'}});
  }
 }
 async integrate(initial:number[][],duration:number,signal?:AbortSignal,options:IntegrationOptions={}){
  if(!initial.length||initial.length>256||initial.some(s=>s.length!==54)||!Number.isFinite(duration)||!(duration>0))throw Error('Invalid chemical tile');
  if(signal?.aborted)throw Error('Chemical integration cancelled');
  if(!Number.isInteger(options.maxAttempts??65536)||(options.maxAttempts??65536)<1||!Number.isFinite(options.maxWallMs??60000)||(options.maxWallMs??60000)<=0)throw Error('Invalid chemical integration budget');
  if(initial.some(s=>s.some(v=>!Number.isFinite(v))||s[0]<200||s[0]>3500||s.slice(1).some(v=>v<0)||Math.abs(s.slice(1).reduce((a,b)=>a+b,0)-1)>1e-6))throw Error('Invalid chemical state');
  const wallStart=performance.now();const compileStart=performance.now();await(this.ready??=this.compile());const profile={compilationMs:performance.now()-compileStart,submitCpuMs:0,mapWaitMs:0,submissions:0,dispatches:0,readbackBytes:0,gpuMs:null,gpuTimingSource:'unavailable',rejections:{estimator:0,newton:0,damping:0,lu:0,thermodynamics:0}};let rejectionReason:keyof typeof profile.rejections='newton';const n=initial.length,bytes=n*54*4,d=this.device,buffers:GPUBuffer[]=[];
  const make=(size:number)=>{const b=d.createBuffer({size,usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC|GPUBufferUsage.COPY_DST});buffers.push(b);return b;};
  const states=make(bytes),accepted=make(bytes),base=make(bytes),previous=make(bytes),full=make(bytes),delta=make(bytes),jac=make(n*2970*4),hTarget=make(n*4),status=make(n*8*4),par=make(8),summary=make(32);
  d.queue.writeBuffer(states,0,new Float32Array(initial.flat()));
  const staging=d.createBuffer({size:bytes+n*8*4,usage:GPUBufferUsage.MAP_READ|GPUBufferUsage.COPY_DST});
  const small=d.createBuffer({size:32,usage:GPUBufferUsage.MAP_READ|GPUBufferUsage.COPY_DST});buffers.push(staging,small);
  const bind=(name:string,bs:GPUBuffer[])=>d.createBindGroup({layout:this.pipelines[name].getBindGroupLayout(0),entries:bs.map((b,i)=>({binding:i,resource:{buffer:b}}))});
  const binds={jac:bind('jac',[this.mechanism,states,jac]),lu:bind('lu',[jac,states,base,hTarget,delta,status,par]),apply:bind('apply',[previous,delta,states,par])};
  const run=(name:keyof typeof binds)=>{const encoder=d.createCommandEncoder();const p=encoder.beginComputePass();p.setPipeline(this.pipelines[name]);p.setBindGroup(0,binds[name]);p.dispatchWorkgroups(n);p.end();const t=performance.now();d.queue.submit([encoder.finish()]);profile.submitCpuMs+=performance.now()-t;profile.submissions++;profile.dispatches++;};
  const copy=(src:GPUBuffer,dst:GPUBuffer,size=bytes)=>{const e=d.createCommandEncoder();e.copyBufferToBuffer(src,0,dst,0,size);const t=performance.now();d.queue.submit([e.finish()]);profile.submitCpuMs+=performance.now()-t;profile.submissions++;};
  const targetModule=d.createShaderModule({code:`@group(0) @binding(0) var<storage,read> j:array<f32>;@group(0) @binding(1) var<storage,read_write> h:array<f32>;@compute @workgroup_size(1) fn main(@builtin(global_invocation_id) id:vec3u){h[id.x]=j[id.x*2970u+54u];}`});
  const targetPipeline=d.createComputePipeline({layout:'auto',compute:{module:targetModule,entryPoint:'main'}});
  const targetBind=d.createBindGroup({layout:targetPipeline.getBindGroupLayout(0),entries:[{binding:0,resource:{buffer:jac}},{binding:1,resource:{buffer:hTarget}}]});
  const reduceModule=d.createShaderModule({code:`@group(0) @binding(0) var<storage,read> status:array<f32>;@group(0) @binding(1) var<storage,read> j:array<f32>;@group(0) @binding(2) var<storage,read> states:array<f32>;@group(0) @binding(3) var<storage,read> base:array<f32>;@group(0) @binding(4) var<storage,read> hTarget:array<f32>;@group(0) @binding(5) var<storage,read> par:array<f32>;@group(0) @binding(6) var<storage,read_write> result:array<f32>;
   @compute @workgroup_size(1) fn main(){var norm=0.;var failed=0.;var linear=0.;var pivot=1.;var energy=0.;for(var c=0u;c<${n}u;c++){var sum=0.;for(var r=0u;r<54u;r++){let value=states[c*54u+r];if((r==0u&&(!(value>=200.)||!(value<=3500.)))||(r>0u&&!(value>=0.))){failed=1.;}let tol=select(1e-12,1e-3,r==0u)+1e-5*max(abs(base[c*54u+r]),abs(states[c*54u+r]));var residual=states[c*54u+r]-base[c*54u+r]-par[0]*j[c*2970u+r*55u+54u];var scale=tol;if(r==0u){residual=j[c*2970u+54u]-hTarget[c];scale=max(1.,abs(j[c*2970u])*tol);}sum+=(residual/scale)*(residual/scale);}norm=max(norm,sqrt(sum/54.));failed=max(failed,status[c*8u+1u]);linear=max(linear,status[c*8u+2u]);pivot=max(pivot,status[c*8u+3u]);energy=max(energy,abs(j[c*2970u+54u]-hTarget[c])/max(1.,abs(hTarget[c])));}result[0]=norm;result[1]=failed;result[2]=linear;result[3]=pivot;result[4]=energy;}`});
  const reduce=d.createComputePipeline({layout:'auto',compute:{module:reduceModule,entryPoint:'main'}}),reduceBind=d.createBindGroup({layout:reduce.getBindGroupLayout(0),entries:[status,jac,states,base,hTarget,par,summary].map((b,i)=>({binding:i,resource:{buffer:b}}))});
  let blocks=0,newtons=0,maxLinear=0,maxAttemptedLinear=0,maxPivot=1;
  const read=async()=>{if(signal?.aborted)throw Error('Chemical integration cancelled');const e=d.createCommandEncoder(),p=e.beginComputePass();p.setPipeline(reduce);p.setBindGroup(0,reduceBind);p.dispatchWorkgroups(1);p.end();e.copyBufferToBuffer(summary,0,small,0,32);d.queue.submit([e.finish()]);const mapStart=performance.now();await small.mapAsync(GPUMapMode.READ);profile.mapWaitMs+=performance.now()-mapStart;profile.readbackBytes+=32;const a=new Float32Array(small.getMappedRange().slice(0));small.unmap();if(a.some(v=>!Number.isFinite(v)))throw Error('Non-finite chemistry diagnostic');blocks++;maxAttemptedLinear=Math.max(maxAttemptedLinear,a[2]);if(!a[1])maxLinear=Math.max(maxLinear,a[2]);maxPivot=Math.max(maxPivot,a[3]);return a;};
  const backward=async(dt:number)=>{
   copy(states,base);d.queue.writeBuffer(par,0,new Float32Array([dt,1]));
   for(let it=0;it<12;it++){
    run('jac');run('lu');let m=await read();newtons++;if(m[1]||!Number.isFinite(m[0])){rejectionReason=m[1]?'lu':'thermodynamics';return false;}if(m[0]<=.1)return true;
    copy(states,previous);const oldNorm=m[0];let improved=false;
    for(let damping=0;damping<8;damping++){d.queue.writeBuffer(par,0,new Float32Array([dt,2**(-damping)]));run('apply');run('jac');m=await read();if(m[0]<oldNorm||m[0]<=.1){improved=true;break;}}
    if(!improved){rejectionReason='damping';return false;}
   }rejectionReason='newton';return false;
  };
    const errorCode=`@group(0) @binding(0) var<storage,read> a:array<f32>;@group(0) @binding(1) var<storage,read> b:array<f32>;@group(0) @binding(2) var<storage,read_write> out:array<f32>;@compute @workgroup_size(1) fn main(){var worst=0.;for(var c=0u;c<${n}u;c++){var sum=0.;for(var i=0u;i<54u;i++){let id=c*54u+i;let tol=select(1e-12,1e-3,i==0u)+1e-5*max(abs(a[id]),abs(b[id]));sum+=pow((a[id]-b[id])/tol,2.);}worst=max(worst,sqrt(sum/54.));}out[0]=worst;}`;
    const ep=d.createComputePipeline({layout:'auto',compute:{module:d.createShaderModule({code:errorCode}),entryPoint:'main'}}),eb=d.createBindGroup({layout:ep.getBindGroupLayout(0),entries:[states,full,summary].map((b,i)=>({binding:i,resource:{buffer:b}}))});
  let time=0,dt=Math.min(1e-6,duration),attempts=0,rejected=0,energyError=0;const start=performance.now();
  try{
   run('jac');const e=d.createCommandEncoder(),p=e.beginComputePass();p.setPipeline(targetPipeline);p.setBindGroup(0,targetBind);p.dispatchWorkgroups(n);p.end();d.queue.submit([e.finish()]);copy(states,accepted);
   while(time<duration&&attempts<(options.maxAttempts??65536)&&dt>=1e-16&&performance.now()-start<(options.maxWallMs??60000)){
    if(signal?.aborted)throw Error('Chemical integration cancelled');attempts++;if(attempts===1||attempts%25===0)options.onProgress?.({time,dt,attempts,rejected,wallMs:performance.now()-start});dt=Math.min(dt,duration-time);
    const okFull=await backward(dt);copy(states,full);copy(accepted,states);const okHalf=await backward(dt/2);const okSecond=okHalf&&await backward(dt/2);
    const ce=d.createCommandEncoder(),cp=ce.beginComputePass();cp.setPipeline(ep);cp.setBindGroup(0,eb);cp.dispatchWorkgroups(1);cp.end();ce.copyBufferToBuffer(summary,0,small,0,32);d.queue.submit([ce.finish()]);const mapStart=performance.now();await small.mapAsync(GPUMapMode.READ);profile.mapWaitMs+=performance.now()-mapStart;profile.readbackBytes+=32;let error=new Float32Array(small.getMappedRange().slice(0))[0];small.unmap();
    if(!okFull||!okHalf||!okSecond)error=Infinity;
    if(Number.isFinite(error)&&error<=1){time+=dt;copy(states,accepted);const m=await read();energyError=Math.max(energyError,m[4]);dt*=Math.max(.2,Math.min(2,.9/Math.sqrt(Math.max(error,1e-4))));}
    else{profile.rejections[okFull&&okHalf&&okSecond?'estimator':rejectionReason]++;copy(accepted,states);rejected++;dt*=Number.isFinite(error)?Math.max(.2,Math.min(.5,.9/Math.sqrt(error))):.5;}
   }
   copy(accepted,states);const encoder=d.createCommandEncoder();encoder.copyBufferToBuffer(states,0,staging,0,bytes);d.queue.submit([encoder.finish()]);await staging.mapAsync(GPUMapMode.READ);const final=Array.from(new Float32Array(staging.getMappedRange().slice(0,bytes)));staging.unmap();if(final.some(v=>!Number.isFinite(v)))throw Error('Non-finite accepted chemistry state');
   return {profile:{...profile,wallMs:performance.now()-wallStart},diagnostics:{time,attempts,rejected,newtonIterations:newtons,maxAcceptedLinearResidual:maxLinear,maxAttemptedLinearResidual:maxAttemptedLinear,maxPivotRatio:maxPivot,enthalpyFraction:energyError,complete:time>=duration},states:final,status:[time,attempts,rejected,newtons,0,maxLinear,maxPivot,0,energyError,Number(time>=duration)],stopReason:time>=duration?'completed':dt<1e-16?'step-underflow':attempts>=(options.maxAttempts??65536)?'attempt-limit':'wall-limit',maxAttemptedLinear,wallMs:performance.now()-start,workgroupBytes:12776,blocks};
  }finally{for(const b of buffers)b.destroy();}
 }
}
