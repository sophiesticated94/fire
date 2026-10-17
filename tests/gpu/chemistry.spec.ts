import {test,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
test('full GRI30 analytical GPU RHS and Jacobian versus independent Cantera finite differences',async({page})=>{
 test.setTimeout(180000);const errors:string[]=[];page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const report=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const chem=new l.Gri30(l.engine.computeDevice);const fixtures=l.chemistryFixtures;const output=await chem.evaluate(fixtures.map((f:any)=>f.state));const results=[];
  for(let cell=0;cell<fixtures.length;cell++){const f=fixtures[cell];let rhsError=0,jacError=0;const worst=[];for(let row=0;row<54;row++){const rhs=output[cell*2970+row*55+54];rhsError=Math.max(rhsError,Math.abs(rhs-f.rhs[row])/Math.max(1e-8,Math.abs(f.rhs[row])));const scale=Math.max(1e-8,...f.jacobian.slice(row*54,(row+1)*54).map(Math.abs));for(let col=0;col<54;col++){const actual=output[cell*2970+row*55+col],ref=f.jacobian[row*54+col];const error=Math.abs(actual-ref)/Math.max(1e-8,Math.abs(ref),scale*1e-6);jacError=Math.max(jacError,error);if(error>.001)worst.push({row,col,actual,ref,error});}}results.push({T:f.T,phi:f.phi,rhsError,jacError,worst:worst.sort((a,b)=>b.error-a.error).slice(0,10)});}
  chem.dispose();return {adapter:l.engine.adapter,results,finite:output.every(Number.isFinite)};});
 mkdirSync('artifacts/gpu-v14',{recursive:true});writeFileSync('artifacts/gpu-v14/chemistry-jacobian.json',JSON.stringify({...report,errors},null,2));
 expect(errors).toEqual([]);expect(report.finite).toBe(true);for(const r of report.results){expect(r.rhsError,JSON.stringify(r)).toBeLessThan(.001);expect(r.jacError,JSON.stringify(r)).toBeLessThan(.001);}
});
