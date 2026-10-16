fn thermal(id:u32,r:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,s:ptr<storage,array<f32>,read_write>,par:vec4f)->void {
 if(id>=NC){return;}let q=xyz(id);let t=temp(r,q);var conduction=0.;
 for(var a=0;a<3;a++){conduction+=KT*(tghost(r,v,q,a,-1)+tghost(r,v,q,a,1)-2.*t)/(H[a]*H[a]);}
 let heat=par.y*weight(q);(*s)[2u*id]=(conduction+heat)*GAS/(P0*CP);(*s)[2u*id+1u]=heat;
}
