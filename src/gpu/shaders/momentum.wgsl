fn momentum(id:u32,r:ptr<storage,array<f32>,read_write>,next:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>,par:vec4f)->void {
 if(id>=NF){return;}let f=face(id);let q=f.xyz;let c=f.w;
 if(c==2&&q.z==0){(*out)[id]=0.;return;}
 let u=vel(v,c,q);if(q[c]==0||q[c]==N[c]){(*out)[id]=u;return;}
 var transport=0.;var diffusion=0.;
 for(var a=0;a<3;a++){
  let e=unit(a);let plus=.5*(mass(r,v,a,q+e)+mass(r,v,a,q+e-unit(c)));
  let minus=.5*(mass(r,v,a,q)+mass(r,v,a,q-unit(c)));
  transport+=(plus*select(vel(v,c,q+e),u,plus>=0.)-minus*select(u,vel(v,c,q-e),minus>=0.))/H[a];
  diffusion+=(vel(v,c,q+e)+vel(v,c,q-e)-2.*u)/(H[a]*H[a]);
 }
 diffusion+=(div(v,q)-div(v,q-unit(c)))/(3.*H[c]);
 let body=select(0.,GRAV*(R0-rf(r,c,q)),c==2);
 (*out)[id]=(rf(r,c,q)*u+par.x*(-transport+MU*diffusion+body))/rf(next,c,q);
}
