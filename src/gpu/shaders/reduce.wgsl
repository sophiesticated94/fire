fn reduce(slot:u32,parts:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>,mode:u32)->void {
 if(slot>=24u){return;}var value=0.;let isMax=select(slot==4u,slot==4u||slot==5u||slot==6u||slot==7u||slot==8u||slot==9u||slot==10u||slot==11u||slot==12u||slot==20u||slot==21u,mode==1u);
 for(var g=0u;g<(NC+63u)/64u;g++){let x=(*parts)[g*24u+slot];if(isMax){value=max(value,x);}else{value+=x;}}
 (*out)[slot]=value;
}
