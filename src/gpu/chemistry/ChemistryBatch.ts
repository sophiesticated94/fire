import type {IntegrationOptions} from './ImplicitTile';
import type {GpuImplicitTile} from './GpuImplicitTile';
import type {TileCheckpoint} from './ChemistryCheckpoint';

export interface BatchOptions extends Omit<IntegrationOptions,'checkpoint'|'onCheckpoint'> {
  tileSize?:number;
  sliceWallMs?:number;
  loadTile?:(tile:number)=>Promise<TileCheckpoint|undefined>;
  saveTile?:(tile:number,checkpoint:TileCheckpoint)=>Promise<void>;
}

/** Round-robin scheduler. No cell is removed when it rejects a trial.
 * Durable callbacks allow large campaigns to keep only one tile resident.
 * Tile checkpoints are the authoritative output, including partial results.
 */
export async function integrateBatch(engine:GpuImplicitTile, initial:number[][], duration:number, signal:AbortSignal|undefined, options:BatchOptions={}){
  const invocationStart=performance.now();initial=initial.map(s=>s.slice());options={...options,sampleTimes:options.sampleTimes?.slice()};
  const tileSize=options.tileSize??256,slice=options.sliceWallMs??5000,limit=options.maxWallMs??60000;
  if(!Number.isInteger(tileSize)||tileSize<1||tileSize>256||initial.length<1||initial.length>65536||!Number.isFinite(slice)||slice<1100||!Number.isFinite(limit)||limit<=0)throw Error('Invalid chemistry batch');
  if(Boolean(options.loadTile)!==Boolean(options.saveTile))throw Error('Durable chemistry batches require both loadTile and saveTile');
  const count=Math.ceil(initial.length/tileSize),memory=new Map<number,TileCheckpoint>(),completed=new Set<number>();
  const start=invocationStart;let visited=0,stopReason='wall-limit';
  const load=options.loadTile??(async(tile:number)=>memory.get(tile));
  const save=options.saveTile??(async(tile:number,c:TileCheckpoint)=>{memory.set(tile,c);});
  outer:while(completed.size<count){
    for(let tile=0;tile<count;tile++){
      if(completed.has(tile))continue;
      if(signal?.aborted){stopReason='cancelled';break outer;}
      const remaining=limit-(performance.now()-start);
      if(remaining<1100)break outer;
      const checkpoint=await load(tile);
      // Integrator validates even completed checkpoints before accepting them.
      const result=await engine.integrate(initial.slice(tile*tileSize,(tile+1)*tileSize),duration,signal,
        {...options,checkpoint,maxWallMs:Math.min(slice,remaining),onCheckpoint:undefined});
      visited++;await save(tile,result.checkpoint);
      if(result.stopReason==='completed')completed.add(tile);
      else if(result.stopReason!=='wall-limit'){stopReason=result.stopReason;break outer;}
    }
  }
  if(completed.size===count)stopReason='completed';
  return {reactors:initial.length,tiles:count,completedTiles:completed.size,visitedSlices:visited,stopReason,
    complete:completed.size===count,wallMs:performance.now()-start,
    checkpoints:options.saveTile?undefined:Array.from(memory.entries()).map(([tile,checkpoint])=>({tile,checkpoint}))};
}
