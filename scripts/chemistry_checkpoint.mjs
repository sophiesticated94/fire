import {createHash} from 'node:crypto';
import {openSync,writeFileSync,fsyncSync,closeSync,renameSync,readFileSync,existsSync,copyFileSync,mkdirSync} from 'node:fs';
import {dirname} from 'node:path';

export function envelope(payload){
  const json=JSON.stringify(payload);
  return {schema:1,sha256:createHash('sha256').update(json).digest('hex'),payload};
}
export function atomicWrite(path,payload){
  mkdirSync(dirname(path),{recursive:true});
  const temp=path+'.tmp',fd=openSync(temp,'w');
  try{writeFileSync(fd,JSON.stringify(envelope(payload)));fsyncSync(fd);}finally{closeSync(fd);}
  // A failed replacement leaves both the old primary and a verified backup.
  if(existsSync(path)){readCheckpoint(path);copyFileSync(path,path+'.previous');}
  renameSync(temp,path);
}
export function readCheckpoint(path){
  const data=JSON.parse(readFileSync(path,'utf8'));
  if(data.schema!==1 || data.sha256!==envelope(data.payload).sha256)throw Error('Checkpoint integrity verification failed: '+path);
  return data.payload;
}
export class CampaignBudget {
  constructor(saved,limit=8*60*60*1000){
    if(!Number.isFinite(limit)||limit<=0)throw Error('Invalid campaign limit');
    this.limit=limit;this.used=saved?.usedMs??0;
    // A crashed session is charged for its durable lease. This conservative
    // charge prevents restarting a killed browser from resetting the budget.
    if(saved?.lease)this.used+=Math.min(saved.lease.reservedMs,Math.max(0,Date.now()-saved.lease.startedAt));
    if(!Number.isFinite(this.used)||this.used<0)throw Error('Invalid campaign accounting');
    this.started=performance.now();this.base=this.used;
  }
  elapsed(){return this.base+performance.now()-this.started;}
  remaining(){return Math.max(0,this.limit-this.elapsed());}
  snapshot(reservedMs=0){return {limitMs:this.limit,usedMs:this.elapsed(),lease:reservedMs?{startedAt:Date.now(),reservedMs}:null};}
}
