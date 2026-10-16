fn advect(id:u32,r:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>,par:vec4f)->void {
 if(id>=NC){return;}let q=xyz(id);var flux=0.;for(var a=0;a<3;a++){flux+=(mass(r,v,a,q+unit(a))-mass(r,v,a,q))/H[a];}
 (*out)[id]=(*r)[id]-par.x*flux;
}
