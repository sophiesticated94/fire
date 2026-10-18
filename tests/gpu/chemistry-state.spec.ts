import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
const conservationFixture=JSON.parse(readFileSync(new URL('./chemistry-conservation-fixture.json',import.meta.url),'utf8'));

test('compensated BE preserves elements through the early small-step regression',async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async fixture=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    try{return await g.integrate([fixture.initial],fixture.time,undefined,{implementation:'gpu',precision:'compensated-state',localErrorTarget:1/64,maxWallMs:90000});}
    finally{g.dispose();}
  },conservationFixture);
  expect(r.mechanismSha256).toBe(conservationFixture.mechanismSha256);expect(r.stopReason).toBe('completed');
  expect(Math.abs(r.checkpoint.control[3]+r.checkpoint.targetEnthalpyLow![0]-conservationFixture.enthalpyRoundedInitial)).toBeLessThanOrEqual(1e-5);
  expect(Math.abs(r.states[0]-conservationFixture.state[0])).toBeLessThanOrEqual(1);
  for(let i=1;i<54;i++)expect(Math.abs(r.states[i]-conservationFixture.state[i])).toBeLessThanOrEqual(1e-12+.05*Math.abs(conservationFixture.state[i]));
  const sum=r.states.slice(1).reduce((a:number,b:number)=>a+b,0);
  expect(Math.abs(sum-1)).toBeLessThanOrEqual(1e-5);
  for(let e=0;e<conservationFixture.elements.length;e++){
    const value=conservationFixture.elementMatrix[e].reduce((s:number,x:number,i:number)=>s+x*r.states[i+1]/sum,0);
    expect(Math.abs(value-conservationFixture.elements[e])/Math.max(1e-30,Math.abs(conservationFixture.elements[e]))).toBeLessThanOrEqual(1e-5);
  }
});

test('stricter BE error budget is explicit, checkpointed and cannot loosen tolerances',async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    const initial=[l.reactorFixtures.cases[8].initial];
    try{
      const base=await g.integrate(initial,1e-7,undefined,{implementation:'gpu',maxWallMs:30000});
      const tight=await g.integrate(initial,1e-7,undefined,{implementation:'gpu',localErrorTarget:1/64,maxWallMs:30000});
      let mismatch=false,loosened=false,legacy=false;
      try{await g.integrate(initial,1e-7,undefined,{implementation:'gpu',checkpoint:tight.checkpoint,maxWallMs:30000});}catch{mismatch=true;}
      try{await g.integrate(initial,1e-7,undefined,{implementation:'gpu',localErrorTarget:2});}catch{loosened=true;}
      try{await g.integrate(initial,1e-7,undefined,{implementation:'gpu',checkpoint:{...base.checkpoint,schema:1}});}catch{legacy=true;}
      return {base,tight,mismatch,loosened,legacy};
    }finally{g.dispose();}
  });
  expect(r.tight.stopReason).toBe('completed');expect(r.tight.checkpoint.schema).toBe(4);
  expect(r.tight.checkpoint.localErrorTarget).toBe(1/64);
  expect(r.tight.checkpoint.tolerances).toEqual(r.base.checkpoint.tolerances);
  expect(r.tight.diagnostics.acceptedSteps).toBeGreaterThanOrEqual(r.base.diagnostics.acceptedSteps);
  expect(r.mismatch&&r.loosened&&r.legacy).toBe(true);
});

test('compensated state keeps low parts through cancellation and resume',async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    const initial=[l.reactorFixtures.cases[8].initial,l.reactorFixtures.cases[0].initial],abort=new AbortController();
    const options={implementation:'gpu',precision:'compensated-state',localErrorTarget:1/64,maxWallMs:30000,sampleTimes:[1e-8]};
    try{
      const first=await g.integrate(initial,1e-7,abort.signal,{...options,onProgress:()=>abort.abort()});
      const resumed=await g.integrate(initial,1e-7,undefined,{...options,checkpoint:first.checkpoint});
      const full=await g.integrate(initial,1e-7,undefined,options);
      const baseline=await g.integrate(initial,1e-7,undefined,{implementation:'gpu',maxWallMs:30000});
      let rejected=false;try{await g.integrate(initial,1e-7,undefined,{...options,checkpoint:{...first.checkpoint,acceptedLow:[[NaN]]}});}catch{rejected=true;}
      return {first,resumed,full,baseline,rejected,reference:initial.map((_:any,i:number)=>l.reactorFixtures.cases[i===0?8:0].points.find((p:any)=>p.time===1e-7).state),species:l.reactorFixtures.cases[8].initial.length};
    }finally{g.dispose();}
  });
  expect(r.resumed.stopReason).toBe('completed');expect(r.full.stopReason).toBe('completed');expect(r.baseline.stopReason).toBe('completed');
  expect(r.full.checkpoint.acceptedLow!.flat().some((x:number)=>x!==0)).toBe(true);
  expect(r.rejected).toBe(true);
  for(let i=0;i<108;i++)expect(Math.abs(r.resumed.states[i]-r.full.states[i])).toBeLessThanOrEqual(i%54===0?1:1e-12+1e-5*Math.abs(r.full.states[i]));
  expect(r.full.trajectory.every(Number.isFinite)).toBe(true);
  for(let cell=0;cell<2;cell++)for(let i=1;i<54;i++)expect(Math.abs(r.full.states[cell*54+i]-r.reference[cell][i])).toBeLessThanOrEqual(1e-12+.05*Math.abs(r.reference[cell][i]));
});

test('passive chemistry trace preserves accepted steps and streams without gaps',async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    const initial=[l.reactorFixtures.cases[8].initial],chunks:any[]=[];
    try{
      const plain=await g.integrate(initial,1e-6,undefined,{implementation:'gpu',maxWallMs:30000});
      const traced=await g.integrate(initial,1e-6,undefined,{implementation:'gpu',maxWallMs:30000,traceCapacity:48,onTrace:(c:any)=>chunks.push(c)});
      const plainAgain=await g.integrate(initial,1e-6,undefined,{implementation:'gpu',maxWallMs:30000});
      const ring=await g.integrate(initial,1e-6,undefined,{implementation:'gpu',maxWallMs:30000,traceCapacity:12});
      return {plain,traced,plainAgain,chunks,ring};
    }finally{g.dispose();}
  });
  expect(r.traced.stopReason).toBe('completed');expect(r.traced.states).toEqual(r.plain.states);
  expect(r.plainAgain.states).toEqual(r.plain.states);
  expect(r.traced.checkpoint.control).toEqual(r.plain.checkpoint.control);
  expect(r.traced.gpuInitial).toEqual(r.traced.checkpoint.initial[0].map(Math.fround));
  const records=r.chunks.flatMap((c:any)=>c.records);
  expect(records.map((x:any)=>x.sequence)).toEqual(records.map((_:any,i:number)=>i));
  expect(r.chunks.every((c:any)=>c.dropped===0)).toBe(true);
  expect(r.ring.trace!.dropped).toBeGreaterThan(0);
  expect(r.ring.trace!.records).toHaveLength(12);
  expect(r.traced.profile.dispatches/r.traced.profile.statusReads).toBeLessThanOrEqual(32);
});

test('GPU state machine completes independent reactors and matches Cantera samples',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    const cases=[l.reactorFixtures.cases[0],l.reactorFixtures.cases.find((x:any)=>x.T===1500&&x.phi===1)];
    try{
      const result=await g.integrate(cases.map((x:any)=>x.initial),1e-7,undefined,{implementation:'gpu',sampleTimes:[1e-8],maxWallMs:30000});
      const alone=await g.integrate([cases[1].initial],1e-7,undefined,{implementation:'gpu',sampleTimes:[1e-8],maxWallMs:30000});
      return {result,alone,ref:cases.map((x:any)=>x.points.find((p:any)=>p.time===1e-7).state)};
    }finally{g.dispose();}
  });
  expect(errors).toEqual([]);expect(r.result.stopReason).toBe('completed');expect(r.alone.stopReason).toBe('completed');
  expect(r.result.states.slice(54)).toEqual(r.alone.states);
  for(let cell=0;cell<2;cell++)for(let i=0;i<54;i++)expect(Math.abs(r.result.states[cell*54+i]-r.ref[cell][i])).toBeLessThanOrEqual(i===0?1:Math.max(1e-4,.02*Math.abs(r.ref[cell][i])));
  expect(r.result.profile.dispatches/r.result.profile.statusReads).toBeLessThanOrEqual(32);
  expect(r.result.diagnostics.maxAcceptedLinearResidual).toBeLessThanOrEqual(1e-5);
});

test('cancellation yields an accepted checkpoint and resume preserves trajectory',async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    const f=l.reactorFixtures.cases.find((x:any)=>x.T===1500&&x.phi===1),abort=new AbortController();
    try{
      const options={implementation:'gpu',sampleTimes:[1e-8,1e-7],maxWallMs:30000};
      const interrupted=await g.integrate([f.initial],1e-6,abort.signal,{...options,onProgress:()=>abort.abort()});
      const resumed=await g.integrate([f.initial],1e-6,undefined,{...options,checkpoint:interrupted.checkpoint});
      const full=await g.integrate([f.initial],1e-6,undefined,options);
      let rejected=false;try{await g.integrate([f.initial],2e-6,undefined,{...options,checkpoint:interrupted.checkpoint});}catch{rejected=true;}
      return {interrupted,resumed,full,rejected};
    }finally{g.dispose();}
  });
  expect(r.interrupted.stopReason).toBe('cancelled');expect(r.resumed.stopReason).toBe('completed');expect(r.full.stopReason).toBe('completed');expect(r.rejected).toBe(true);
  for(let i=0;i<54;i++)expect(Math.abs(r.resumed.states[i]-r.full.states[i])).toBeLessThanOrEqual(i===0?1:1e-12+1e-5*Math.abs(r.full.states[i]));
  expect(r.resumed.trajectory.every(Number.isFinite)).toBe(true);
});

test('refined LU and storage-backed double-single diagnostic execute on GPU',async({page})=>{
  const errors:string[]=[];page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    try{
      const f=l.reactorFixtures.cases.find((x:any)=>x.T===1500&&x.phi===1);
      const reactor=await g.integrate([f.initial],1e-7,undefined,{implementation:'gpu',linearSolver:'refined-lu',inspection:true,maxWallMs:30000});
      // Exactly representable coefficients. The true solution has low parts
      // that cannot be retained by a single float32 output.
      const systems=[[1e8,1,1e8,1,1,2]];
      const single=await l.probeLinearPrecision(l.engine.computeDevice,systems,2,'float32');
      const extended=await l.probeLinearPrecision(l.engine.computeDevice,systems,2,'double-single');
      return {reactor,single,extended};
    }finally{g.dispose();}
  });
  expect(errors).toEqual([]);expect(r.reactor.stopReason).toBe('completed');expect(r.reactor.inspection.stride).toBe(3342);
  expect(r.reactor.diagnostics.rejected).toBeGreaterThan(0); // RETRY must remain active.
  const residual=(x:number[])=>Math.max(Math.abs(1e8*x[0]+x[1]-1e8),Math.abs(x[0]+x[1]-2));
  expect(r.extended.systems[0].failed).toBe(false);
  expect(residual(r.extended.systems[0].solution)).toBeLessThan(residual(r.single.systems[0].solution));
  expect(residual(r.extended.systems[0].solution)).toBeLessThan(1e-5);
});

test('device loss preserves the previous durable chemistry checkpoint',async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const device=l.engine.computeDevice,g=new l.Gri30(device);
    const initial=[l.reactorFixtures.cases.find((x:any)=>x.T===1500&&x.phi===1).initial],abort=new AbortController();
    const prior=await g.integrate(initial,1e-6,abort.signal,{implementation:'gpu',maxWallMs:30000,onProgress:()=>abort.abort()});
    const before=JSON.stringify(prior.checkpoint);let failed=false;
    try{await g.integrate(initial,1e-6,undefined,{implementation:'gpu',checkpoint:prior.checkpoint,maxWallMs:30000,onProgress:()=>device.destroy()});}catch{failed=true;}
    g.dispose();const adapter=await navigator.gpu!.requestAdapter({powerPreference:'high-performance'});
    const next=await adapter!.requestDevice({requiredLimits:{maxStorageBuffersPerShaderStage:8}}),restored=new l.Gri30(next);
    try{
      const result=await restored.integrate(initial,1e-6,undefined,{implementation:'gpu',checkpoint:prior.checkpoint,maxWallMs:30000});
      return {failed,unchanged:before===JSON.stringify(prior.checkpoint),complete:result.stopReason==='completed'};
    }finally{restored.dispose();next.destroy();}
  });
  expect(r).toEqual({failed:true,unchanged:true,complete:true});
});

test('scheduler handles more than 256 reactors without truncating the final tile',async({page})=>{
  await page.goto('/tests/gpu/harness.html');await page.waitForFunction(()=>!!(window as any).lab);
  const r=await page.evaluate(async()=>{
    const l=(window as any).lab;await l.create({cells:[8,8,16]});const g=new l.Gri30(l.engine.computeDevice);
    try{
      const cold=l.reactorFixtures.cases[0].initial,hot=l.reactorFixtures.cases.find((x:any)=>x.T===1500&&x.phi===1).initial;
      const result=await g.integrateBatch(Array.from({length:513},(_,i)=>i%2?cold:hot),1e-8,undefined,{maxWallMs:60000,sliceWallMs:15000});
      return {reactors:result.reactors,complete:result.complete,tiles:result.tiles,counts:result.checkpoints.map((t:any)=>t.checkpoint.accepted.length),
        finite:result.checkpoints.every((t:any)=>t.checkpoint.accepted.flat().every(Number.isFinite))};
    }finally{g.dispose();}
  });
  expect(r).toEqual({reactors:513,complete:true,tiles:3,counts:[256,256,1],finite:true});
});
