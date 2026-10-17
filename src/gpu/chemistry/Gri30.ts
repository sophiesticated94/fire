/// <reference types="@webgpu/types" />
import table from './data/mechanism.json';
import provenance from './data/provenance.json';
import kinetics from './kinetics.wgsl?raw';
import {ImplicitTile,type IntegrationOptions} from './ImplicitTile';

export class Gri30 {
 readonly model='gpu-gri30-0.1-experimental';
 readonly species=table.species;readonly provenance=provenance;
 private mechanism:GPUBuffer;private pipeline:GPUComputePipeline;private integrator?:ImplicitTile;
 readonly source=`@group(0) @binding(0) var<storage,read> mechanism:array<f32>;
 @group(0) @binding(1) var<storage,read> states:array<f32>;
 @group(0) @binding(2) var<storage,read_write> output:array<f32>;
 @compute @workgroup_size(64) fn main(@builtin(workgroup_id) group:vec3u,@builtin(local_invocation_index) lane:u32){
  let cell=group.x;if(lane>=54u){return;}let f=evaluate(cell,i32(lane));
  for(var row=0u;row<54u;row++){output[cell*2970u+row*55u+lane]=f[row].y;if(lane==0u){output[cell*2970u+row*55u+54u]=f[row].x;}}
 }
 ${kinetics}`;
 constructor(readonly device:GPUDevice){
  this.mechanism=device.createBuffer({size:table.data.length*4,usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST});device.queue.writeBuffer(this.mechanism,0,new Float32Array(table.data));
  this.pipeline=device.createComputePipeline({layout:'auto',compute:{module:device.createShaderModule({code:this.source}),entryPoint:'main'}});
 }
 async evaluate(states:number[][]){
  if(!states.length||states.length>256||states.some(s=>s.length!==54))throw Error('GRI test tile must contain 1–256 complete reactor states');
  const input=this.device.createBuffer({size:states.length*54*4,usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST});this.device.queue.writeBuffer(input,0,new Float32Array(states.flat()));
  const output=this.device.createBuffer({size:states.length*2970*4,usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC});
  const staging=this.device.createBuffer({size:output.size,usage:GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ});
  try{
   const bind=this.device.createBindGroup({layout:this.pipeline.getBindGroupLayout(0),entries:[{binding:0,resource:{buffer:this.mechanism}},{binding:1,resource:{buffer:input}},{binding:2,resource:{buffer:output}}]});
   const encoder=this.device.createCommandEncoder();const pass=encoder.beginComputePass();pass.setPipeline(this.pipeline);pass.setBindGroup(0,bind);pass.dispatchWorkgroups(states.length);pass.end();encoder.copyBufferToBuffer(output,0,staging,0,output.size);this.device.queue.submit([encoder.finish()]);
   await staging.mapAsync(GPUMapMode.READ);const values=new Float32Array(staging.getMappedRange().slice(0));staging.unmap();return Array.from(values);
  }finally{input.destroy();output.destroy();staging.destroy();}
 }
 async integrate(states:number[][],duration:number,signal?:AbortSignal,options:IntegrationOptions={}){
  this.integrator??=new ImplicitTile(this.device,this.mechanism);
  return {model:this.model,mechanismSha256:this.provenance.sha256,...await this.integrator.integrate(states,duration,signal,options)};
 }
 dispose(){this.mechanism.destroy();}
}
