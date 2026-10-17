import {test,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
test.beforeEach(async({page})=>{await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab)});
test('volume heating and cooling preserve mass and account for external enthalpy',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16],gravity:0,k:0,mu:0});const e=l.engine;e.setParameters({power:0,ambient:21});const heating=[];for(let i=0;i<16;i++)heating.push(await e.step());e.setParameters({ambient:19,wind:.6,gravity:0,viscosity:2e-5,thermalConductivity:0});const cooling=[];for(let i=0;i<16;i++)cooling.push(await e.step());return {heating,cooling,after:e.metrics};});
 expect(r.heating.at(-1).ambient).toBeCloseTo(21,5);expect(r.heating.at(-1).environmentEnergy).toBeGreaterThan(0);expect(r.cooling.at(-1).ambient).toBeLessThan(21);expect(r.after.time).toBeGreaterThan(r.heating.at(-1).time);
 for(const m of [...r.heating,...r.cooling]){expect(m.cumulativeMassError).toBeLessThan(1e-4);expect(Math.abs(m.energyError)).toBeLessThan(.01*Math.max(1,Math.abs(m.environmentEnergy)));expect(m.normalizedDivergence).toBeLessThan(1e-3);expect(m.cfl).toBeLessThan(.50001);}
});
test('failure rolls back ambient ramp, energy and all auxiliary fields',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine;e.setParameters({ambient:50});const before=await e.readStateForTest();e.solve=async()=>{throw Error('ramp rollback')};try{await e.step()}catch{}const after=await e.readStateForTest();return {before,after};});expect(r.after).toEqual(r.before);
});

test('configuration arriving during a step applies on the following step',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine;const stats=e.stats.bind(e);let updated=false;e.stats=async(...args:any[])=>{const m=await stats(...args);if(!updated){updated=true;e.setParameters({ambient:30,gravity:0,wind:.2});}return m;};const first=await e.step();const second=await e.step();return {first,second,config:e.config};});
 expect(r.first.ambient).toBeCloseTo(20,5);expect(r.second.ambient).toBeGreaterThan(20);expect(r.second.time).toBeGreaterThan(r.first.time);expect(r.config.wind).toBe(.2);
});

test('live material properties match an independent CPU continuation without resetting flow',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine;let cpu=new l.CpuReference([8,8,16]);for(let i=0;i<5;i++){const m=await e.step();cpu.step(m.dt);}const time=e.time;
  e.setParameters({gravity:20,viscosity:5e-5,thermalConductivity:.1});const continued=new l.CpuReference([8,8,16],20,.1,5e-5);continued.rho=cpu.rho;continued.v=cpu.v;continued.thermal();continued.v=continued.project(continued.v);cpu=continued;
  for(let i=0;i<10;i++){const m=await e.step();cpu.step(m.dt);}const fields=await e.readFieldsForTest();let temperature=0,velocity=0;for(let i=0;i<cpu.count;i++)temperature=Math.max(temperature,Math.abs(101325/(287.05*fields.rho[i])-101325/(287.05*cpu.rho[i])));for(let i=0;i<cpu.faces;i++)velocity+=(fields.velocity[i]-cpu.v[i])**2;return {time,after:e.time,temperature,velocityRms:Math.sqrt(velocity/cpu.faces)};});
 expect(r.after).toBeGreaterThan(r.time);expect(r.temperature).toBeLessThan(.01);expect(r.velocityRms).toBeLessThan(.001);
});

test('full-grid maximum wind and ambient ramp remain conservative over a domain crossing',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[32,32,64]});const e=l.engine;const initial=await e.read(e.rho);const initialMass64=Array.from(initial as Float32Array).reduce((a:number,b:number)=>a+b,0)*e.grid.volume;let diagnosis:any;const stats=e.stats.bind(e);e.stats=async(...args:any[])=>{const m=await stats(...args);if(args.length>2){const dt=e.par.value.x;const error=Math.abs(m[0]-e.lastMass+dt*m[16])/e.mass0;if(error>1e-5){const rho=await e.read(args[0]);diagnosis={dt,error,m:Array.from(m),initialMass64,initialMass32:e.mass0,newMass64:Array.from(rho as Float32Array).reduce((a:number,b:number)=>a+b,0)*e.grid.volume,massIntegral:e.massIntegral,lastMass:e.lastMass};}}return m;};e.setParameters({wind:.6,ambient:50,gravity:0,viscosity:0,thermalConductivity:0});const steps=[];try{for(let i=0;i<80;i++)steps.push(await e.step());return {steps};}catch(error){return {steps,error:String(error),diagnosis};}});
 mkdirSync('artifacts/gpu-v14',{recursive:true});writeFileSync('artifacts/gpu-v14/wind-conservation.json',JSON.stringify(r,null,2));writeFileSync(`artifacts/gpu-v14/wind-conservation-${r.steps[0]?.adapter.vendor??'unknown'}.json`,JSON.stringify(r,null,2));
 expect(r.error).toBeUndefined();expect(r.steps.at(-1).time).toBeGreaterThan(.16/.6);for(const m of r.steps){expect(m.cfl).toBeLessThanOrEqual(.50001);expect(m.cumulativeMassError).toBeLessThan(1e-4);expect(m.normalizedDivergence).toBeLessThan(1e-3);expect(Math.abs(m.energyError)/Math.max(1,Math.abs(m.environmentEnergy)+m.time)).toBeLessThan(.01);}
});
