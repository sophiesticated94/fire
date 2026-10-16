import type {Result} from './types';

/** Longest contiguous burning interval; never invent a flame in a cold result. */
export function burningWindow(result:Result):[number,number]|undefined{
  const ts=result.series.Time??[],power=result.series.HRR??[];
  const heat=result.times.map((t,i)=>{
    if(!power.length)return result.extrema[i]?.hrr??0;
    let closest=0;for(let j=1;j<ts.length;j++)if(Math.abs(ts[j]-t)<Math.abs(ts[closest]-t))closest=j;
    return power[closest]??0;
  });
  const peak=Math.max(0,...heat);if(peak<=1e-6)return;
  let start=-1,best:[number,number]|undefined;
  for(let i=0;i<=heat.length;i++){
    if(i<heat.length&&heat[i]>=peak*.5){if(start<0)start=i}
    else if(start>=0){const span:[number,number]=[result.times[start],result.times[i-1]];if(!best||span[1]-span[0]>best[1]-best[0])best=span;start=-1}
  }
  return best;
}

export function bounce(time:number,delta:number,direction:number,window:[number,number]):{time:number;direction:number}{
  const [start,end]=window,length=end-start;
  if(length<=0)return {time:start,direction:1};
  // A triangular phase handles both ends without a cold restart or overshoot.
  const position=Math.max(0,Math.min(length,time-start));
  let phase=(direction>0?position:2*length-position)+delta;
  phase=((phase%(2*length))+2*length)%(2*length);
  return {time:start+(phase<=length?phase:2*length-phase),direction:phase<length?1:-1};
}
