// Double-single NASA7 and first-order input-low correction to f32 species RHS.
// No double-single exp/log, reaction coefficients or full chemistry here.
// AD vec2f in kinetics remains (value, derivative), never (hi, lo).
export const accurateEnthalpy=`
struct DoubleSingle {hi:f32,lo:f32}
fn ds(a:f32)->DoubleSingle{return DoubleSingle(a,0.);}
fn plus(a:DoubleSingle,b:DoubleSingle)->DoubleSingle{
 let s=a.hi+b.hi;let z=s-a.hi;let e=(a.hi-(s-z))+(b.hi-z)+a.lo+b.lo;
 let hi=s+e;return DoubleSingle(hi,e-(hi-s));
}
fn minus(a:DoubleSingle,b:DoubleSingle)->DoubleSingle{return plus(a,DoubleSingle(-b.hi,-b.lo));}
fn times(a:DoubleSingle,b:DoubleSingle)->DoubleSingle{
 let p=a.hi*b.hi;
 let ca=4097.*a.hi;let ah=ca-(ca-a.hi);let al=a.hi-ah;
 let cb=4097.*b.hi;let bh=cb-(cb-b.hi);let bl=b.hi-bh;
 let e=((ah*bh-p)+ah*bl+al*bh)+al*bl+a.hi*b.lo+a.lo*b.hi+a.lo*b.lo;
 let hi=p+e;return DoubleSingle(hi,e-(hi-p));
}
fn divide(a:DoubleSingle,b:DoubleSingle)->DoubleSingle{
 let q=a.hi/b.hi;let r=minus(a,times(b,ds(q)));
 return plus(ds(q),ds((r.hi+r.lo)/b.hi));
}
@group(0) @binding(0) var<storage,read> mechanism:array<f32>;
@group(0) @binding(1) var<storage,read> mechanismLow:array<f32>;
@group(0) @binding(2) var<storage,read> states:array<f32>;
@group(0) @binding(3) var<storage,read_write> low:array<f32>;
@group(0) @binding(4) var<storage,read_write> jac:array<f32>;
@group(0) @binding(5) var<storage,read> control:array<f32>;
fn coefficient(i:u32)->DoubleSingle{return DoubleSingle(mechanism[i],mechanismLow[i]);}
var<workgroup> enthalpies:array<DoubleSingle,64>;
var<workgroup> energies:array<DoubleSingle,64>;
var<workgroup> capacities:array<DoubleSingle,64>;
var<workgroup> masses:array<DoubleSingle,64>;
var<workgroup> enabled:u32;
@compute @workgroup_size(64) fn main(@builtin(workgroup_id) group:vec3u,@builtin(local_invocation_index) lane:u32){
 let cell=group.x;let c=cell*40u;let j=cell*2970u;let o=cell*54u;let l=cell*328u;
 // Uniform guard: every active lane reaches all reduction barriers.
 if(lane==0u){enabled=select(0u,1u,control[c+8u]==1. || control[c+8u]==3.);}workgroupBarrier();
 if(workgroupUniformLoad(&enabled)==0u){return;}
 enthalpies[lane]=ds(0.);energies[lane]=ds(0.);capacities[lane]=ds(0.);masses[lane]=ds(0.);
 if(lane<53u){
  let t=DoubleSingle(states[o],low[l]);let y=DoubleSingle(states[o+lane+1u],low[l+lane+1u]);
  let base=57u+lane*15u;let middle=coefficient(base);
  let high=t.hi>middle.hi || (t.hi==middle.hi && t.lo>middle.lo);
  let a=base+1u+select(0u,7u,high);
  // NASA7: h/R = a1*T + a2*T²/2 + ... + a5*T⁵/5 + a6.
  var h=divide(coefficient(a+4u),ds(5.));
  h=plus(times(h,t),divide(coefficient(a+3u),ds(4.)));
  h=plus(times(h,t),divide(coefficient(a+2u),ds(3.)));
  h=plus(times(h,t),divide(coefficient(a+1u),ds(2.)));
  h=plus(times(h,t),coefficient(a));h=plus(times(h,t),coefficient(a+5u));
  var cp=coefficient(a+4u);cp=plus(times(cp,t),coefficient(a+3u));
  cp=plus(times(cp,t),coefficient(a+2u));cp=plus(times(cp,t),coefficient(a+1u));cp=plus(times(cp,t),coefficient(a));
  let specific=divide(coefficient(2u),coefficient(4u+lane));
  enthalpies[lane]=times(h,specific);energies[lane]=times(y,enthalpies[lane]);
  capacities[lane]=times(y,times(cp,specific));masses[lane]=y;
 }
 workgroupBarrier();
 for(var stride=32u;stride>0u;stride/=2u){
  if(lane<stride){energies[lane]=plus(energies[lane],energies[lane+stride]);capacities[lane]=plus(capacities[lane],capacities[lane+stride]);masses[lane]=plus(masses[lane],masses[lane+stride]);}
  workgroupBarrier();
 }
 let h=divide(energies[0],masses[0]);
 if(lane==0u){let cp=divide(capacities[0],masses[0]);jac[j]=cp.hi+cp.lo;jac[j+54u]=h.hi;low[l+270u]=h.lo;}
 if(lane<53u){let derivative=divide(minus(enthalpies[lane],h),masses[0]);jac[j+lane+1u]=derivative.hi+derivative.lo;}
 if(lane>0u && lane<54u){
  let row=j+lane*55u;var source=ds(jac[row+54u]);
  for(var col=0u;col<54u;col++){source=plus(source,times(ds(jac[row+col]),ds(low[l+col])));}
  jac[row+54u]=source.hi;low[l+271u+lane]=source.lo;
 }
}`;
