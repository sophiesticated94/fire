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
