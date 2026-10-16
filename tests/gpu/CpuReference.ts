// Float64 finite-volume reference. Pressure is solved with independent matrix-free
// conjugate gradients, not the GPU red/black relaxation implementation.
export class CpuReference {
 readonly p=101325;readonly R=287.05;readonly cp=1005;readonly T0=293.15;readonly rho0=this.p/(this.R*this.T0);
 rho:Float64Array;v:Float64Array;source:Float64Array;h:number[];count:number;faces:number;offset:number[];weights:Float64Array;
 constructor(readonly cells=[8,8,16],readonly gravity=9.81,readonly k=.0257,readonly mu=1.81e-5,public power=1,public wind=0){
  const [x,y,z]=cells;this.count=x*y*z;this.h=[.16/x,.16/y,.32/z];this.offset=[0,(x+1)*y*z,(x+1)*y*z+x*(y+1)*z];this.faces=this.offset[2]+x*y*(z+1);
  this.rho=new Float64Array(this.count).fill(this.rho0);this.v=new Float64Array(this.faces);this.source=new Float64Array(this.count);this.weights=new Float64Array(this.count);let norm=0;
  this.eachCell((q,id)=>{const [i,j,k]=q;const w=Math.exp(-(((i+.5)*this.h[0]-.08)**2+((j+.5)*this.h[1]-.08)**2)/(2*.01**2)-((k+.5)*this.h[2]-.015)**2/(2*.005**2));this.weights[id]=w;norm+=w*this.h.reduce((a,b)=>a*b,1);});this.weights=this.weights.map(w=>w/norm);
  this.eachFace((a,q,id)=>{if(a===0)this.v[id]=wind;});this.thermal();this.v=this.project(this.v);
 }
 index(q:number[]){return(q[2]*this.cells[1]+q[1])*this.cells[0]+q[0]}
 outside(q:number[]){return q.some((n,a)=>n<0||n>=this.cells[a])}
 shift(q:number[],a:number,s:number){const p=[...q];p[a]+=s;return p}
 eachCell(fn:(q:number[],id:number)=>void){for(let z=0;z<this.cells[2];z++)for(let y=0;y<this.cells[1];y++)for(let x=0;x<this.cells[0];x++)fn([x,y,z],this.index([x,y,z]));}
 eachFace(fn:(a:number,q:number[],id:number)=>void){for(let a=0;a<3;a++){const d=this.cells.map((n,b)=>n+Number(a===b));for(let z=0;z<d[2];z++)for(let y=0;y<d[1];y++)for(let x=0;x<d[0];x++)fn(a,[x,y,z],this.faceIndex(a,[x,y,z]));}}
 faceIndex(a:number,q:number[]){const d=this.cells.map((n,b)=>n+Number(a===b)),p=q.map((n,b)=>Math.min(d[b]-1,Math.max(0,n)));return this.offset[a]+(p[2]*d[1]+p[1])*d[0]+p[0]}
 density(r:Float64Array,q:number[]){return this.outside(q)?this.rho0:r[this.index(q)]}
 velocity(v:Float64Array,a:number,q:number[]){return a===2&&q[2]<=0?0:v[this.faceIndex(a,q)]}
 flux(r:Float64Array,v:Float64Array,a:number,q:number[]){const u=this.velocity(v,a,q);return u*this.density(r,u>=0?this.shift(q,a,-1):q)}
 faceDensity(r:Float64Array,a:number,q:number[]){return(this.density(r,q)+this.density(r,this.shift(q,a,-1)))*.5}
 div(v:Float64Array,q:number[]){return this.h.reduce((s,h,a)=>s+(this.velocity(v,a,this.shift(q,a,1))-this.velocity(v,a,q))/h,0)}
 temperature(q:number[]){return this.p/(this.R*this.density(this.rho,q))}
 thermal(){this.eachCell((q,id)=>{const t=this.temperature(q);let heat=this.power*this.weights[id];for(let a=0;a<3;a++)for(const side of [-1,1]){const adj=this.shift(q,a,side);let tn=this.temperature(adj);if(this.outside(adj)){const inflow=side*this.velocity(this.v,a,side<0?q:this.shift(q,a,1))<0;tn=a===2&&side<0?t:inflow?this.T0:t;}heat+=this.k*(tn-t)/(this.h[a]**2);}this.source[id]=heat*this.R/(this.p*this.cp);});}
 project(v:Float64Array){
  const rows:{id:number;w:number}[][]=Array.from({length:this.count},()=>[]),diag=new Float64Array(this.count),b=new Float64Array(this.count);
  this.eachCell((q,id)=>{b[id]=this.source[id]-this.div(v,q);for(let a=0;a<3;a++)for(const side of [-1,1]){if(a===2&&q[2]===0&&side<0)continue;const adj=this.shift(q,a,side),outside=this.outside(adj);const f=side<0?q:this.shift(q,a,1);const w=(outside?2:1)/(this.faceDensity(this.rho,a,f)*this.h[a]**2);diag[id]+=w;if(!outside)rows[id].push({id:this.index(adj),w});}});
  const apply=(x:Float64Array)=>x.map((v,i)=>diag[i]*v-rows[i].reduce((s,n)=>s+n.w*x[n.id],0));const dot=(a:Float64Array,b:Float64Array)=>a.reduce((s,v,i)=>s+v*b[i],0);
  const x=new Float64Array(this.count);let r=b.slice(),d=r.slice(),rr=dot(r,r);
  for(let it=0;it<4000&&rr>1e-22;it++){const ad=apply(d),alpha=rr/dot(d,ad);for(let i=0;i<this.count;i++){x[i]+=alpha*d[i];r[i]-=alpha*ad[i];}const next=dot(r,r),beta=next/rr;for(let i=0;i<this.count;i++)d[i]=r[i]+beta*d[i];rr=next;}
  const out=v.slice();this.eachFace((a,q,id)=>{if(a===2&&q[2]===0){out[id]=0;return;}const left=this.shift(q,a,-1);const pl=this.outside(left)?0:x[this.index(left)],pr=this.outside(q)?0:x[this.index(q)];const factor=this.outside(left)||this.outside(q)?2:1;out[id]=v[id]-factor*(pr-pl)/(this.h[a]*this.faceDensity(this.rho,a,q));});return out;
 }
 step(dt=1/120){const old=this.rho,transport=this.v;const next=old.slice();this.eachCell((q,id)=>{let net=0;for(let a=0;a<3;a++)net+=(this.flux(old,transport,a,this.shift(q,a,1))-this.flux(old,transport,a,q))/this.h[a];next[id]=old[id]-dt*net;});const velocity=transport.slice();
  this.eachFace((c,q,id)=>{if(c===2&&q[2]===0){velocity[id]=0;return;}if(q[c]===0||q[c]===this.cells[c])return;const u=this.velocity(transport,c,q);let adv=0,diff=0;for(let a=0;a<3;a++){const plusQ=this.shift(q,a,1),minusQ=this.shift(q,a,-1);const plus=.5*(this.flux(old,transport,a,plusQ)+this.flux(old,transport,a,this.shift(plusQ,c,-1))),minus=.5*(this.flux(old,transport,a,q)+this.flux(old,transport,a,this.shift(q,c,-1)));adv+=(plus*(plus>=0?u:this.velocity(transport,c,plusQ))-minus*(minus>=0?this.velocity(transport,c,minusQ):u))/this.h[a];diff+=(this.velocity(transport,c,plusQ)+this.velocity(transport,c,minusQ)-2*u)/this.h[a]**2;}diff+=(this.div(transport,q)-this.div(transport,this.shift(q,c,-1)))/(3*this.h[c]);const rho=this.faceDensity(old,c,q),body=c===2?this.gravity*(this.rho0-rho):0;velocity[id]=(rho*u+dt*(-adv+this.mu*diff+body))/this.faceDensity(next,c,q);});
  this.rho=next;this.v=velocity;this.thermal();this.v=this.project(this.v);
 }
}
