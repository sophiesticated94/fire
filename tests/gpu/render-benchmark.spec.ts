import {test,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
test('render and compute benchmark: warm-up then three 30 s wall-clock samples',async({page})=>{
 test.setTimeout(240000);await page.setViewportSize({width:1280,height:900});await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 await page.exposeFunction('captureGpu',async()=>{await page.screenshot({path:'artifacts/gpu/thermal-plume.png'});});
 const result=await page.evaluate(async()=>{
  const l=(window as any).lab;await l.create();const e=l.engine;const {WebGpuFireScene}=await import('/src/scene/WebGpuFireScene.ts');const host=document.createElement('div');host.style.cssText='width:800px;height:600px';document.body.append(host);const scene=new WebGpuFireScene(host,e);let frames=0,running=true;
  const draw=()=>{if(running){scene.render();frames++;requestAnimationFrame(draw)}};requestAnimationFrame(draw);const trials=[];
  for(let i=-1;i<3;i++){const start=performance.now(),frameStart=frames,time=e.time,steps=e.steps,bytes=e.readbackBytes;const samples=[];while(performance.now()-start<(i<0?10000:30000))samples.push(await e.step());if(i>=0)trials.push({wallSeconds:(performance.now()-start)/1000,physicalSeconds:e.time-time,steps:e.steps-steps,frames:frames-frameStart,readbackBytes:e.readbackBytes-bytes,samples});}
  await (window as any).captureGpu();running=false;scene.dispose();return {adapter:e.adapter,userAgent:navigator.userAgent,model:e.model,timingScheme:e.timingScheme,grid:e.grid.cells,viewport:[800,600],pixelRatio:e.renderer.getPixelRatio(),fieldsBytes:e.fields.bytes,fullReadbacks:e.fullReadbacks,trials};
 });
 mkdirSync('artifacts/gpu',{recursive:true});writeFileSync('artifacts/gpu/render-benchmark-native.json',JSON.stringify(result,null,2));expect(result.fullReadbacks).toBe(0);expect(result.trials).toHaveLength(3);
});
