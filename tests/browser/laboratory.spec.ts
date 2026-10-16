import {test,expect} from '@playwright/test';

test('real CFD result, layers, playback and parameters',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  await page.setViewportSize({width:1440,height:1100});
  await page.goto('/');
  await expect(page.locator('#result-label')).toContainText('FDS ·',{timeout:20000});
  await expect(page.locator('#empty-state')).toBeHidden({timeout:20000});
  await page.locator('#play').click();
  await expect(page.locator('#metric-temp')).not.toContainText('—');
  const viewport=await page.locator('#viewport').boundingBox();
  await page.locator('#viewport').click({position:{x:viewport!.width/2,y:viewport!.height/2}});
  await expect(page.locator('#probe')).toBeVisible();
  await expect(page.locator('#probe')).toContainText('O₂');
  await page.locator('#close-probe').click();
  // Legacy samples remain viewable, but no longer impersonate the new cache key.
  const fixture=(await (await page.request.get('/api/experiments')).json()).find((h:{featured?:boolean;config:{scene:string}})=>h.featured&&h.config.scene==='burner');
  await page.route('**/api/experiments',async route=>{
    if(route.request().method()==='POST')await route.fulfill({json:{id:fixture.id,status:'completed',progress:1,cached:true}});
    else await route.continue();
  });
  const [cached]=await Promise.all([
    page.waitForResponse(r=>r.url().endsWith('/api/experiments')&&r.request().method()==='POST'),
    page.locator('#compute').click(),
  ]);
  expect((await cached.json()).cached).toBe(true);
  await expect(page.locator('#empty-state')).toBeHidden({timeout:20000});
  await page.screenshot({path:'artifacts/ignis-desktop.png',fullPage:true});
  await page.getByRole('tab',{name:'Temperatura',exact:true}).click();
  await expect(page.locator('#legend')).toBeVisible();
  await page.locator('#cutaway').check();
  await expect(page.locator('#slice-control')).toBeVisible();
  await page.locator('#slice').fill('0.25');
  await page.screenshot({path:'artifacts/ignis-temperature.png',fullPage:true});
  await page.getByRole('tab',{name:'Przepływ',exact:true}).click();
  await page.getByRole('tab',{name:'Tlen',exact:true}).click();
  await page.getByRole('tab',{name:'Płomień',exact:true}).click();
  await page.locator('#number-fuel').fill('18');await page.locator('#number-fuel').dispatchEvent('change');
  await expect(page.locator('#param-fuel')).toHaveValue('18');
  await expect(page.locator('#compute-note')).toContainText('zachowuje');
  await page.locator('#reset').click();await expect(page.locator('#number-fuel')).toHaveValue('12');
  await page.locator('#about').click();await expect(page.locator('#details')).toBeVisible();
  await page.locator('.dialog-close').click();
  await page.locator('#presentation').click();await expect(page.locator('body')).toHaveClass('presenting');
  await page.keyboard.press('Escape');await expect(page.locator('body')).not.toHaveClass('presenting');
  expect(errors).toEqual([]);
});

test('continuous flame never restarts cold, ignition persists across frames and layers',async({page})=>{
  await page.goto('/');await expect(page.locator('#empty-state')).toBeHidden();
  await expect(page.locator('#viewport')).toHaveAttribute('data-flame-visible','true');
  for(let i=0;i<5;i++){
    await page.waitForTimeout(900);
    expect(Number((await page.locator('#current-time').innerText()).replace(',','.'))).toBeGreaterThan(0);
    await expect(page.locator('#viewport')).toHaveAttribute('data-flame-visible','true');
  }
  await page.locator('#ignition').click();await expect(page.locator('#ignition')).toHaveText('Zapłon');
  await expect(page.locator('#viewport')).toHaveAttribute('data-flame-visible','false');
  await page.getByRole('tab',{name:'Temperatura',exact:true}).click();
  await page.waitForTimeout(2300);await page.getByRole('tab',{name:'Płomień',exact:true}).click();
  await expect(page.locator('#viewport')).toHaveAttribute('data-flame-visible','false');
  await expect(page.locator('#fire-state')).toContainText('zgaszony');
  await page.locator('#ignition').click();await expect(page.locator('#viewport')).toHaveAttribute('data-flame-visible','true');
  await page.locator('#playback-mode').selectOption('physical');
  await page.locator('#timeline').fill('1.99');await page.locator('#play').click();
  await expect(page.locator('#play')).toHaveAttribute('aria-label','Odtwórz wynik');
  await expect(page.locator('#current-time')).toHaveText('2,00');
  await page.screenshot({path:'artifacts/ignis-ignition.png',fullPage:true});
});

test('partial preview grows, keeps prior result, and completes without resetting the selected time',async({page})=>{
  const history=await (await page.request.get('/api/experiments')).json();
  const fixture=history.find((h:{featured?:boolean;config:{scene:string}})=>h.featured&&h.config.scene==='burner');
  const native=await (await page.request.get(`/api/experiments/${fixture.id}/result`)).json();
  const id='e'.repeat(20),attempt='f'.repeat(32);let count=2,status='running';
  const job=()=>({id,attempt,status,progress:.2,config:native.config,previewFrames:count});
  await page.route('**/api/experiments',async route=>{if(route.request().method()==='POST')await route.fulfill({json:job()});else await route.continue()});
  await page.route(`**/api/experiments/${id}`,route=>route.fulfill({json:job()}));
  await page.route(`**/api/experiments/${id}/preview/manifest`,route=>route.fulfill({json:{...native,id,attempt,complete:false,revision:count,times:native.times.slice(0,count),extrema:native.extrema.slice(0,count)}}));
  await page.route(`**/api/experiments/${id}/preview/frames/*`,async route=>{
    const n=new URL(route.request().url()).pathname.split('/').at(-1);
    const response=await page.request.get(`/api/experiments/${fixture.id}/frames/${n}`);
    await route.fulfill({body:await response.body(),contentType:'application/octet-stream'});
  });
  await page.route(`**/api/experiments/${id}/result`,route=>route.fulfill({json:{...native,id,attempt,complete:true}}));
  await page.route(`**/api/experiments/${id}/frames/*`,async route=>{
    const n=new URL(route.request().url()).pathname.split('/').at(-1);const response=await page.request.get(`/api/experiments/${fixture.id}/frames/${n}`);
    await route.fulfill({body:await response.body(),contentType:'application/octet-stream'});
  });
  await page.goto('/');await expect(page.locator('#empty-state')).toBeHidden();
  await page.locator('#compute').click();await expect(page.locator('#preview-toggle')).toBeEnabled();
  await expect(page.locator('#result-label')).not.toContainText('CZĘŚCIOWY');
  await page.locator('#preview-toggle').click();await expect(page.locator('#result-label')).toContainText('CZĘŚCIOWY');
  await expect(page.locator('#end-time')).toHaveText('0,10');
  count=8;await expect(page.locator('#end-time')).toHaveText('0,70');
  await page.locator('#preview-toggle').click();await expect(page.locator('#result-label')).not.toContainText('CZĘŚCIOWY');
  await page.locator('#preview-toggle').click();await expect(page.locator('#result-label')).toContainText('CZĘŚCIOWY');
  await page.getByRole('tab',{name:'Tlen',exact:true}).click();
  await page.locator('#timeline').fill('0.5');await expect(page.locator('#current-time')).toHaveText('0,50');
  status='completed';await expect(page.locator('#result-label')).not.toContainText('CZĘŚCIOWY');
  await expect(page.locator('#current-time')).toHaveText('0,50');
  await expect(page.getByRole('tab',{name:'Tlen',exact:true})).toHaveAttribute('aria-selected','true');
});

test('preview failure does not hide a solver error or discard the prior result',async({page})=>{
  const id='d'.repeat(20);let failed=false;
  await page.route('**/api/experiments',async route=>{
    if(route.request().method()==='POST')await route.fulfill({json:{id,status:'running',progress:0}});
    else await route.continue();
  });
  await page.route(`**/api/experiments/${id}`,route=>route.fulfill({json:{id,status:failed?'failed':'running',progress:.1,error:'Kontrolowany błąd solvera'}}));
  await page.route(`**/api/experiments/${id}/preview/manifest`,route=>route.fulfill({status:503,json:{detail:'Podgląd niedostępny'}}));
  await page.goto('/');await expect(page.locator('#empty-state')).toBeHidden();
  const before=await page.locator('#result-conditions').innerText();
  await page.locator('#compute').click();failed=true;
  await expect(page.locator('#error-message')).toContainText('Kontrolowany błąd solvera');
  await expect(page.locator('#result-conditions')).toHaveText(before);
  await expect(page.locator('#compute')).toBeEnabled();
});

test('mobile layout has no horizontal overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  await expect(page.locator('#empty-state')).toBeHidden({timeout:20000});
  await page.locator('#play').click();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'artifacts/ignis-mobile.png',fullPage:true});
});

test('all three native examples and their layers open',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.setViewportSize({width:1440,height:1080});await page.goto('/');
  await expect(page.locator('#empty-state')).toBeHidden({timeout:20000});
  await page.locator('#play').click();
  for(const id of ['burner','candle','wood']){
    await page.locator(`[data-scene="${id}"]`).click();
    await expect(page.locator('#empty-state')).toBeHidden({timeout:20000});
    await expect(page.locator('#metric-temp')).not.toContainText('—');
    if(id==='wood')await expect(page.locator('#number-duration')).toHaveValue('15');
    await page.screenshot({path:`artifacts/ignis-${id}.png`,fullPage:true});
    await page.getByRole('tab',{name:'Temperatura',exact:true}).click();
    await expect(page.locator('#legend')).toBeVisible();
    await page.getByRole('tab',{name:'Płomień',exact:true}).click();
  }
  expect(errors).toEqual([]);
});

test('without WebGL the numeric laboratory remains usable',async({page})=>{
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,type:string,...args:unknown[]){if(type.startsWith('webgl'))return null;return (original as Function).apply(this,[type,...args])} as typeof original});
  await page.goto('/');
  await expect(page.locator('.graphics-error')).toContainText('WebGL2');
  await expect(page.locator('#metric-temp')).not.toContainText('—',{timeout:20000});
  await expect(page.locator('#compute')).toBeEnabled();
});
