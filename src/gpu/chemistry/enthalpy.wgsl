fn enthalpy(cell:u32,seed:i32)->vec2f {
 let offset=cell*54u;let t=vec2f(states[offset],select(0.,1.,seed==0));var sum=vec2f(0.);var h=vec2f(0.);
 for(var i=0u;i<53u;i++){
  let y=vec2f(states[offset+i+1u],select(0.,1.,seed==i32(i)+1));sum+=y;
  let base=57u+i*15u;let a=base+1u+select(0u,7u,t.x>=mechanism[base]);let t2=mul(t,t);let t3=mul(t2,t);let t4=mul(t3,t);
  let ht=vec2f(mechanism[a],0.)+t*(mechanism[a+1u]/2.)+t2*(mechanism[a+2u]/3.)+t3*(mechanism[a+3u]/4.)+t4*(mechanism[a+4u]/5.)+inv(t)*mechanism[a+5u];
  h+=mul(y,mul(ht,t))*(mechanism[2]/mechanism[4u+i]);
 }return mul(h,inv(sum));
}
