fn project(id:u32,r:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,p:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>)->void {
 if(id>=NF){return;}let f=face(id);let q=f.xyz;let a=f.w;if(a==2&&q.z==0){(*out)[id]=0.;return;}
 var grad=0.;if(q[a]==0){grad=2.*(*p)[cell(q)]/H[a];}else if(q[a]==N[a]){grad=-2.*(*p)[cell(q-unit(a))]/H[a];}else{grad=((*p)[cell(q)]-(*p)[cell(q-unit(a))])/H[a];}
 (*out)[id]=vel(v,a,q)-beta(r,a,q)*grad;
}
