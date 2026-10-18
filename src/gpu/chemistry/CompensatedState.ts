import {tileLu,tileRefinedLu,tileController,tileApply} from './TileShaders';

// Compensated state and a separate NASA7 kernel. Species kinetics, its AD and
// LU remain f32. This is deliberately NOT full double-single chemistry.
const binding='\n@group(0) @binding(7) var<storage,read_write> low:array<f32>;\n';
const helpers=`
struct StatePair {hi:f32,lo:f32}
fn stateSum(a:f32,b:f32)->StatePair{
 let s=a+b;let z=s-a;return StatePair(s,(a-(s-z))+(b-z));
}
`;

export function compensatedSources(refined:boolean){
 const lu=(refined?tileRefinedLu:tileLu)+binding;
 const withResidual=lu.replace(
  'var residual=states[offset+row]-work[cell*270u+54u+row]-dt*jac[jbase+row*55u+54u];',
  'var residual=(states[offset+row]-work[cell*270u+54u+row])+(low[cell*328u+row]-low[cell*328u+108u+row])-dt*jac[jbase+row*55u+54u]-dt*low[cell*328u+271u+row];');
 if(withResidual===lu)throw Error('Compensated LU template changed');
 const withEnergy=withResidual.replace('residual=jac[jbase+54u]-control[cell*40u+3u];',
  'residual=(jac[jbase+54u]-control[cell*40u+3u])+(low[cell*328u+270u]-low[cell*328u+271u]);');
 let controller=tileController+binding;
 controller=controller.replace('var r=value-base-control[c+2u]*jac[j+lane*55u+54u];',
  'var r=(value-base)+(low[cell*328u+lane]-low[cell*328u+108u+lane])-control[c+2u]*jac[j+lane*55u+54u]-control[c+2u]*low[cell*328u+271u+lane];');
 controller=controller.replace('r=jac[j+54u]-control[c+3u];','r=(jac[j+54u]-control[c+3u])+(low[cell*328u+270u]-low[cell*328u+271u]);');
 controller=controller.replace('control[c+3u]=jac[j+54u];','control[c+3u]=jac[j+54u];low[cell*328u+271u]=low[cell*328u+270u];');
 controller=controller.replace('abs(jac[j+54u]-control[c+3u])','abs((jac[j+54u]-control[c+3u])+(low[cell*328u+270u]-low[cell*328u+271u]))');
 controller=controller.replace('((value-referenceState)/et)',
  '(((value-referenceState)+(low[cell*328u+lane]-low[cell*328u+216u+lane]))/et)').replace('((value-referenceState)/et)',
  '(((value-referenceState)+(low[cell*328u+lane]-low[cell*328u+216u+lane]))/et)');
 controller=controller.replace('work[w+162u+i]=states[o+i];states[o+i]=work[w+i];work[w+54u+i]=work[w+i];',
  'work[w+162u+i]=states[o+i];low[cell*328u+216u+i]=low[cell*328u+i];states[o+i]=work[w+i];work[w+54u+i]=work[w+i];low[cell*328u+i]=low[cell*328u+54u+i];low[cell*328u+108u+i]=low[cell*328u+54u+i];');
 controller=controller.replace('states[o+i]=work[w+i];work[w+54u+i]=work[w+i];',
  'states[o+i]=work[w+i];work[w+54u+i]=work[w+i];low[cell*328u+i]=low[cell*328u+54u+i];low[cell*328u+108u+i]=low[cell*328u+54u+i];');
 controller=controller.replace('work[w+54u+i]=states[o+i];}control[c+9u]=2.;',
  'work[w+54u+i]=states[o+i];low[cell*328u+108u+i]=low[cell*328u+i];}control[c+9u]=2.;');
 controller=controller.replace('work[w+i]=states[o+i];work[w+54u+i]=states[o+i];',
  'work[w+i]=states[o+i];work[w+54u+i]=states[o+i];low[cell*328u+54u+i]=low[cell*328u+i];low[cell*328u+108u+i]=low[cell*328u+i];');
 controller=controller.replace('work[w+108u+i]=states[o+i];',
  'work[w+108u+i]=states[o+i];low[cell*328u+162u+i]=low[cell*328u+i];');
 controller=controller.replace('trajectory[(cell*u32(schedule[1])+sample)*54u+i]=states[o+i];',
  'trajectory[(cell*u32(schedule[1])+sample)*54u+i]=states[o+i];trajectory[u32(schedule[0])*u32(schedule[1])*54u+(cell*u32(schedule[1])+sample)*54u+i]=low[cell*328u+i];');
 let update=tileApply+binding+helpers;
 update=update.replace('let raw=work[w+108u+lane]+alphas[0]*work[w+216u+lane];',
  'let first=stateSum(work[w+108u+lane],alphas[0]*work[w+216u+lane]);let pair=stateSum(first.hi,first.lo+low[g.x*328u+162u+lane]);let raw=pair.hi;');
 update=update.replace('states[o+lane]=value;',
  'states[o+lane]=value;low[g.x*328u+lane]=select(pair.lo,0.,lane>0u&&raw<0.);');
 return {lu:withEnergy,controller,update};
}
