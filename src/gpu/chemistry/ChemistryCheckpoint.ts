export const CHEMISTRY_VERSION = 'gri30-gpu-state-machine-7';
export const CONTROL_STRIDE = 40;
export const TOLERANCES = {rtol: 1e-5, speciesAtol: 1e-12, temperatureAtol: 1e-3} as const;

// Only accepted states are durable. A resumed trial restarts from accepted;
// partially factored matrices and partially applied Newton updates are discarded.
export interface TileCheckpoint {
  schema: 4;
  integrator: typeof CHEMISTRY_VERSION;
  mechanismSha256: string;
  precision: 'float32'|'compensated-state';
  acceptedHigh?:number[][];
  acceptedLow?:number[][];
  targetEnthalpyLow?:number[];
  linearSolver: 'lu'|'refined-lu';
  localErrorTarget: number;
  tolerances: typeof TOLERANCES;
  initial: number[][];
  accepted: number[][];
  control: number[];
  sampleTimes: number[];
  trajectory: number[];
  duration: number;
}

export function validateCheckpoint(c: TileCheckpoint, initial: number[][], duration: number,
  samples: number[], mechanism: string, linearSolver:'lu'|'refined-lu',localErrorTarget=1,precision:'float32'|'compensated-state'='float32') {
  if (c.schema !== 4 || c.integrator !== CHEMISTRY_VERSION || c.mechanismSha256 !== mechanism || c.localErrorTarget!==localErrorTarget ||
      c.precision !== precision || c.linearSolver!==linearSolver || JSON.stringify(c.tolerances) !== JSON.stringify(TOLERANCES) ||
      c.duration !== duration || JSON.stringify(c.initial) !== JSON.stringify(initial) ||
      JSON.stringify(c.sampleTimes) !== JSON.stringify(samples) || c.accepted.length !== initial.length ||
      c.control.length !== initial.length * CONTROL_STRIDE ||
      c.trajectory.length !== initial.length * samples.length * 54 ||
      c.control.some(x => !Number.isFinite(x)) || c.trajectory.some(x => !Number.isFinite(x)) ||
      c.accepted.some(s => s.length !== 54 || s.some(x => !Number.isFinite(x)) ||
        s[0] < 300 || s[0] > 3000 || s.slice(1).some(y => y < 0) ||
        Math.abs(s.slice(1).reduce((a,b) => a+b,0)-1) > 1e-5))
    throw Error('Incompatible or corrupt chemistry checkpoint');
  if(precision==='compensated-state'){
    if(c.targetEnthalpyLow?.length!==initial.length || c.targetEnthalpyLow.some(v=>!Number.isFinite(v) || Math.fround(v)!==v))throw Error('Invalid compensated enthalpy checkpoint');
    if(c.acceptedHigh?.length!==initial.length || c.acceptedLow?.length!==initial.length ||
      c.accepted.some((s,i)=>c.acceptedHigh![i]?.length!==54 || c.acceptedLow![i]?.length!==54 ||
        s.some((v,j)=>!Number.isFinite(c.acceptedLow![i][j]) || !Number.isFinite(c.acceptedHigh![i][j]) ||
          Math.fround(c.acceptedHigh![i][j])!==c.acceptedHigh![i][j] || Math.fround(c.acceptedLow![i][j])!==c.acceptedLow![i][j] ||
          v!==c.acceptedHigh![i][j]+c.acceptedLow![i][j])))throw Error('Invalid compensated state checkpoint');
  }
  for (let i=0;i<initial.length;i++) {
    const p=c.control.slice(i*CONTROL_STRIDE,(i+1)*CONTROL_STRIDE);
    if(p[39]!==localErrorTarget)throw Error('Checkpoint local error budget mismatch');
    if (p[0]<0 || p[0]>Math.fround(duration) || !(p[1]>0) || p[20]<0 ||
        p[20]>samples.length || !Number.isInteger(p[20]) || p[9]<0 || p[9]>2 || p[19]<0 || p[19]>1 ||
        [8,9,10,11,12,13,14,15,19,20,24,25,28,29,30,31,32,33,34,35,36].some(i=>!Number.isInteger(p[i]) || p[i]<0 || p[i]>16777216) || ![1,2,3,4,5,6].includes(p[8]))
      throw Error('Invalid checkpoint controller');
    const physical=p[0]-p[27];
    if((p[8]===5 && (p[20]!==samples.length || physical!==Math.fround(duration))) ||
      (p[8]!==5 && p[20]===samples.length) ||
      (p[20]>0 && physical<Math.fround(samples[p[20]-1])-1e-15) ||
      (p[20]<samples.length && physical>Math.fround(samples[p[20]])+1e-15))
      throw Error('Inconsistent checkpoint sampling progress');
  }
}

export enum ReactorPhase {Evaluate=1, Apply=2, Damping=3, Retry=4, Complete=5, Failed=6}
export interface ReactorProgress {
  time:number;dt:number;phase:ReactorPhase;newtonIteration:number;dampingAttempt:number;
  attempts:number;rejected:number;accepted:number;rejectionReason:number;
  status:'active'|'retry'|'complete'|'failed';
}
export function reactorProgress(p:number[]):ReactorProgress {
  return {time:p[0]-p[27],dt:p[1],phase:p[8],newtonIteration:p[10],dampingAttempt:p[11],
    attempts:p[12],rejected:p[13],accepted:p[14],rejectionReason:p[15],
    status:p[8]===5?'complete':p[8]===6?'failed':p[8]===4?'retry':'active'};
}
