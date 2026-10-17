import {test,expect} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
test('benchmark SOR reference versus GPU convergence with native adapter evidence',async({page,browser})=>{
 test.setTimeout(1800000);page.on('console',m=>{if(m.text().startsWith('SOR '))console.log(m.text())});mkdirSync('artifacts/gpu-v14',{recursive:true});
 await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
 const cdp=await browser.newBrowserCDPSession();const processes=await cdp.send('SystemInfo.getProcessInfo');
 const gpu=processes.processInfo.find(p=>p.type.toLowerCase()==='gpu');if(!gpu)throw Error('No GPU process evidence');
 const evidence=promisify(execFile)('.venv/Scripts/python.exe',['scripts/gpu_hardware.py','--pid',String(gpu.id),'--seconds','8'],{maxBuffer:8000000});
 const renderOnly=process.env.IGNIS_SOR_RENDER_ONLY==='1';
 const result=await page.evaluate(async(renderOnly)=>{
   const l=(window as any).lab;const {WebGpuFireScene}=await import('/src/scene/WebGpuFireScene.ts');
   const trials=[];let adapter:any;
   for(const render of (renderOnly?[true]:[false,true]))for(const mode of ['reference','batched']){
     await l.create({pressureMode:mode});const e=l.engine;adapter=e.adapter;
     const host=document.createElement('div');host.style.cssText='width:800px;height:600px';document.body.append(host);const scene=render?new WebGpuFireScene(host,e):null;let frames=0,draw=true;
     const raf=()=>{if(draw){scene?.render();if(scene)frames++;requestAnimationFrame(raf)}};if(scene)requestAnimationFrame(raf);
     const cycle=async()=>{const before=performance.now();await e.reset();const resetMs=performance.now()-before;const samples=[];while(e.time<.5)samples.push(await e.step());return {resetMs,samples,physical:e.time};};
     const warm=performance.now();while(performance.now()-warm<10000)await cycle();
     for(let trial=0;trial<3;trial++){const start=performance.now(),initialFrames=frames;const cycles=[];while(performance.now()-start<30000)cycles.push(await cycle());console.log('SOR '+JSON.stringify({mode,render,trial,physicalSeconds:cycles.reduce((n,c)=>n+c.physical,0),wallSeconds:(performance.now()-start)/1000}));trials.push({mode,render,trial,wallSeconds:(performance.now()-start)/1000,frames:frames-initialFrames,cycles});}
     draw=false;scene?.dispose();host.remove();
   }
   return {adapter,model:l.engine.model,config:l.engine.config,cells:l.engine.grid.cells,trials,userAgent:navigator.userAgent,fullReadbacks:l.engine.fullReadbacks};
 },renderOnly);
 const native=JSON.parse((await evidence).stdout);const matching=native.adapters.find((a:any)=>a.device===result.adapter.device&&a.vendor==='0x10de');
 const active=matching&&native.samples.some((s:any)=>s.Name.toLowerCase().includes('luid_'+matching.luid.toLowerCase())&&Number(s.UtilizationPercentage)>0);
 const report={...result,protocol:{renderOnly,warmupWallSeconds:10,minimumWindowWallSeconds:30,windows:3},native,rtxVerified:result.adapter.vendor==='nvidia'&&matching?.device==='0x28a1'&&!!active};
 writeFileSync(`artifacts/gpu-v14/sor-${result.adapter.vendor}${renderOnly?'-confirmation':''}.json`,JSON.stringify(report,null,2));
 if(process.env.IGNIS_GPU_ADAPTER==='rtx')expect(report.rtxVerified).toBe(true);
 expect(result.fullReadbacks).toBe(0);
});
