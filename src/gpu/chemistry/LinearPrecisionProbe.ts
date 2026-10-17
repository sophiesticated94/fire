/// <reference types="@webgpu/types" />
// Diagnostic only. This never advances a reactor and is not a chemistry fallback.
// Storage-backed double-single avoids exceeding 16 KiB workgroup memory. Four
// small systems at most: a deliberately bounded experiment, not a 3D solver.
const source=`
@group(0) @binding(0) var<storage,read> input:array<f32>;
@group(0) @binding(1) var<storage,read_write> matrix:array<vec2f>;
@group(0) @binding(2) var<storage,read_write> output:array<vec2f>;
@group(0) @binding(3) var<uniform> parameters:vec4u;
fn add(a:vec2f,b:vec2f)->vec2f{
 if(parameters.y==0u){return vec2f(a.x+b.x,0.);}
 let s=a.x+b.x;let v=s-a.x;let e=(a.x-(s-v))+(b.x-v)+a.y+b.y;
 let hi=s+e;return vec2f(hi,e-(hi-s));
}
fn neg(a:vec2f)->vec2f{return -a;}
fn mul(a:vec2f,b:vec2f)->vec2f{
 let p=a.x*b.x;if(parameters.y==0u){return vec2f(p,0.);}
 // Dekker product, independent of whether this driver fuses fma.
 let ca=4097.*a.x;let ah=ca-(ca-a.x);let al=a.x-ah;
 let cb=4097.*b.x;let bh=cb-(cb-b.x);let bl=b.x-bh;
 let error=((ah*bh-p)+ah*bl+al*bh)+al*bl+a.x*b.y+a.y*b.x;
 let hi=p+error;return vec2f(hi,error-(hi-p));
}
fn divide(a:vec2f,b:vec2f)->vec2f{
 let q=a.x/b.x;if(parameters.y==0u){return vec2f(q,0.);}
 let r=add(a,neg(mul(b,vec2f(q,0.))));return add(vec2f(q,0.),vec2f((r.x+r.y)/b.x,0.));
}
@compute @workgroup_size(1) fn main(@builtin(workgroup_id) g:vec3u){
 let n=parameters.x;let base=g.x*n*(n+1u);let out=g.x*(n+1u);
 for(var i=0u;i<n*(n+1u);i++){matrix[base+i]=vec2f(input[base+i],0.);}
 output[out+n]=vec2f(0.);
 for(var col=0u;col<n;col++){
  var picked=col;var pivot=abs(matrix[base+col*(n+1u)+col].x);
  for(var r=col+1u;r<n;r++){let v=abs(matrix[base+r*(n+1u)+col].x);if(v>pivot){pivot=v;picked=r;}}
  if(!(pivot>1e-30)){output[out+n]=vec2f(1.);return;}
  for(var k=col;k<=n;k++){let a=base+col*(n+1u)+k;let b=base+picked*(n+1u)+k;let old=matrix[a];matrix[a]=matrix[b];matrix[b]=old;}
  for(var r=col+1u;r<n;r++){
   let factor=divide(matrix[base+r*(n+1u)+col],matrix[base+col*(n+1u)+col]);
   for(var k=col+1u;k<=n;k++){let a=base+r*(n+1u)+k;matrix[a]=add(matrix[a],neg(mul(factor,matrix[base+col*(n+1u)+k])));}
  }
 }
 for(var row=i32(n)-1;row>=0;row--){var v=matrix[base+u32(row)*(n+1u)+n];
  for(var k=u32(row)+1u;k<n;k++){v=add(v,neg(mul(matrix[base+u32(row)*(n+1u)+k],output[out+k])));}
  output[out+u32(row)]=divide(v,matrix[base+u32(row)*(n+1u)+u32(row)]);
 }
}`;

export async function probeLinearPrecision(device:GPUDevice,systems:number[][],dimension:number,mode:'float32'|'double-single'){
  if(!['float32','double-single'].includes(mode)||!Number.isInteger(dimension)||dimension<1||dimension>54||!systems.length||systems.length>4||systems.some(s=>s.length!==dimension*(dimension+1)||s.some(x=>!Number.isFinite(x))))throw Error('Invalid linear precision probe');
  const start=performance.now(),buffers:GPUBuffer[]=[];
  const make=(size:number,usage:GPUBufferUsageFlags)=>{const b=device.createBuffer({size,usage});buffers.push(b);return b;};
  try{
    const input=make(systems.flat().length*4,GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_DST);
    const matrix=make(input.size*2,GPUBufferUsage.STORAGE),output=make(systems.length*(dimension+1)*8,GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC);
    const parameters=make(16,GPUBufferUsage.UNIFORM|GPUBufferUsage.COPY_DST),staging=make(output.size,GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ);
    device.queue.writeBuffer(input,0,new Float32Array(systems.flat()));device.queue.writeBuffer(parameters,0,new Uint32Array([dimension,Number(mode==='double-single'),0,0]));
    const pipeline=await device.createComputePipelineAsync({layout:'auto',compute:{module:device.createShaderModule({code:source}),entryPoint:'main'}});
    const group=device.createBindGroup({layout:pipeline.getBindGroupLayout(0),entries:[input,matrix,output,parameters].map((buffer,binding)=>({binding,resource:{buffer}}))});
    const e=device.createCommandEncoder(),p=e.beginComputePass();p.setPipeline(pipeline);p.setBindGroup(0,group);p.dispatchWorkgroups(systems.length);p.end();e.copyBufferToBuffer(output,0,staging,0,output.size);device.queue.submit([e.finish()]);
    await staging.mapAsync(GPUMapMode.READ);const values=new Float32Array(staging.getMappedRange().slice(0));staging.unmap();
    return {mode,wallMs:performance.now()-start,storageBytes:buffers.reduce((a,b)=>a+b.size,0),workgroupBytes:0,
      systems:systems.map((_,c)=>({solution:Array.from({length:dimension},(_,i)=>values[(c*(dimension+1)+i)*2]+values[(c*(dimension+1)+i)*2+1]),failed:values[(c*(dimension+1)+dimension)*2]!==0 || Array.from(values.subarray(c*(dimension+1)*2,(c+1)*(dimension+1)*2)).some(x=>!Number.isFinite(x))}))};
  }finally{buffers.forEach(b=>b.destroy());}
}
