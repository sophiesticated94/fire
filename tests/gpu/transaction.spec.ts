import {test,expect} from '@playwright/test';
import {defaultPressureMode} from '../../src/gpu/GpuGrid';

test('automatic SOR selection is restricted to the measured device and grid',()=>{
 expect(defaultPressureMode({vendor:'nvidia',device:'0x28a1'},[32,32,64])).toBe('batched');
 expect(defaultPressureMode({vendor:'intel',device:''},[32,32,64])).toBe('reference');
 expect(defaultPressureMode({vendor:'nvidia',device:'other'},[32,32,64])).toBe('reference');
 expect(defaultPressureMode({vendor:'nvidia',device:'0x28a1'},[8,8,16])).toBe('reference');
});
test('failure restores every field including source, pressure and convergence history',async({page})=>{
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const result=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16],pressureMode:'batched'});const e=l.engine;await e.step();e.setParameters({wind:.08,power:2});const before=await e.readStateForTest();const stats=e.stats.bind(e);e.stats=async(...args:any[])=>{const m=await stats(...args);if(args.length>2)throw Error('after-projection');return m;};try{await e.step()}catch{}const after=await e.readStateForTest();return {before,after};});
 expect(result.after.fields).toEqual(result.before.fields);expect(result.after.meta).toEqual(result.before.meta);
});

test('failed restore submission still restores CPU metadata and reports the failure',async({page})=>{
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const r=await page.evaluate(async()=>{const l=(window as any).lab;await l.create({cells:[8,8,16]});const e=l.engine;const saved=e.snapshotMeta();const copy=e.copySnapshot.bind(e);e.copySnapshot=(restore=false)=>{if(restore)throw Error('lost restore');copy(false);};e.solve=async()=>{throw Error('projection failed');};try{await e.step()}catch{}return {saved,after:e.snapshotMeta(),error:e.error};});
 expect(r.after).toEqual(r.saved);expect(r.error).toContain('projection failed');expect(r.error).toContain('przywrócić buforów');
});
for(const cells of [[8,8,16],[32,32,64]])test(`batched SOR matches reference fields and actual iteration count ${cells.join('×')}`,async({page})=>{
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const result=await page.evaluate(async(cells)=>{const l=(window as any).lab;const out=[];for(const mode of ['reference','batched']){await l.create({cells,pressureMode:mode});for(let i=0;i<10;i++)await l.engine.step();out.push({fields:await l.engine.readFieldsForTest(),iterations:l.engine.metrics.iterations});}return out;},cells);
 expect(result[0].fields).toEqual(result[1].fields);expect(result[0].iterations).toBe(result[1].iterations);
});
