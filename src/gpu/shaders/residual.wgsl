fn residual(group:u32,r:ptr<storage,array<f32>,read_write>,rhs:ptr<storage,array<f32>,read_write>,p:ptr<storage,array<f32>,read_write>,s:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>,m:ptr<storage,array<f32>,read_write>)->void {
 let first=group*64u;if(first>=NC||(*m)[24]>0.){return;}var rr=0.;var bb=0.;var net=0.;var expansion=0.;var maximum=0.;
 for(var id=first;id<min(first+64u,NC);id++){
 let a=lap(p,r,xyz(id));let e=a.x-a.y*(*p)[id]-(*rhs)[id];rr+=e*e;bb+=(*rhs)[id]*(*rhs)[id];net+=e*DV;expansion+=abs((*s)[2u*id])*DV;maximum=max(maximum,abs(e));
 }
 for(var j=0u;j<24u;j++){(*out)[group*24u+j]=0.;}
 (*out)[group*24u]=rr;(*out)[group*24u+1u]=bb;(*out)[group*24u+2u]=net;(*out)[group*24u+3u]=expansion;(*out)[group*24u+4u]=maximum;
}
