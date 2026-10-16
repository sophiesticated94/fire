import {test,expect} from '@playwright/test';
test('GPU mode retains state, pauses in FDS and draws all layers from shared storage',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.goto('/');await expect(page.locator('#result-label')).toContainText('FDS',{timeout:30000});
 await page.click('#mode-gpu');await expect(page.locator('#gpu-start')).toBeEnabled({timeout:30000});
 await page.click('#gpu-start');await expect.poll(()=>page.locator('#gpu-time').textContent(),{timeout:30000}).not.toBe('0,00 s');
 await page.click('#gpu-start');await page.waitForTimeout(1200);const time=await page.locator('#gpu-time').textContent();await page.waitForTimeout(600);expect(await page.locator('#gpu-time').textContent()).toBe(time);
 for(const layer of ['flow','density','temperature']){await page.click(`[data-gpu-layer="${layer}"]`);await page.waitForTimeout(500);}
 await page.check('#gpu-cut');await page.click('[data-gpu-view="side"]');
 await page.screenshot({path:'artifacts/gpu/interface.png',fullPage:true});
 await page.click('#mode-fds');await expect(page.locator('#viewport')).toBeVisible();await page.waitForTimeout(500);await page.click('#mode-gpu');expect(await page.locator('#gpu-time').textContent()).toBe(time);
 for(let i=0;i<5;i++){await page.click('#mode-fds');await page.click('#mode-gpu');expect(await page.locator('#gpu-viewport canvas').count()).toBe(1);expect(await page.locator('#viewport canvas').count()).toBe(1);expect(await page.locator('#gpu-time').textContent()).toBe(time);}
 await page.click('#gpu-reset');await expect(page.locator('#gpu-time')).toHaveText('0,00 s');
 expect(errors).toEqual([]);
});
test('unavailable WebGPU leaves the FDS view accessible',async({page})=>{
 await page.addInitScript(()=>Object.defineProperty(navigator,'gpu',{value:undefined}));await page.goto('/');await page.click('#mode-gpu');await expect(page.locator('#gpu-error')).toContainText('nie udostępnia WebGPU');await page.click('#mode-fds');await expect(page.locator('#viewport')).toBeVisible();
});
test('running GPU suspends in FDS and resumes without wall-clock catch-up',async({page})=>{
 await page.goto('/');await page.click('#mode-gpu');await expect(page.locator('#gpu-start')).toBeEnabled({timeout:30000});await page.click('#gpu-start');await expect.poll(()=>page.locator('#gpu-time').textContent()).not.toBe('0,00 s');
 await page.click('#mode-fds');await expect(page.locator('#gpu-laboratory')).toHaveAttribute('data-busy','false',{timeout:15000});const time=await page.locator('#gpu-time').textContent();await page.waitForTimeout(800);expect(await page.locator('#gpu-time').textContent()).toBe(time);
 await page.click('#mode-gpu');await expect.poll(()=>page.locator('#gpu-time').textContent()).not.toBe(time);
});
