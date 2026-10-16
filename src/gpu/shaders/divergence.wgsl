fn divergence(id:u32,v:ptr<storage,array<f32>,read_write>,s:ptr<storage,array<f32>,read_write>,rhs:ptr<storage,array<f32>,read_write>)->void {
 if(id>=NC){return;}(*rhs)[id]=div(v,xyz(id))-(*s)[2u*id];
}
