import {test,expect} from '@playwright/test';
import {writeFileSync,mkdirSync} from 'node:fs';
test('native 32×32×64 stability, energy budget and timed trials',async({page})=>{
 test.setTimeout(5400000);
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 page.on('console',m=>{if(m.text().startsWith('CHECKPOINT ')){mkdirSync('artifacts/gpu',{recursive:true});writeFileSync('artifacts/gpu/checkpoint.json',m.text().slice(11));console.log(m.text());}});
 const report=await page.evaluate(async()=>{
  const l=(window as any).lab;await l.create();const e=l.engine;const wall=performance.now();let at5:any,at60:any;const samples:any[]=[];
  while(e.time<60){const m=await e.step();if(!at5&&e.time>=5)at5={...m};if(e.steps%120===0){samples.push({...m});console.log('CHECKPOINT '+JSON.stringify({time:e.time,steps:e.steps,metrics:m,at5,wallSeconds:(performance.now()-wall)/1000}));}}
  at60={...e.metrics};const trials=[];
  // Time windows are wall clock; solver physical time never skips to match the clock.
  for(let trial=-1;trial<3;trial++){const start=performance.now(),initial=e.time,steps=e.steps,bytes=e.readbackBytes;const metrics=[];while(performance.now()-start<(trial<0?10000:30000)){metrics.push(await e.step());}if(trial>=0)trials.push({wallSeconds:(performance.now()-start)/1000,physicalSeconds:e.time-initial,steps:e.steps-steps,readbackBytes:e.readbackBytes-bytes,metrics});}
  return {model:e.model,adapter:e.adapter,cells:e.grid.cells,at5,at60,samples,trials,totalWallSeconds:(performance.now()-wall)/1000,fullReadbacks:e.fullReadbacks};
 });
 mkdirSync('artifacts/gpu',{recursive:true});writeFileSync('artifacts/gpu/benchmark-native.json',JSON.stringify(report,null,2));
 expect(report.at60.time).toBeGreaterThanOrEqual(60);expect(report.fullReadbacks).toBe(0);
 expect(Math.abs(report.at5.energyError)/report.at5.time).toBeLessThan(.05);
 expect(report.at60.cumulativeMassError).toBeLessThan(1e-4);
});
