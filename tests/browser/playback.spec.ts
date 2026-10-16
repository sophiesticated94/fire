import {test,expect} from '@playwright/test';
import {burningWindow,bounce} from '../../src/playback';
import type {Result} from '../../src/types';

test('burning interval excludes cold ignition and extinction, bounce remains bounded',()=>{
  const result={times:[0,.1,.2,.3,.4,.5],extrema:[],series:{Time:[0,.1,.2,.3,.4,.5],HRR:[0,1,6,10,8,0]}} as unknown as Result;
  expect(burningWindow(result)).toEqual([.2,.4]);
  let time=.2,direction=1;
  for(let i=0;i<100;i++){const next=bounce(time,.037,direction,[.2,.4]);time=next.time;direction=next.direction;expect(time).toBeGreaterThanOrEqual(.2);expect(time).toBeLessThanOrEqual(.4)}
  result.series.HRR.fill(0);expect(burningWindow(result)).toBeUndefined();
  expect(bounce(1,10,1,[1,1])).toEqual({time:1,direction:1});
});
