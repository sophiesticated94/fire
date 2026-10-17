import kinetics from './kinetics.wgsl?raw';
import enthalpy from './enthalpy.wgsl?raw';
import {referenceLu} from './ImplicitTile';

// Explicit SoA-in-buffers contract: 54 state values, 5*54 scratch values,
// 54*55 Jacobian values, 8 LU metrics and 40 controller values per reactor.
// Controller indices are shared with GpuImplicitTile and checkpoint schema 1.
const bindings = `
@group(0) @binding(0) var<storage,read_write> states:array<f32>;
@group(0) @binding(1) var<storage,read_write> work:array<f32>;
@group(0) @binding(2) var<storage,read> jac:array<f32>;
@group(0) @binding(3) var<storage,read> status:array<f32>;
@group(0) @binding(4) var<storage,read_write> control:array<f32>;
@group(0) @binding(5) var<storage,read> schedule:array<f32>;
@group(0) @binding(6) var<storage,read_write> trajectory:array<f32>;
`;

export const tileJacobian = `
@group(0) @binding(0) var<storage,read> mechanism:array<f32>;
@group(0) @binding(1) var<storage,read> states:array<f32>;
@group(0) @binding(2) var<storage,read_write> output:array<f32>;
@group(0) @binding(3) var<storage,read> control:array<f32>;
@compute @workgroup_size(64) fn main(@builtin(workgroup_id) g:vec3u,@builtin(local_invocation_index) lane:u32){
 let cell=g.x;let phase=control[cell*40u+8u];
 if(lane>=54u || (phase!=1. && phase!=3.)){return;}
 if(phase==3.){
  if(lane!=0u){return;}let trial=evaluate(cell,-1);let trialH=enthalpy(cell,0);
  for(var row=0u;row<54u;row++){output[cell*2970u+row*55u+54u]=select(trial[row].x,trialH.x,row==0u);}
  output[cell*2970u]=trialH.y;return;
 }
 let f=evaluate(cell,i32(lane));let h=enthalpy(cell,i32(lane));
 for(var row=0u;row<54u;row++){
  output[cell*2970u+row*55u+lane]=select(f[row].y,h.y,row==0u);
  if(lane==0u){output[cell*2970u+row*55u+54u]=select(f[row].x,h.x,row==0u);}
 }
}
${kinetics}\n${enthalpy}`;

// Reuse the unchanged cooperative factorization, including its residual test.
// The uniform guard precedes every barrier, including all early returns.
export const tileLu = referenceLu
  .replace('@group(0) @binding(2) var<storage,read> base:array<f32>;', '@group(0) @binding(2) var<storage,read_write> work:array<f32>;')
  .replace('@group(0) @binding(3) var<storage,read> hTarget:array<f32>;', '@group(0) @binding(3) var<storage,read> control:array<f32>;')
  .replace('@group(0) @binding(4) var<storage,read_write> delta:array<f32>;', '')
  .replace('@group(0) @binding(6) var<storage,read> parameters:array<f32>;', 'var<workgroup> enabled:u32;')
  .replace('let cell=group.x;', `if(lane==0u){enabled=select(0u,1u,control[group.x*40u+8u]==1. && control[group.x*40u+19u]==1.);}workgroupBarrier();
 if(workgroupUniformLoad(&enabled)==0u){return;}let cell=group.x;`)
  .replace('parameters[0]', 'control[cell*40u+2u]')
  .replaceAll('base[offset+lane]', 'work[cell*270u+54u+lane]')
  .replaceAll('base[offset+row]', 'work[cell*270u+54u+row]')
  .replaceAll('hTarget[cell]', 'control[cell*40u+3u]')
  .replaceAll('delta[offset+lane]', 'work[cell*270u+216u+lane]')
  .replaceAll('delta[offset+row]', 'work[cell*270u+216u+row]')
  .replace('status[state+3u]=largest/smallest;', 'let ratio=largest/smallest;status[state+3u]=min(ratio,3.402823e38);status[state+4u]=select(0.,1.,!(ratio<=3.402823e38));')
  .replace('work[cell*270u+216u+row]=solution[row]*scale[row];', `work[cell*270u+216u+row]=solution[row]*scale[row];
   if(!(abs(solution[row])<=3.402823e38) || !(abs(work[cell*270u+216u+row])<=3.402823e38) || !(errors[row]<=3.402823e38)){
    errors[row]=3.402823e38;work[cell*270u+216u+row]=0.;
   }`);

// Same float32 tolerances and matrix, with two residual-correction solves.
// Pivot permutations are retained explicitly; no second dense matrix is needed.
export const tileRefinedLu = tileLu
 .replace('var<workgroup> enabled:u32;', 'var<workgroup> enabled:u32;var<workgroup> permutation:array<u32,54>;var<workgroup> correction:array<f32,54>;')
 .replace('if(lane<54u){scale[lane]=', 'if(lane<54u){permutation[lane]=lane;scale[lane]=')
 .replace('let picked=workgroupUniformLoad(&pivot);', 'let picked=workgroupUniformLoad(&pivot);if(lane==0u){let old=permutation[col];permutation[col]=permutation[picked];permutation[picked]=old;}')
 .replace('if(lane<54u){let row=lane;let rowScale=select(scale[row],hScale,row==0u);var lhs=0.;', `
 for(var refinement=0u;refinement<2u;refinement++){
  if(lane<54u){let row=lane;let rowScale=select(scale[row],hScale,row==0u);var lhs=0.;var compensation=0.;
   for(var col=0u;col<54u;col++){
    var value=select(0.,1.,row==col)-dt*jac[jbase+row*55u+col];if(row==0u){value=jac[jbase+col];}
    let term=value*scale[col]/rowScale*solution[col]-compensation;let sum=lhs+term;compensation=(sum-lhs)-term;lhs=sum;
   }errors[row]=original[row]-lhs;
  }workgroupBarrier();
  if(lane==0u){
   for(var row=0u;row<54u;row++){var v=errors[permutation[row]];for(var col=0u;col<row;col++){v-=a[row*55u+col]*correction[col];}correction[row]=v;}
   for(var row=53i;row>=0i;row--){var v=correction[u32(row)];for(var col=u32(row)+1u;col<54u;col++){v-=a[u32(row)*55u+col]*correction[col];}correction[u32(row)]=v/a[u32(row)*55u+u32(row)];}
   xNorm=0.;for(var row=0u;row<54u;row++){solution[row]+=correction[row];xNorm=max(xNorm,abs(solution[row]));}
  }workgroupBarrier();
 }
 if(lane<54u){let row=lane;let rowScale=select(scale[row],hScale,row==0u);var lhs=0.;`);

export const tileController = `${bindings}
var<workgroup> terms:array<f32,64>;
var<workgroup> errors:array<f32,64>;
var<workgroup> invalid:array<f32,64>;
fn reject(c:u32,reason:u32){
 control[c+15u]=f32(reason);control[c+27u+reason]+=1.;control[c+13u]+=1.;
 control[c+8u]=4.;
}
@compute @workgroup_size(64) fn main(@builtin(workgroup_id) g:vec3u,@builtin(local_invocation_index) lane:u32){
 let cell=g.x;let c=cell*40u;let o=cell*54u;let w=cell*270u;let j=cell*2970u;
 let phase=control[c+8u];
 terms[lane]=0.;errors[lane]=0.;invalid[lane]=0.;
 if(lane<54u && (phase==1. || phase==3.)){
  let value=states[o+lane];let base=work[w+54u+lane];
  let tol=select(1e-12,1e-3,lane==0u)+1e-5*max(abs(base),abs(value));
  var r=value-base-control[c+2u]*jac[j+lane*55u+54u];var scale=tol;
  if(lane==0u){r=jac[j+54u]-control[c+3u];scale=max(1.,abs(jac[j])*tol);}
  terms[lane]=(r/scale)*(r/scale);
  let referenceState=work[w+162u+lane];let et=select(1e-12,1e-3,lane==0u)+1e-5*max(abs(value),abs(referenceState));
  errors[lane]=((value-referenceState)/et)*((value-referenceState)/et);
  if(!(value>=0.) || !(value<=3.402823e38) || (lane==0u && (!(value>=300.) || !(value<=3000.)))){invalid[lane]=1.;}
 }
 workgroupBarrier();
 for(var stride=32u;stride>0u;stride/=2u){
  if(lane<stride){terms[lane]+=terms[lane+stride];errors[lane]=max(errors[lane],errors[lane+stride]);invalid[lane]=max(invalid[lane],invalid[lane+stride]);}workgroupBarrier();
 }
 if(lane!=0u){return;}
 if(phase==5. || phase==6.){return;}
 if(control[c+24u]>=16777200. || control[c+25u]>=16777200.){control[c+8u]=6.;control[c+15u]=9.;return;}
 if(phase==4.){
  for(var i=0u;i<54u;i++){states[o+i]=work[w+i];work[w+54u+i]=work[w+i];}
  if(control[c+15u]!=1.){control[c+1u]=control[c+2u]*select(.5,1.,control[c+9u]>0.);}
  if(control[c+1u]<1e-16){control[c+8u]=6.;control[c+15u]=8.;return;}
  if(control[c+12u]>=schedule[2]){control[c+8u]=6.;control[c+15u]=9.;return;}
  control[c+2u]=min(control[c+1u],schedule[4u+u32(control[c+20u])]-control[c]+control[c+27u]);
  control[c+9u]=0.;control[c+10u]=0.;control[c+11u]=0.;control[c+12u]+=1.;control[c+8u]=1.;return;
 }
 if(phase!=1. && phase!=3.){return;}
 if(control[c+19u]==0.){control[c+3u]=jac[j+54u];control[c+19u]=1.;return;}
 let norm=sqrt(terms[0]/54.);control[c+4u]=norm;
 if(invalid[0]>0. || !(norm<=3.402823e38)){reject(c,6u);return;}
 let hError=abs(jac[j+54u]-control[c+3u])/max(1.,abs(control[c+3u]));
 if(phase==1.){
  control[c+24u]+=1.;control[c+17u]=max(control[c+17u],status[cell*8u+2u]);
  control[c+18u]=max(control[c+18u],status[cell*8u+3u]);control[c+38u]=max(control[c+38u],status[cell*8u+4u]);
  if(status[cell*8u+1u]>0.){reject(c,4u);return;}
  control[c+16u]=max(control[c+16u],status[cell*8u+2u]);
 }else{
  control[c+25u]+=1.;control[c+37u]=max(control[c+37u],control[c+22u]);
  if(control[c+22u]>.1){reject(c,5u);return;}
  if(!(norm<control[c+6u] || norm<=.1)){
   control[c+11u]+=1.;if(control[c+11u]>=8.){reject(c,3u);return;}
   control[c+5u]*=.5;control[c+8u]=2.;return;
  }
  control[c+10u]+=1.;
 }
 if(norm>.1){
  if(control[c+10u]>=12.){reject(c,2u);return;}
  if(phase==3.){control[c+8u]=1.;return;}
  for(var i=0u;i<54u;i++){work[w+108u+i]=states[o+i];}
  control[c+6u]=norm;control[c+5u]=1.;control[c+11u]=0.;control[c+8u]=2.;return;
 }
 if(hError>1e-5){reject(c,7u);return;}
 if(control[c+9u]==0.){
  for(var i=0u;i<54u;i++){work[w+162u+i]=states[o+i];states[o+i]=work[w+i];work[w+54u+i]=work[w+i];}
  control[c+9u]=1.;control[c+2u]*=.5;
 }else if(control[c+9u]==1.){
  for(var i=0u;i<54u;i++){work[w+54u+i]=states[o+i];}control[c+9u]=2.;
 }else{
  let error=sqrt(errors[0]);control[c+23u]=error;
  if(!(error<=1.)){
   control[c+1u]=control[c+2u]*2.*max(.2,min(.5,.9/sqrt(error)));reject(c,1u);return;
  }
  let step=control[c+2u]*2.;let sampleTarget=schedule[4u+u32(control[c+20u])];
  let remaining=sampleTarget-control[c]+control[c+27u];
  let y=step-control[c+27u];let t=control[c]+y;control[c+27u]=(t-control[c])-y;control[c]=t;
  control[c+26u]=step;control[c+14u]+=1.;control[c+7u]=max(control[c+7u],hError);
  for(var i=0u;i<54u;i++){work[w+i]=states[o+i];work[w+54u+i]=states[o+i];}
  control[c+1u]=step*max(.2,min(2.,.9/sqrt(max(error,1e-4))));
  if(step>=remaining){
   control[c]=sampleTarget;control[c+27u]=0.;let sample=u32(control[c+20u]);
   for(var i=0u;i<54u;i++){trajectory[(cell*u32(schedule[1])+sample)*54u+i]=states[o+i];}
   control[c+20u]+=1.;if(control[c+20u]>=schedule[1]){control[c+8u]=5.;return;}
  }
  if(control[c+12u]>=schedule[2]){control[c+8u]=6.;control[c+15u]=9.;return;}
  control[c+2u]=min(control[c+1u],schedule[4u+u32(control[c+20u])]-control[c]+control[c+27u]);
  control[c+9u]=0.;control[c+12u]+=1.;
 }
 control[c+10u]=0.;control[c+11u]=0.;control[c+8u]=1.;
}`;

export const tileApply = `${bindings}
var<workgroup> alphas:array<f32,64>;
var<workgroup> corrections:array<f32,64>;
var<workgroup> enabled:u32;
@compute @workgroup_size(64) fn main(@builtin(workgroup_id) g:vec3u,@builtin(local_invocation_index) lane:u32){
 let c=g.x*40u;let w=g.x*270u;let o=g.x*54u;
 if(lane==0u){enabled=select(0u,1u,control[c+8u]==2.);}workgroupBarrier();
 if(workgroupUniformLoad(&enabled)==0u){return;}
 var alpha=control[c+5u];
 if(lane>0u && lane<54u){let d=work[w+216u+lane];let y=work[w+108u+lane];
  if(d<0. && y+alpha*d < -1e-12){alpha=min(alpha,.99*y/(-d));}
 }
 alphas[lane]=alpha;workgroupBarrier();
 for(var stride=32u;stride>0u;stride/=2u){if(lane<stride){alphas[lane]=min(alphas[lane],alphas[lane+stride]);}workgroupBarrier();}
 corrections[lane]=0.;
 if(lane<54u){let raw=work[w+108u+lane]+alphas[0]*work[w+216u+lane];let value=select(max(0.,raw),raw,lane==0u);states[o+lane]=value;
  if(lane>0u){corrections[lane]=abs(value-raw)/(1e-12+1e-5*abs(work[w+108u+lane]));}
  if(!(abs(raw)<=3.402823e38)){states[o+lane]=raw;corrections[lane]=3.402823e38;}
 }
 workgroupBarrier();for(var stride=32u;stride>0u;stride/=2u){if(lane<stride){corrections[lane]=max(corrections[lane],corrections[lane+stride]);}workgroupBarrier();}
 if(lane==0u){control[c+22u]=corrections[0];control[c+8u]=3.;}
}`;

// Second reduction level: reactor metrics are already parallel. Each lane
// handles at most four reactors; no serial scan of the entire campaign.
export const tileSummary = `
@group(0) @binding(0) var<storage,read> control:array<f32>;
@group(0) @binding(1) var<storage,read_write> result:array<f32>;
@group(0) @binding(2) var<storage,read> schedule:array<f32>;
var<workgroup> values:array<f32,1024>;
@compute @workgroup_size(64) fn main(@builtin(local_invocation_index) lane:u32){
 for(var k=0u;k<16u;k++){values[lane*16u+k]=0.;}values[lane*16u]=3.402823e38;values[lane*16u+14u]=3.402823e38;
 for(var cell=lane;cell<u32(schedule[0]);cell+=64u){let c=cell*40u;let b=lane*16u;
  values[b]=min(values[b],control[c]);values[b+1u]=max(values[b+1u],control[c]);
  values[b+2u]+=control[c+12u];values[b+3u]+=control[c+13u];
  values[b+4u]+=select(0.,1.,control[c+8u]==5.);values[b+5u]+=select(0.,1.,control[c+8u]==6.);
  values[b+6u]=max(values[b+6u],control[c+16u]);values[b+7u]=max(values[b+7u],control[c+7u]);
  values[b+8u]+=control[c+24u];values[b+9u]+=control[c+14u];
  values[b+10u]=max(values[b+10u],control[c+17u]);values[b+11u]=max(values[b+11u],control[c+18u]);
  if(control[c+8u]<5.){values[b+14u]=min(values[b+14u],control[c+1u]);}
  values[b+12u]+=control[c+25u];values[b+13u]=max(values[b+13u],control[c+22u]);
 }workgroupBarrier();
 for(var stride=32u;stride>0u;stride/=2u){if(lane<stride){for(var k=0u;k<16u;k++){
  let a=lane*16u+k;let b=(lane+stride)*16u+k;
  if(k==0u || k==14u){values[a]=min(values[a],values[b]);}else if(k==1u || k==6u || k==7u || k==10u || k==11u || k==13u){values[a]=max(values[a],values[b]);}else{values[a]+=values[b];}
 }}workgroupBarrier();}
 if(lane==0u){for(var k=0u;k<16u;k++){result[k]=values[k];}}
}`;

