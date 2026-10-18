// A snapshot is taken after LU and before the controller. vec2f in kinetics
// remains a dual number (value, derivative), never a double-single number.
export const TRACE_STRIDE = 427;
export const traceShader = `
@group(0) @binding(0) var<storage,read> states:array<f32>;
@group(0) @binding(1) var<storage,read> work:array<f32>;
@group(0) @binding(2) var<storage,read> jac:array<f32>;
@group(0) @binding(3) var<storage,read> status:array<f32>;
@group(0) @binding(4) var<storage,read> control:array<f32>;
@group(0) @binding(5) var<storage,read_write> trace:array<f32>;
var<workgroup> slot:u32;
@compute @workgroup_size(64) fn main(@builtin(local_invocation_index) lane:u32){
 if(lane==0u){slot=u32(trace[0]);trace[0]+=1.;}workgroupBarrier();
 let capacity=(arrayLength(&trace)-4u)/427u;
 let b=4u+(slot%capacity)*427u;
 if(lane==0u){trace[b+426u]=jac[0];}
 if(lane<54u){trace[b+lane]=states[lane];trace[b+372u+lane]=jac[lane*55u+54u];}
 for(var i=lane;i<270u;i+=64u){trace[b+54u+i]=work[i];}
 if(lane<40u){trace[b+324u+lane]=control[lane];}
 if(lane<8u){trace[b+364u+lane]=status[lane];}
}`;

export function decodeTrace(values:Float32Array, capacity:number){
 const total=values[0],retained=Math.min(total,capacity),start=total-retained;
 return {schema:1,source:'GPU snapshot after LU before controller',total,capacity,dropped:start,
   records:Array.from({length:retained},(_,i)=>{
     const sequence=start+i,b=4+(sequence%capacity)*TRACE_STRIDE;
     const take=(offset:number,n:number)=>Array.from(values.subarray(b+offset,b+offset+n));
     return {sequence,state:take(0,54),work:take(54,270),control:take(324,40),linear:take(364,8),rhs:take(372,54),enthalpyDerivative:values[b+426]};
   })};
}
