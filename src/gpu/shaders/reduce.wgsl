fn reduce(slot:u32,parts:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>,mode:u32)->void {
 if(slot>=24u){return;}var value=0.;var correction=0.;let isMax=select(slot==4u,slot==4u||slot==5u||slot==6u||slot==7u||slot==8u||slot==9u||slot==10u||slot==11u||slot==12u||slot==20u||slot==21u,mode==1u);
 // Statistics span 1024 partial sums on the full grid. Plain float32 sums
 // can falsely trip conservation guards during uniform volume heating.
 // Pressure reduction (mode=0) retains the measured reference arithmetic.
 for(var g=0u;g<(NC+63u)/64u;g++){let x=(*parts)[g*24u+slot];if(isMax){value=max(value,x);}else if(mode==1u){let delta=x-correction;let total=value+delta;correction=(total-value)-delta;value=total;}else{value+=x;}}
 (*out)[slot]=value;
}
