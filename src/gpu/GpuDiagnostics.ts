export interface GpuStepDiagnostics {
  time:number;dt:number;steps:number;iterations:number;mass:number;enthalpy:number;temperature:number;densityMin:number;densityMax:number;
  speed:number;cfl:number;divergenceRms:number;divergenceMax:number;normalizedDivergence:number;normalizedMaximum:number;
  expansionFluxError:number;massError:number;cumulativeMassError:number;energyError:number;heaterPower:number;
  gpuMs:number|null;wallMs:number;readbackBytes:number;allocatedBytes:number;adapter:Record<string,unknown>;
}
export function quantile(a:number[],p:number){const b=[...a].sort((a,b)=>a-b);return b[Math.min(b.length-1,Math.floor(p*b.length))]??0}
export function finite(values:ArrayLike<number>){for(let i=0;i<values.length;i++)if(!Number.isFinite(values[i]))throw Error('Niefinitywne pole GPU');}
