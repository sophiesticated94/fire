fn pressure(id:u32,r:ptr<storage,array<f32>,read_write>,rhs:ptr<storage,array<f32>,read_write>,p:ptr<storage,array<f32>,read_write>,colour:u32)->void {
 if(id>=NC){return;}let q=xyz(id);if(u32(q.x+q.y+q.z)%2u!=colour){return;}
 let a=lap(p,r,q);let solved=(a.x-(*rhs)[id])/a.y;(*p)[id]=mix((*p)[id],solved,1.8);
}
