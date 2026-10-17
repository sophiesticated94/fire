fn diagnostics(group:u32,r:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,s:ptr<storage,array<f32>,read_write>,old:ptr<storage,array<f32>,read_write>,transport:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>)->void {
 let first=group*64u;if(first>=NC){return;}var z:array<f32,24>;for(var j=0u;j<24u;j++){z[j]=0.;}
 for(var id=first;id<min(first+64u,NC);id++){
 let q=xyz(id);let den=(*r)[id];let t=P0/(GAS*den);var u=vec3f(0.);var cfl=0.;
 for(var a=0;a<3;a++){u[a]=.5*(vel(v,a,q)+vel(v,a,q+unit(a)));z[9+i32(a)]=max(z[9+i32(a)],max(abs(vel(v,a,q)),abs(vel(v,a,q+unit(a)))));cfl+=max(0.,vel(v,a,q+unit(a)))/H[a]+max(0.,-vel(v,a,q))/H[a];}
 let err=div(v,q)-(*s)[2u*id];z[0]+=den*DV;z[1]+=den*CP*(t-TREF)*DV;z[2]+=err*err;z[3]+=dot(u,u);z[4]=max(z[4],abs(err));z[5]=max(z[5],length(u));z[6]=max(z[6],t);z[7]=max(z[7],1./den);z[8]=max(z[8],den);z[12]=max(z[12],cfl);
 if(!(den>0.)||!(t>=200.&&t<=1000.)||any(abs(u)>vec3f(1000.))){z[13]+=1.;}
 z[20]=max(z[20],abs(den*GAS*t/P0-1.));
 z[23]+=den*CP*BATH*DV;z[14]+=(*s)[2u*id+1u]*DV;z[15]+=(*s)[2u*id]*DV;z[21]=max(z[21],abs((*s)[2u*id]));z[22]+=abs((*s)[2u*id])*DV;
 for(var a=0;a<3;a++){for(var side=-1;side<=1;side+=2){if(q[a]!=select(0,N[a]-1,side>0)){continue;}if(a==2&&side<0){continue;}
  let f=q+unit(a)*select(0,1,side>0);let area=DV/H[a];let flux=f32(side)*mass(old,transport,a,f)*area;let un=f32(side)*vel(transport,a,f);let td=select(temp(old,q),T0,un<0.);
  z[16]+=flux;z[17]+=flux*CP*(td-TREF);
  z[18]+=KT*(temp(old,q)-select(temp(old,q),T0,un<0.))/H[a]*area;
  z[19]+=f32(side)*vel(v,a,f)*area;
 }}
 }
 for(var j=0u;j<24u;j++){(*out)[group*24u+j]=z[j];}
}
