export const AIR={p:101325,R:287.05,cp:1005,T:293.15,mu:1.81e-5,k:.0257,g:9.81};
export interface GpuFlowConfig {power:number;wind:number;ambient:number;gravity:number;viscosity:number;thermalConductivity:number}
export interface GridOptions {cells?:[number,number,number];mu?:number;k?:number;gravity?:number;testReadback?:boolean;ambient?:number;pressureMode?:'reference'|'batched'}
// Measured on the target RTX 4050; other devices/grids retain the reference.
// The reference remains explicitly selectable for regression and benchmarking.
export function defaultPressureMode(adapter:{vendor:string;device:string},cells:readonly number[]){
  return adapter.vendor==='nvidia'&&adapter.device==='0x28a1'&&cells.join(',')==='32,32,64'?'batched' as const:'reference' as const;
}
export class GpuGrid {
  cells:[number,number,number];size:[number,number,number]=[.16,.16,.32];h:number[];count:number;faces:number;offsets:number[];weights:Float32Array;normalization:number;
  constructor(public options:GridOptions={}){
    this.cells=[...(options.cells??[32,32,64])] as [number,number,number];
    if(this.cells.length!==3||this.cells.some(n=>!Number.isInteger(n)||n<4||n>64))throw Error('Niepoprawna siatka GPU');
    if([options.mu??AIR.mu,options.k??AIR.k,options.gravity??AIR.g].some(v=>!Number.isFinite(v)||v<0))throw Error('Niepoprawne właściwości powietrza');
    if(!Number.isFinite(options.ambient??20)||(options.ambient??20)<0||(options.ambient??20)>50)throw Error('Temperatura otoczenia poza zakresem 0–50 °C');
    if(options.pressureMode!==undefined&&!['reference','batched'].includes(options.pressureMode))throw Error('Nieznany wariant projekcji ciśnienia');
    const [x,y,z]=this.cells;this.count=x*y*z;this.h=this.size.map((s,i)=>s/this.cells[i]);
    this.offsets=[0,(x+1)*y*z,(x+1)*y*z+x*(y+1)*z];this.faces=this.offsets[2]+x*y*(z+1);
    this.weights=new Float32Array(this.count);let sum=0;
    for(let k=0;k<z;k++)for(let j=0;j<y;j++)for(let i=0;i<x;i++){
      const r=((i+.5)*this.h[0]-.08)**2+((j+.5)*this.h[1]-.08)**2;
      const w=Math.exp(-r/(2*.01**2)-((k+.5)*this.h[2]-.015)**2/(2*.005**2));
      this.weights[this.index(i,j,k)]=w;sum+=w*this.volume;
    }
    this.normalization=sum;
  }
  get volume(){return this.h.reduce((a,b)=>a*b,1)}
  ambientKelvin=AIR.T;
  get ambientDensity(){return AIR.p/(AIR.R*this.ambientKelvin)}
  index(i:number,j:number,k:number){return (k*this.cells[1]+j)*this.cells[0]+i}
  faceIndex(a:number,i:number,j:number,k:number){const d=this.cells.map((n,b)=>n+Number(a===b));return this.offsets[a]+(k*d[1]+j)*d[0]+i}
  wgsl(){const [x,y,z]=this.cells;return `
const N=vec3i(${x},${y},${z}); const H=vec3f(${this.h.map(v=>v.toPrecision(12)).join(',')});
const NC:u32=${this.count}u; const NF:u32=${this.faces}u; const DV:f32=${this.volume.toPrecision(12)};
var<private> R0:f32; var<private> T0:f32; var<private> GRAV:f32; var<private> MU:f32; var<private> KT:f32; var<private> TREF:f32; var<private> BATH:f32;
const GAS:f32=287.05; const P0:f32=101325.; const CP:f32=1005.;
const WN:f32=${this.normalization.toPrecision(12)};
fn cell(q:vec3i)->u32 {let p=clamp(q,vec3i(0),N-vec3i(1));return u32((p.z*N.y+p.y)*N.x+p.x);}
fn xyz(id:u32)->vec3i{return vec3i(i32(id)%N.x,(i32(id)/N.x)%N.y,i32(id)/(N.x*N.y));}
fn unit(a:i32)->vec3i {var e=vec3i(0);e[a]=1;return e;}
fn dims(a:i32)->vec3i {return N+unit(a);}
fn off(a:i32)->u32 {if(a==0){return 0u;}if(a==1){return u32((N.x+1)*N.y*N.z);}return u32((N.x+1)*N.y*N.z+N.x*(N.y+1)*N.z);}
fn fi(a:i32,q:vec3i)->u32 {let d=dims(a);let p=clamp(q,vec3i(0),d-vec3i(1));return off(a)+u32((p.z*d.y+p.y)*d.x+p.x);}
fn face(id:u32)->vec4i {var a=0;if(id>=off(2)){a=2;}else if(id>=off(1)){a=1;}let d=dims(a);let v=i32(id-off(a));return vec4i(v%d.x,(v/d.x)%d.y,v/(d.x*d.y),a);}
fn density(r:ptr<storage,array<f32>,read_write>,q:vec3i)->f32 {if(any(q<vec3i(0))||any(q>=N)){return R0;}return (*r)[cell(q)];}
fn temp(r:ptr<storage,array<f32>,read_write>,q:vec3i)->f32{return P0/(GAS*density(r,q));}
fn vel(v:ptr<storage,array<f32>,read_write>,a:i32,q:vec3i)->f32 {if(a==2&&q.z<=0){return 0.;}return (*v)[fi(a,q)];}
fn div(v:ptr<storage,array<f32>,read_write>,q:vec3i)->f32 {var d=0.;for(var a=0;a<3;a++){d+=(vel(v,a,q+unit(a))-vel(v,a,q))/H[a];}return d;}
fn mass(r:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,a:i32,q:vec3i)->f32 {let u=vel(v,a,q);return u*select(density(r,q),density(r,q-unit(a)),u>=0.);}
fn beta(r:ptr<storage,array<f32>,read_write>,a:i32,q:vec3i)->f32 {return 2./(density(r,q)+density(r,q-unit(a)));}
fn rf(r:ptr<storage,array<f32>,read_write>,a:i32,q:vec3i)->f32{return 1./beta(r,a,q);}
fn weight(q:vec3i)->f32 {let p=(vec3f(q)+.5)*H;return exp(-dot(p.xy-vec2f(.08),p.xy-vec2f(.08))/(2.*.01*.01)-(p.z-.015)*(p.z-.015)/(2.*.005*.005))/WN;}
fn tghost(r:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,q:vec3i,a:i32,s:i32)->f32 {
 let n=q+unit(a)*s;if(n[a]>=0&&n[a]<N[a]){return temp(r,n);}if(a==2&&s<0){return temp(r,q);}
 let f=q+unit(a)*select(0,1,s>0);if(vel(v,a,f)*f32(s)<0.){return T0;}return temp(r,q);
}
fn coeff(r:ptr<storage,array<f32>,read_write>,q:vec3i,a:i32,s:i32)->f32 {
 if(a==2&&s<0&&q.z==0){return 0.;}let f=q+unit(a)*select(0,1,s>0);let outside=q[a]+s<0||q[a]+s>=N[a];
 return beta(r,a,f)*select(1.,2.,outside)/(H[a]*H[a]);
}
fn lap(p:ptr<storage,array<f32>,read_write>,r:ptr<storage,array<f32>,read_write>,q:vec3i)->vec2f {
 var sum=0.;var diag=0.;for(var a=0;a<3;a++){for(var s=-1;s<=1;s+=2){let c=coeff(r,q,a,s);diag+=c;let n=q+unit(a)*s;if(all(n>=vec3i(0))&&all(n<N)){sum+=c*(*p)[cell(n)];}}}return vec2f(sum,diag);
}
`}
}
