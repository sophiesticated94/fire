import {test,expect} from '@playwright/test';
test('native GPU creates a low-Mach expansion field and advances mass',async({page})=>{
 const errors:string[]=[];page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const result=await page.evaluate(async()=>{const l=(window as any).lab;const first=await l.create({cells:[8,8,16]});const steps=[];for(let i=0;i<10;i++)steps.push(await l.engine.step());return {first,last:l.engine.metrics,steps,fields:await l.engine.readFieldsForTest()}});
 expect(errors).toEqual([]);expect(result.last.time).toBeGreaterThan(0);expect(result.last.temperature).toBeGreaterThan(20);
 expect(result.last.normalizedDivergence).toBeLessThan(1e-3);expect(result.last.cumulativeMassError).toBeLessThan(1e-4);
 expect(result.last.heaterPower).toBeCloseTo(1,4);expect(result.fields.rho.every((r:number)=>r>0)).toBeTruthy();
 console.log(JSON.stringify({first:result.first,last:result.last}));
});
