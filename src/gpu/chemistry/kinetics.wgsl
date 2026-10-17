// Forward-mode analytical differentiation. No finite differences in production.
// Species concentrations: kmol/m³; molecular weights: kg/kmol; enthalpy: J/kg.
fn mul(a:vec2f,b:vec2f)->vec2f{return vec2f(a.x*b.x,a.y*b.x+a.x*b.y);}
fn inv(a:vec2f)->vec2f{return vec2f(1./a.x,-a.y/(a.x*a.x));}
fn ln(a:vec2f)->vec2f{return vec2f(log(a.x),a.y/a.x);}
fn ex(a:vec2f)->vec2f{let v=exp(a.x);return vec2f(v,v*a.y);}
fn arr(base:u32,t:vec2f)->vec2f{return vec2f(mechanism[base],0.)+ln(t)*mechanism[base+1u]-inv(t)*mechanism[base+2u];}

fn mass_action(logk:vec2f,c:ptr<function,array<vec2f,53>>,start:u32,count:u32)->vec2f {
 var sum=logk;var zeroes=0u;var derivative=0.;
 for(var j=0u;j<count;j++){let index=u32(mechanism[start+2u*j]);let order=mechanism[start+2u*j+1u];let value=(*c)[index];
  if(value.x<=0.){zeroes+=u32(order);derivative=value.y;}else{sum+=ln(value)*order;}
 }
 if(zeroes>1u){return vec2f(0.);}if(zeroes==1u){if(derivative==0.){return vec2f(0.);}return vec2f(0.,exp(sum.x)*derivative);}
 return ex(sum);
}

fn evaluate(cell:u32,seed:i32)->array<vec2f,54> {
 let offset=cell*54u;let t=vec2f(states[offset],select(0.,1.,seed==0));
 var y:array<vec2f,53>;var c:array<vec2f,53>;var h:array<vec2f,53>;var g:array<vec2f,53>;var omega:array<vec2f,53>;var compensation:array<vec2f,53>;
 var total=vec2f(0.);for(var i=0u;i<53u;i++){y[i]=vec2f(states[offset+i+1u],select(0.,1.,seed==i32(i)+1));total+=y[i];}
 var molecular=vec2f(0.);var cp=vec2f(0.);
 for(var i=0u;i<53u;i++){
  y[i]=mul(y[i],inv(total));molecular+=y[i]/mechanism[4u+i];
  let base=57u+i*15u;let a=base+1u+select(0u,7u,t.x>=mechanism[base]);let a0=mechanism[a];
  let t2=mul(t,t);let t3=mul(t2,t);let t4=mul(t3,t);
  let cpr=vec2f(a0,0.)+t*mechanism[a+1u]+t2*mechanism[a+2u]+t3*mechanism[a+3u]+t4*mechanism[a+4u];
  let hrt=vec2f(a0,0.)+t*(mechanism[a+1u]/2.)+t2*(mechanism[a+2u]/3.)+t3*(mechanism[a+3u]/4.)+t4*(mechanism[a+4u]/5.)+inv(t)*mechanism[a+5u];
  let sr=ln(t)*a0+t*mechanism[a+1u]+t2*(mechanism[a+2u]/2.)+t3*(mechanism[a+3u]/3.)+t4*(mechanism[a+4u]/4.)+vec2f(mechanism[a+6u],0.);
  g[i]=hrt-sr;h[i]=mul(hrt,t)*(mechanism[2]/mechanism[4u+i]);cp+=mul(y[i],cpr)*(mechanism[2]/mechanism[4u+i]);omega[i]=vec2f(0.);compensation[i]=vec2f(0.);
 }
 let rho=inv(mul(molecular,t))*(mechanism[3]/mechanism[2]);
 for(var i=0u;i<53u;i++){c[i]=mul(rho,y[i])/mechanism[4u+i];}
 for(var reaction=0u;reaction<325u;reaction++){
  let base=852u+reaction*112u;let kind=u32(mechanism[base]);var logkf=arr(base+4u,t);
  if(kind>0u){var third=vec2f(0.);for(var i=0u;i<53u;i++){third+=c[i]*mechanism[base+33u+i];}
   if(third.x<=0.){continue;}
   if(kind==1u){logkf+=ln(third);}else{
    let logpr=arr(base+7u,t)+ln(third)-logkf;let pr=ex(logpr);logkf+=logpr-ln(vec2f(1.,0.)+pr);
    if(kind==2u){let alpha=mechanism[base+10u];var fc=ex(-t/mechanism[base+11u])*(1.-alpha)+ex(-t/mechanism[base+12u])*alpha;
     if(mechanism[base+13u]>0.){fc+=ex(inv(t)*(-mechanism[base+13u]));}
     let lf=ln(fc)/log(10.);let cc=vec2f(-.4,0.)-.67*lf;let nn=vec2f(.75,0.)-1.27*lf;let xx=logpr/log(10.)+cc;let f=mul(xx,inv(nn-.14*xx));
     logkf+=mul(lf,inv(vec2f(1.,0.)+mul(f,f)))*log(10.);
    }
   }
  }
  var logkc=vec2f(0.);var dn=0.;let net=u32(mechanism[base+102u]);
  for(var j=0u;j<net;j++){let i=u32(mechanism[base+86u+2u*j]);let nu=mechanism[base+87u+2u*j];logkc-=g[i]*nu;dn+=nu;}
  logkc+=ln(inv(t)*(mechanism[3]/mechanism[2]))*dn;
  var progress=mass_action(logkf,&c,base+15u,u32(mechanism[base+2u]));
  if(mechanism[base+1u]>.5){progress-=mass_action(logkf-logkc,&c,base+21u,u32(mechanism[base+3u]));}
  for(var j=0u;j<net;j++){let i=u32(mechanism[base+86u+2u*j]);let nu=mechanism[base+87u+2u*j];let addition=progress*(nu*mechanism[4u+i])-compensation[i];let sum=omega[i]+addition;compensation[i]=(sum-omega[i])-addition;omega[i]=sum;}
 }
 var result:array<vec2f,54>;var heat=vec2f(0.);var heatCompensation=vec2f(0.);
 for(var i=0u;i<53u;i++){result[i+1u]=mul(omega[i],inv(rho));let addition=mul(h[i],omega[i])-heatCompensation;let sum=heat+addition;heatCompensation=(sum-heat)-addition;heat=sum;}
 result[0]=-mul(heat,inv(mul(rho,cp)));return result;
}
