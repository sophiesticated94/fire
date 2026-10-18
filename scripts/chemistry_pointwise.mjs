import {chromium} from '@playwright/test';
import {createServer} from 'vite';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawnSync} from 'node:child_process';

// Called inside the forensics driver's existing budget lease and lock.
export async function pointwise(out,python,reserve){
 const run=(args)=>{
  reserve(60000);const r=spawnSync(python,args,{encoding:'utf8',timeout:60000});
  if(r.status!==0)throw Error(r.stderr);return r;
 };
 const input=resolve(out,'pointwise-input.json'),output=resolve(out,'pointwise-ignition.json');
 run(['scripts/chemistry_ignition_reference.py','prepare',resolve(out,'chemistry-divergence.json'),input]);
 const data=JSON.parse(readFileSync(input,'utf8'));
 const hardware=JSON.parse(run(['scripts/gpu_hardware.py']).stdout);
 let server,browser;
 try{
  server=await createServer({mode:'gputest',server:{host:'127.0.0.1',port:5177,strictPort:true,hmr:false}});await server.listen();
  browser=await chromium.launch({channel:'msedge',headless:true,args:['--use-angle=d3d11','--force-high-performance-gpu','--use-webgpu-power-preference=force-high-performance','--enable-webgpu-developer-features']});
  const page=await browser.newPage();await page.goto('http://127.0.0.1:5177/tests/gpu/harness.html');await page.waitForFunction(()=>!!window.lab);
  const values=await page.evaluate(async states=>{
   const a=await navigator.gpu.requestAdapter({powerPreference:'high-performance'});if(!a)throw Error('WebGPU unavailable');
   const d=await a.requestDevice({requiredLimits:{maxStorageBuffersPerShaderStage:8}});
   const g=new window.lab.Gri30(d);
   try{return {values:await g.evaluate(states),adapter:{vendor:a.info.vendor,device:a.info.device,architecture:a.info.architecture}};}
   finally{g.dispose();d.destroy();}
  },data.states);
  if(values.adapter.vendor!=='nvidia'||values.adapter.device!=='0x28a1'||!hardware.adapters.some(a=>a.vendor==='0x10de'&&a.device==='0x28a1'))throw Error('RTX 4050 not confirmed');
  writeFileSync(input,JSON.stringify({...data,...values,hardware}));
 }finally{await browser?.close();await server?.close();}
 const report=run(['scripts/chemistry_ignition_reference.py','audit',input,output]);console.log(report.stdout.trim());
}
