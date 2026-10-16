import {test,expect} from '@playwright/test';
test('manufactured pressure gradient: open-face Dirichlet and sealed floor',async({page})=>{
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const result=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16],gravity:0,k:0,mu:0});const e=l.engine;e.setParameters({power:0});const c=new l.CpuReference([8,8,16],0,0,0,0,0);const potential=(q:number[])=>Math.sin(Math.PI*(q[0]+.5)/8)*Math.sin(Math.PI*(q[1]+.5)/8)*Math.cos(Math.PI*(q[2]+.5)/32)*1e-4;
 c.eachFace((a:number,q:number[],id:number)=>{if(a===2&&q[2]===0){c.v[id]=0;return;}const left=c.shift(q,a,-1);c.v[id]=((c.outside(q)?0:potential(q))-(c.outside(left)?0:potential(left)))*(c.outside(q)||c.outside(left)?2:1)/(c.h[a]*c.rho0);});
 await e.initializeForTest(Array.from(c.rho),Array.from(c.v));const f=await e.readFieldsForTest();return {speed:Math.max(...f.velocity.map(Math.abs)),metrics:e.metrics};});
 expect(result.speed).toBeLessThan(1e-5);expect(result.metrics.normalizedDivergence).toBeLessThan(1e-3);
});
test('CFL rejection retries four times and does not commit physical time',async({page})=>{
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const result=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine,stats=e.stats.bind(e);let trials=0;e.stats=async(...args:any[])=>{const m=await stats(...args);if(args.length>2){m[12]=1e6;trials++;}return m;};try{await e.step()}catch{}return {trials,time:e.time,steps:e.steps,error:e.error};});
 expect(result.trials).toBe(4);expect(result.time).toBe(0);expect(result.steps).toBe(0);expect(result.error).toContain('CFL');
});
