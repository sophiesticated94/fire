import {test,expect} from '@playwright/test';
for(const c of [{name:'heated plume',power:1,wind:0,g:9.81},{name:'rest',power:0,wind:0,g:9.81},{name:'wind transport',power:1,wind:.05,g:9.81},{name:'expansion without gravity',power:1,wind:0,g:0}]){
 test(`float64 CG reference: ${c.name}`,async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const errors=await page.evaluate(async(c)=>{const l=(window as any).lab;await l.create({cells:[8,8,16],gravity:c.g});l.engine.setParameters({power:c.power,wind:c.wind});await l.engine.reset();const cpu=new l.CpuReference([8,8,16],c.g,.0257,1.81e-5,c.power,c.wind);for(let i=0;i<10;i++){const m=await l.engine.step();cpu.step(m.dt);}const gpu=await l.engine.readFieldsForTest();let temperature=0,rho=0,vrms=0,ref=0;for(let i=0;i<cpu.count;i++){temperature=Math.max(temperature,Math.abs(101325/287.05/gpu.rho[i]-101325/287.05/cpu.rho[i]));rho=Math.max(rho,Math.abs(gpu.rho[i]-cpu.rho[i])/cpu.rho[i]);}for(let i=0;i<cpu.faces;i++){vrms+=(gpu.velocity[i]-cpu.v[i])**2;ref+=cpu.v[i]**2;}return {temperature,rho,vrms:Math.sqrt(vrms/cpu.faces),referenceRms:Math.sqrt(ref/cpu.faces),metrics:l.engine.metrics};},c);
  expect(errors.temperature).toBeLessThan(.01);expect(errors.rho).toBeLessThan(1e-4);expect(errors.vrms).toBeLessThan(Math.max(.001,.01*errors.referenceRms));
  if(c.power)expect(errors.metrics.expansionFluxError).toBeLessThan(.01);else if(!c.wind)expect(errors.metrics.speed).toBeLessThan(1e-6);
 });
}
