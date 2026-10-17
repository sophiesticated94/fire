fn convergence(id:u32,m:ptr<storage,array<f32>,read_write>)->void {
 if(id!=0u||(*m)[24]>0.){return;}
 (*m)[25]+=16.;
 let rms=sqrt((*m)[0]/f32(NC));let rhs=sqrt((*m)[1]/f32(NC));
 if(rms<=max(1e-4,1e-3*rhs)&&abs((*m)[2])<=.01*max((*m)[3],1e-8)){(*m)[24]=1.;}
}
