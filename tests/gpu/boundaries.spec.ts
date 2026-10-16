import {test,expect} from '@playwright/test';
test.beforeEach(async({page})=>{await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab)});
test('variable density preserves a uniform velocity with consistent dual mass fluxes',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16],gravity:0,k:0,mu:0});const e=l.engine;e.setParameters({power:0,wind:.04});const c=new l.CpuReference([8,8,16],0,0,0,0,.04);c.eachCell((q:number[],id:number)=>{c.rho[id]*=1-.03*Math.exp(-((q[0]-3.5)**2+(q[1]-3.5)**2+(q[2]-7.5)**2)/5);});await e.initializeForTest(Array.from(c.rho),Array.from(c.v));for(let i=0;i<10;i++){const m=await e.step();c.step(m.dt);}const f=await e.readFieldsForTest();let err=0;for(let i=0;i<c.faces;i++)err=Math.max(err,Math.abs(f.velocity[i]-c.v[i]));return {err,metrics:e.metrics,bottom:f.velocity.slice(e.grid.offsets[2],e.grid.offsets[2]+64)};});
 expect(r.err).toBeLessThan(1e-5);expect(r.bottom.every((n:number)=>n===0)).toBeTruthy();expect(r.metrics.cumulativeMassError).toBeLessThan(1e-4);
});
test('heater off changes the expansion target without deleting warm gas',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16],k:0});const e=l.engine;for(let i=0;i<20;i++)await e.step();const before=e.metrics;e.setParameters({power:0});for(let i=0;i<10;i++)await e.step();return {before,after:e.metrics,full:e.fullReadbacks};});
 expect(r.after.heaterPower).toBe(0);expect(r.after.temperature).toBeGreaterThan(20);expect(r.after.temperature).toBeLessThanOrEqual(r.before.temperature+.01);expect(r.full).toBe(0);
});
test('failed step pauses and retains the last committed state',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine;const state=e.state,velocity=e.velocity;e.fields.rho[1-state].attribute.array.fill(-1);e.fields.rho[1-state].attribute.needsUpdate=true;
 // Inject a compute failure after transport; commit must remain atomic.
 e.solve=async()=>{throw Error('injected projection failure')};try{await e.step()}catch{}return {state:e.state,velocity:e.velocity,time:e.time,paused:e.paused,error:e.error,originalState:state,originalVelocity:velocity};});
 expect(r.state).toBe(r.originalState);expect(r.velocity).toBe(r.originalVelocity);expect(r.time).toBe(0);expect(r.paused).toBe(true);expect(r.error).toContain('injected');
});
test('device loss is reported and does not become a WebGL compute fallback',async({page})=>{
 await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});l.engine.device.destroy();});
 await expect.poll(()=>page.evaluate(()=>(window as any).lab.engine.error)).toContain('Utrata urządzenia');
});
test('small probes are queued once and full readback requires explicit test opt-in',async({page})=>{
 const result=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine;const work=e.step();const values=await e.probeAt(100);await work;const read=e.readbackBytes,fields=e.fields.bytes;e.grid.options.testReadback=false;let blocked=false;try{await e.readFieldsForTest()}catch{blocked=true;}return {values,read,fields,blocked,full:e.fullReadbacks};});
 expect(result.values).toHaveLength(8);expect(result.values![0]).toBeGreaterThanOrEqual(19.99);expect(result.blocked).toBe(true);expect(result.full).toBe(0);expect(result.read).toBeLessThan(result.fields);
});
test('live wind updates use bounded kernels and apply on the next accepted step',async({page})=>{
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine;e.setParameters({power:0});for(let i=0;i<24;i++){e.setParameters({wind:i/240});await e.step();}const kernels=e.kernels.size;const pending=e.step();e.setParameters({power:2,wind:0});await pending;await e.step();return {speed:e.metrics.speed,power:e.metrics.heaterPower,kernels,finalKernels:e.kernels.size,full:e.fullReadbacks};});
 expect(r.power).toBeCloseTo(2,4);expect(r.finalKernels-r.kernels).toBeLessThan(20);expect(r.kernels).toBeLessThan(130);expect(r.full).toBe(0);
});
