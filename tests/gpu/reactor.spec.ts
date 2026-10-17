import {test,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
test('short implicit reactor smoke versus Cantera is not a full chemistry acceptance',async({page})=>{
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const chem=new l.Gri30(l.engine.computeDevice);const f=l.reactorFixtures.cases.find((f:any)=>f.T===1500&&f.phi===1);try{const actual=await chem.integrate([f.initial],1e-8,undefined,{maxWallMs:10000,maxAttempts:100});return {actual,reference:f.points[0].state,species:chem.species};}finally{chem.dispose();}});
 expect(r.actual.stopReason).toBe('completed');expect(r.actual.states.every(Number.isFinite)).toBe(true);expect(Math.abs(r.actual.states[0]-r.reference[0])).toBeLessThan(1);
 for(let i=1;i<54;i++)expect(Math.abs(r.actual.states[i]-r.reference[i])).toBeLessThanOrEqual(Math.max(1e-4,.02*Math.abs(r.reference[i])));
 for(const name of ['H','O','OH','HO2','CH3']){const i=r.species.indexOf(name)+1;expect(Math.abs(r.actual.states[i]-r.reference[i])/(1e-12+.05*Math.abs(r.reference[i]))).toBeLessThanOrEqual(1);}
 expect(r.actual.status[5]).toBeLessThanOrEqual(1e-5);expect(r.actual.status[8]).toBeLessThanOrEqual(1e-5);
});

test('full adiabatic Cantera horizon @chemistry-gate',async({page})=>{
 test.setTimeout(360000);const errors:string[]=[];page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.text().startsWith('REACTOR '))console.log(m.text())});
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const result=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const chem=new l.Gri30(l.engine.computeDevice);const f=l.reactorFixtures.cases.find((f:any)=>f.T===1500&&f.phi===1);const result=await chem.integrate([f.initial],f.horizon,undefined,{maxWallMs:180000,onProgress:(p:any)=>console.log('REACTOR '+JSON.stringify(p))});chem.dispose();return {adapter:l.engine.adapter,fixture:{T:f.T,phi:f.phi,horizon:f.horizon},...result};});
 mkdirSync('artifacts/gpu-v14',{recursive:true});writeFileSync('artifacts/gpu-v14/reactor-gate.json',JSON.stringify({...result,errors},null,2));
 expect(errors).toEqual([]);expect(result.states.every(Number.isFinite)).toBe(true);expect(result.status[5]).toBeLessThanOrEqual(1e-5);expect(result.status[8]).toBeLessThanOrEqual(1e-5);expect(result.stopReason,'Partial chemistry cannot enable a 3D burner').toBe('completed');
});
