/// <reference types="@webgpu/types" />
import {WebGPURenderer,Vector4} from 'three/webgpu';
import {wgslFn,uniform,instanceIndex,uint} from 'three/tsl';
import type {ComputeNode} from 'three/webgpu';
import {GpuGrid,AIR,type GridOptions,type GpuFlowConfig} from './GpuGrid';
import {GpuFields,Field} from './GpuFields';
import {finite,type GpuStepDiagnostics} from './GpuDiagnostics';
import thermal from './shaders/thermal.wgsl?raw';
import advect from './shaders/advect.wgsl?raw';
import momentum from './shaders/momentum.wgsl?raw';
import divergence from './shaders/divergence.wgsl?raw';
import pressure from './shaders/pressure.wgsl?raw';
import project from './shaders/project.wgsl?raw';
import residual from './shaders/residual.wgsl?raw';
import reduce from './shaders/reduce.wgsl?raw';
import diagnostics from './shaders/diagnostics.wgsl?raw';

export class GpuEngine {
  readonly timingScheme='per-pass-step-sum';
  readonly model='gpu-flow-0.1';grid:GpuGrid;fields:GpuFields;config:GpuFlowConfig={power:1,wind:0};
  state=0;velocity=0;time=0;steps=0;readbackBytes=0;fullReadbacks=0;paused=true;disposed=false;busy=false;error='';
  adapter:Record<string,unknown>={};metrics?:GpuStepDiagnostics;onMetrics?:(m:GpuStepDiagnostics)=>void;onError?:(error:string)=>void;
  readonly par=uniform(new Vector4(1/120,1,0,0));private kernels=new Map<string,ComputeNode>();private dirty=true;private pendingConfig=false;
  private device?:GPUDevice;private mass0=0;private energy0=0;private massIntegral=0;private energyIntegral=0;private lastMass=0;private lastEnergy=0;
  private accumulator=0;private lastFrame=0;private iterations=0;private timestamps=false;
  private appliedWind=0;
  private windDelta=uniform(0);private revision=0;private stepConfig?:GpuFlowConfig;suspended=false;
  private timestampIds:string[]=[];
  private deviceLost=false;
  private pendingProbe?:{index:number;resolve:(values:number[]|undefined)=>void};
  private constructor(public renderer:WebGPURenderer,options:GridOptions){this.grid=new GpuGrid(options);this.fields=new GpuFields(this.grid)}
  static async create(options:GridOptions={}){
    new GpuGrid(options); // Validate before allocating a GPU device.
    if(!navigator.gpu)throw Error('Ta przeglądarka nie udostępnia WebGPU. Ścieżka FDS pozostaje dostępna.');
    const adapter=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});
    if(!adapter)throw Error('Brak dostępnego adaptera WebGPU. Otwórz IGNIS w Chrome lub Edge z akceleracją sprzętową.');
    if(adapter.limits.maxStorageBuffersPerShaderStage<8)throw Error('Adapter ma za mało buforów storage (wymagane 8).');
    const features:GPUFeatureName[]=[];if(adapter.features.has('timestamp-query'))features.push('timestamp-query');
    if(adapter.features.has('core-features-and-limits'))features.push('core-features-and-limits');
    const device=await adapter.requestDevice({requiredFeatures:features,requiredLimits:{maxStorageBuffersPerShaderStage:8}});
    const renderer=new WebGPURenderer({device,trackTimestamp:features.includes('timestamp-query'),antialias:false});
    const engine=new GpuEngine(renderer,options);
    engine.device=device;
    try{
      const info=adapter.info;engine.adapter={vendor:info.vendor,architecture:info.architecture,device:info.device,description:info.description,isFallbackAdapter:info.isFallbackAdapter};
      await renderer.init();
      if(!(renderer.backend as unknown as {isWebGPUBackend?:boolean}).isWebGPUBackend)throw Error('Solver wymaga rzeczywistego backendu WebGPU.');
      engine.timestamps=features.includes('timestamp-query');
      engine.device.addEventListener('uncapturederror',e=>engine.fail((e as GPUUncapturedErrorEvent).error.message));
      engine.device.lost.then(info=>{if(!engine.disposed){engine.deviceLost=true;engine.fail(`Utrata urządzenia GPU: ${info.message}. Odśwież aplikację, aby utworzyć nowe urządzenie.`)}});
      await engine.reset();return engine;
    }catch(e){engine.dispose();throw e;}
  }
  get rho(){return this.fields.rho[this.state]}
  get flow(){return this.fields.velocity[this.velocity]}
  private kernel(key:string,source:string,count:number,args:Record<string,unknown>){
    if(!this.kernels.has(key)){
      const fn=wgslFn(source+'\n'+this.grid.wgsl());
      // Three's function-node typing cannot express arbitrary WGSL pointer arguments.
      const node=fn({id:instanceIndex,group:instanceIndex,slot:instanceIndex,...args} as never).compute(count,[64]);
      node.name=key;this.kernels.set(key,node);
    }
    return this.kernels.get(key)!;
  }
  private dispatch(nodes:ComputeNode|ComputeNode[]){
    this.renderer.compute(nodes);
    if(this.timestamps&&this.busy)this.timestampIds.push((this.renderer.backend as unknown as {getTimestampUID(n:unknown):string}).getTimestampUID(nodes));
  }
  private run(key:string,code:string,count:number,args:Record<string,unknown>){this.dispatch(this.kernel(key,code,count,args))}
  private async read(field:Field){const data=await this.renderer.getArrayBufferAsync(field.attribute);if(this.error)throw Error(this.error);this.readbackBytes+=field.count*4;const a=new Float32Array(data as ArrayBuffer);finite(a);return a;}
  setParameters(change:Partial<GpuFlowConfig>){
    const next={...this.config,...change};if(!Number.isFinite(next.power)||next.power<0||next.power>2||!Number.isFinite(next.wind)||next.wind<0||next.wind>.1)throw Error('Parametry GPU poza zakresem');
    if(next.power===this.config.power&&next.wind===this.config.wind)return;
    this.config=next;this.revision++;this.pendingConfig=true;this.dirty=true;
  }
  private uniforms(dt:number){const c=this.stepConfig??this.config;this.par.value.set(dt,c.power,c.wind,0)}
  private thermal(r:Field,v:Field){this.run(`thermal-${this.fields.rho.indexOf(r)}-${this.fields.velocity.indexOf(v)}`,thermal,this.grid.count,{r:r.node,v:v.node,s:this.fields.source.node,par:this.par})}
  private async solve(r:Field,v:Field,dest:Field){
    const f=this.fields,n=this.grid.count,groups=Math.ceil(n/64);
    const key=`${this.fields.rho.indexOf(r)}-${this.fields.velocity.indexOf(v)}-${this.fields.velocity.indexOf(dest)}`;
    this.run('rhs-'+key,divergence,n,{v:v.node,s:f.source.node,rhs:f.rhs.node});
    const red=this.kernel('red-'+key,pressure,n,{r:r.node,rhs:f.rhs.node,p:f.pressure.node,colour:uint(0)});
    const black=this.kernel('black-'+key,pressure,n,{r:r.node,rhs:f.rhs.node,p:f.pressure.node,colour:uint(1)});
    let it=0,converged=false;
    for(;it<1024;){
      this.dispatch(Array.from({length:16},()=>[red,black]).flat());it+=16;
      this.run('residual-'+key,residual,groups,{r:r.node,rhs:f.rhs.node,p:f.pressure.node,s:f.source.node,out:f.chunks.node});
      this.run('reduce-pressure',reduce,24,{parts:f.chunks.node,out:f.metrics.node,mode:uint(0)});
      const m=await this.read(f.metrics);const rms=Math.sqrt(m[0]/n),rhs=Math.sqrt(m[1]/n);
      if(rms<=Math.max(1e-4,1e-3*rhs)&&Math.abs(m[2])<=.01*Math.max(m[3],1e-8)){converged=true;break;}
    }
    this.iterations+=it;
    if(!converged)throw Error('Projekcja ciśnienia nie osiągnęła zbieżności (1024 iteracje).');
    this.run('project-'+key,project,this.grid.faces,{r:r.node,v:v.node,p:f.pressure.node,out:dest.node});
  }
  private async stats(r:Field,v:Field,old=r,transport=v){
    const f=this.fields,key=`${f.rho.indexOf(r)}-${f.velocity.indexOf(v)}-${f.rho.indexOf(old)}-${f.velocity.indexOf(transport)}`;
    this.run('stats-'+key,diagnostics,Math.ceil(this.grid.count/64),{r:r.node,v:v.node,s:f.source.node,old:old.node,transport:transport.node,out:f.chunks.node});
    this.run('reduce-stats',reduce,24,{parts:f.chunks.node,out:f.metrics.node,mode:uint(1)});
    return this.read(f.metrics);
  }
  private async prepare(){
    const c=this.stepConfig??this.config,revision=this.revision;
    let input=this.flow,outputIndex=(this.velocity+1)%3;
    if(this.appliedWind!==c.wind){
      this.windDelta.value=c.wind-this.appliedWind;
      input=this.fields.velocity[outputIndex];outputIndex=(this.velocity+2)%3;
      this.run(`wind-${this.velocity}`,`fn wind(id:u32,v:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>,change:f32)->void {if(id<NF){(*out)[id]=(*v)[id]+select(0.,change,id<off(1));}}`,this.grid.faces,{v:this.flow.node,out:input.node,change:this.windDelta});
    }
    this.uniforms(1/120);this.thermal(this.rho,input);const dest=this.fields.velocity[outputIndex];
    await this.solve(this.rho,input,dest);this.velocity=outputIndex;this.appliedWind=c.wind;this.dirty=this.revision!==revision;this.pendingConfig=this.dirty;
    const m=await this.stats(this.rho,this.flow);this.lastMass=m[0];this.lastEnergy=m[1];if(!this.mass0){this.mass0=m[0];this.energy0=m[1];}
    return m;
  }
  async reset(){
    if(this.busy)throw Error('Zaczekaj na zakończenie kroku GPU');
    if(this.disposed)throw Error('Silnik GPU został zwolniony');
    if(this.deviceLost)throw Error('Urządzenie GPU utracone. Odśwież aplikację.');
    this.busy=true;
    try{
    this.time=0;this.steps=0;this.error='';this.paused=true;this.accumulator=0;this.mass0=0;this.massIntegral=0;this.energyIntegral=0;this.state=0;this.velocity=0;this.iterations=0;
    for(const f of this.fields.all()){(f.attribute.array as Float32Array).fill(0);f.attribute.needsUpdate=true;}
    for(const r of this.fields.rho){(r.attribute.array as Float32Array).fill(this.grid.ambientDensity);r.attribute.needsUpdate=true;}
    for(const v of this.fields.velocity){(v.attribute.array as Float32Array).fill(0);const d=this.grid.cells;for(let k=0;k<d[2];k++)for(let j=0;j<d[1];j++)for(let i=0;i<=d[0];i++)(v.attribute.array as Float32Array)[this.grid.faceIndex(0,i,j,k)]=this.config.wind;v.attribute.needsUpdate=true;}
    this.appliedWind=this.config.wind;this.dirty=true;const m=await this.prepare();this.publish(m,0,0,null);
    }catch(e){this.fail((e as Error).message);throw e;}finally{this.busy=false;}
  }
  async step(maxDt=1/120){
    if(!Number.isFinite(maxDt)||maxDt<=0)throw Error('Krok czasu musi być dodatni');
    if(this.disposed||this.busy)throw Error('Silnik GPU nie jest gotowy');if(this.error)throw Error(this.error);
    this.busy=true;this.timestampIds=[];this.stepConfig={...this.config};const start=performance.now();this.iterations=0;
    try{
      let initial=this.dirty?await this.prepare():await this.stats(this.rho,this.flow);
      const h=this.grid.h;let dt=Math.min(maxDt,1/120,.5/Math.max(initial[12],1e-8),.05/Math.max(initial[21],1e-8));
      const alpha=Math.max(this.grid.options.mu??AIR.mu,(this.grid.options.k??AIR.k)/AIR.cp)*initial[7];
      dt=Math.min(dt,.45/(2*alpha*h.reduce((a,x)=>a+1/(x*x),0)));
      const old=this.rho,transport=this.flow;const next=this.fields.rho[1-this.state];const vi=(this.velocity+1)%3,oi=(this.velocity+2)%3;
      for(let trial=0;trial<4;trial++,dt*=.5){
        this.uniforms(dt);this.run(`advect-${this.state}-${this.velocity}`,advect,this.grid.count,{r:old.node,v:transport.node,out:next.node,par:this.par});
        this.run(`momentum-${this.state}-${this.velocity}`,momentum,this.grid.faces,{r:old.node,next:next.node,v:transport.node,out:this.fields.velocity[vi].node,par:this.par});
        // New thermodynamic state supplies the expansion target for the next transport.
        this.run(`thermal-next-${this.state}-${vi}`,thermal,this.grid.count,{r:next.node,v:this.fields.velocity[vi].node,s:this.fields.source.node,par:this.par});
        await this.solve(next,this.fields.velocity[vi],this.fields.velocity[oi]);
        const m=await this.stats(next,this.fields.velocity[oi],old,transport);
        if(m[13]||m[7]<=0||m[20]>1e-5||Math.hypot(m[9],m[10],m[11])/Math.sqrt(1.4*AIR.R*200)>=.1)throw Error('Stan gazu poza zakresem low-Mach (200–1000 K, Mach < 0,1, zgodność EOS).');
        if(m[12]*dt>.5*(1+1e-5))continue;
        const urms=Math.sqrt(m[3]/this.grid.count);const chi=Math.min(...h)*Math.sqrt(m[2]/this.grid.count)/Math.max(.01,urms);
        const maxChi=Math.min(...h)*m[4]/Math.max(.01,urms);
        if(chi>1e-3||maxChi>1e-2)throw Error(`Błąd rozszerzalności GPU: ${chi.toExponential(2)}`);
        const massStep=Math.abs(m[0]-this.lastMass+dt*m[16])/this.mass0;
        const massTotal=Math.abs(m[0]-this.mass0+this.massIntegral+dt*m[16])/this.mass0;
        if(massStep>1e-5||massTotal>1e-4)throw Error('Przekroczony błąd bilansu masy GPU.');
        if(Math.abs(m[19]-m[15])>.01*Math.max(m[22],1e-8))throw Error('Przekroczony błąd strumienia rozszerzalności GPU.');
        this.massIntegral+=dt*m[16];
        // Use the old state's heater/conduction integral and the actual transport fluxes.
        this.energyIntegral+=dt*(m[17]-initial[15]*AIR.p*AIR.cp/AIR.R);
        this.state=1-this.state;this.velocity=oi;this.time+=dt;this.steps++;
        let gpuMs:number|null=null;if(this.timestamps){
          await this.renderer.resolveTimestampsAsync('compute');
          // A step can span several animation frames. Three's info.timestamp reports
          // only the last frame, so sum this step's individual compute passes.
          const backend=this.renderer.backend as unknown as {hasTimestampQuery(id:string):boolean;getTimestamp(id:string):number};
          if(this.timestampIds.every(id=>backend.hasTimestampQuery(id)))gpuMs=this.timestampIds.reduce((sum,id)=>sum+backend.getTimestamp(id),0);
          this.readbackBytes+=this.timestampIds.length*16;
        }
        this.publish(m,dt,performance.now()-start,gpuMs);
        this.lastMass=m[0];this.lastEnergy=m[1];
        if(this.pendingConfig)this.dirty=true;
        return this.metrics!;
      }
      throw Error('CFL przekroczone mimo czterech prób zmniejszenia kroku.');
    }catch(e){this.fail((e as Error).message);throw e;}finally{
      this.busy=false;this.stepConfig=undefined;
      const pending=this.pendingProbe;this.pendingProbe=undefined;
      if(pending){try{pending.resolve(this.error||this.disposed?undefined:await this.probeAt(pending.index));}catch{pending.resolve(undefined);}}
    }
  }
  private publish(m:Float32Array,dt:number,wallMs:number,gpuMs:number|null){
    const n=this.grid.count,h=Math.min(...this.grid.h),urms=Math.sqrt(m[3]/n),norm=Math.max(.01,urms);
    this.metrics={time:this.time,dt,steps:this.steps,iterations:this.iterations,mass:m[0],enthalpy:m[1],temperature:m[6]-273.15,densityMin:1/m[7],densityMax:m[8],speed:m[5],cfl:dt*m[12],
      divergenceRms:Math.sqrt(m[2]/n),divergenceMax:m[4],normalizedDivergence:h*Math.sqrt(m[2]/n)/norm,normalizedMaximum:h*m[4]/norm,
      expansionFluxError:Math.abs(m[19]-m[15])/Math.max(m[22],1e-8),massError:dt?Math.abs(m[0]-this.lastMass+dt*m[16])/this.mass0:0,
      cumulativeMassError:Math.abs(m[0]-this.mass0+this.massIntegral)/this.mass0,energyError:m[1]-this.energy0+this.energyIntegral,heaterPower:m[14],gpuMs,wallMs,readbackBytes:this.readbackBytes,allocatedBytes:this.fields.bytes,adapter:this.adapter};
    this.onMetrics?.(this.metrics);
  }
  async advance(now:number){
    if(!this.lastFrame)this.lastFrame=now;const delta=Math.min(.1,(now-this.lastFrame)/1000);this.lastFrame=now;
    if(this.paused||this.suspended||document.hidden||this.busy||this.error){this.accumulator=0;return;}
    this.accumulator=Math.min(this.accumulator+delta,8/120);
    for(let i=0;i<8&&this.accumulator>1e-5&&!this.paused&&!this.suspended&&!document.hidden;i++){const m=await this.step(Math.min(this.accumulator,1/120));this.accumulator-=m.dt;}
  }
  resetClock(){this.accumulator=0;this.lastFrame=0;}
  fail(message:string){this.error=message;this.paused=true;this.onError?.(message)}
  async initializeForTest(rho:number[],velocity:number[]){
    if(!this.grid.options.testReadback||this.busy)throw Error('Inicjalizacja dostępna tylko w testach');
    if(rho.length!==this.grid.count||velocity.length!==this.grid.faces)throw Error('Niepoprawne wymiary fixture');
    await this.reset();this.rho.attribute.array.set(rho);this.rho.attribute.needsUpdate=true;this.flow.attribute.array.set(velocity);this.flow.attribute.needsUpdate=true;
    this.mass0=0;this.energy0=0;this.iterations=0;this.dirty=true;const m=await this.prepare();this.publish(m,0,0,null);
  }
  async probeAt(index:number):Promise<number[]|undefined>{
    if(this.disposed||this.error)return;
    if(this.busy){this.pendingProbe?.resolve(undefined);return new Promise(resolve=>{this.pendingProbe={index,resolve};});}
    const code=`fn probe(id:u32,r:ptr<storage,array<f32>,read_write>,v:ptr<storage,array<f32>,read_write>,out:ptr<storage,array<f32>,read_write>,point:u32)->void {if(id!=0u){return;}let q=xyz(point);(*out)[0]=temp(r,q)-273.15;(*out)[1]=(*r)[point];for(var a=0;a<3;a++){(*out)[u32(a)+2u]=.5*(vel(v,a,q)+vel(v,a,q+unit(a)));}for(var a=5u;a<8u;a++){(*out)[a]=0.;}}`;
    // One cached kernel per ping-pong pair, with a mutable probe index.
    this.busy=true;
    try{this.probeIndex.value=Math.max(0,Math.min(this.grid.count-1,index));
      this.run(`probe-${this.state}-${this.velocity}`,code,1,{r:this.rho.node,v:this.flow.node,out:this.fields.probe.node,point:this.probeIndex});
      return Array.from(await this.read(this.fields.probe));
    }finally{this.busy=false;const pending=this.pendingProbe;this.pendingProbe=undefined;if(pending){try{pending.resolve(await this.probeAt(pending.index));}catch{pending.resolve(undefined);}}}
  }
  private probeIndex=uniform(uint(0));
  async readFieldsForTest(){if(!this.grid.options.testReadback)throw Error('Pełny odczyt pól dozwolony tylko w harnessie testowym');this.fullReadbacks++;return {rho:Array.from(await this.read(this.rho)),velocity:Array.from(await this.read(this.flow)),source:Array.from(await this.read(this.fields.source))}}
  dispose(){if(this.disposed)return;this.disposed=true;this.paused=true;this.pendingProbe?.resolve(undefined);this.pendingProbe=undefined;for(const k of this.kernels.values())k.dispose();for(const f of this.fields.all())f.attribute.dispose();this.kernels.clear();this.renderer.dispose();this.device?.destroy();}
}
