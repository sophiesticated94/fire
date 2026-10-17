import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {atomicWrite,readCheckpoint,CampaignBudget} from '../scripts/chemistry_checkpoint.mjs';

test('atomic checkpoint retains verified previous generation and rejects tampering',()=>{
  const dir=mkdtempSync(join(tmpdir(),'ignis-chemistry-'));
  try{
    const path=join(dir,'checkpoint.json');atomicWrite(path,{time:1});
    writeFileSync(path+'.tmp','interrupted write');assert.deepEqual(readCheckpoint(path),{time:1});
    atomicWrite(path,{time:2});assert.deepEqual(readCheckpoint(path),{time:2});assert.deepEqual(readCheckpoint(path+'.previous'),{time:1});
    const corrupted=JSON.parse(readFileSync(path,'utf8'));corrupted.payload.time=3;writeFileSync(path,JSON.stringify(corrupted));
    assert.throws(()=>readCheckpoint(path),/integrity/);assert.deepEqual(readCheckpoint(path+'.previous'),{time:1});
  }finally{assert.ok(dir.startsWith(join(tmpdir(),'ignis-chemistry-')));rmSync(dir,{recursive:true});}
});

test('exhausted CLI budget never launches GPU and cannot reset on restart',()=>{
  const dir=mkdtempSync(join(tmpdir(),'ignis-chemistry-budget-'));
  try{
    const args=['scripts/chemistry_campaign.mjs','--output',dir,'--budget-file',join(dir,'budget.json'),'--budget-ms','1'];
    const first=spawnSync(process.execPath,args,{encoding:'utf8',timeout:15000});
    assert.equal(first.status,2);
    const a=readCheckpoint(join(dir,'chemistry-campaign.json'));
    assert.equal(a.status,'INCOMPLETE');assert.equal(a.adapter,undefined);assert.match(a.error,/budget exhausted/);
    const second=spawnSync(process.execPath,args,{encoding:'utf8',timeout:15000});assert.equal(second.status,2);
    const b=readCheckpoint(join(dir,'chemistry-campaign.json'));
    assert.ok(b.budget.usedMs>=a.budget.usedMs);assert.equal(b.status,'INCOMPLETE');
  }finally{assert.ok(dir.startsWith(join(tmpdir(),'ignis-chemistry-budget-')));rmSync(dir,{recursive:true});}
});

test('campaign budget accumulates resumed sessions and crashed leases',()=>{
  const b=new CampaignBudget({usedMs:100,lease:{startedAt:Date.now()-1000,reservedMs:200}},500);
  assert.ok(b.elapsed()>=300 && b.elapsed()<350);assert.ok(b.remaining()<=200);
  const next=new CampaignBudget(b.snapshot(),500);assert.ok(next.elapsed()>=b.base);
  assert.throws(()=>new CampaignBudget({usedMs:-1}),/accounting/);
});

test('report pairs every historical solution with its immutable matrix',()=>{
  const dir=mkdtempSync(join(tmpdir(),'ignis-chemistry-report-'));
  try{
    const matrices=[join(dir,'first.json'),join(dir,'second.json')];
    writeFileSync(matrices[0],JSON.stringify({systems:[[2,0,4,0,3,6]]}));
    writeFileSync(matrices[1],JSON.stringify({systems:[[5,0,5,0,7,7]]}));
    const snapshot=join(dir,'snapshot.json');writeFileSync(snapshot,'{}');
    atomicWrite(join(dir,'tile.checkpoint.json'),{caseIds:[0],checkpoint:{initial:[Array(54).fill(0)],sampleTimes:[1]}});
    const probe=x=>({wallMs:1,storageBytes:32,systems:[{solution:x,failed:false}]});
    const campaign={version:'test',status:'INCOMPLETE',results:[{id:'tile',inspectionPath:snapshot,profile:{wallMs:1,statusReads:1,submissions:1,gpuMs:{}}}],
      precisionProbes:matrices.map((inspection,i)=>({id:'tile',inspection,reports:[],single:probe(i?[1,1]:[2,2]),extended:probe(i?[1,1]:[2,2])}))};
    const manifest=join(dir,'chemistry-campaign.json'),output=join(dir,'report.json');atomicWrite(manifest,campaign);
    const args=['scripts/report_chemistry_campaign.mjs','--output',output,dir];
    const valid=spawnSync(process.execPath,args,{encoding:'utf8',timeout:15000});assert.equal(valid.status,0,valid.stderr);
    const reports=JSON.parse(readFileSync(output,'utf8')).measurements[0].precisionProbes;
    assert.deepEqual(reports.map(p=>p.singleBackwardErrors),[[0],[0]]);
    campaign.precisionProbes[0].inspection=matrices[1];atomicWrite(manifest,campaign);
    const invalid=spawnSync(process.execPath,args,{encoding:'utf8',timeout:15000});
    assert.equal(invalid.status,1);assert.match(invalid.stderr,/matrix path reused/);
  }finally{assert.ok(dir.startsWith(join(tmpdir(),'ignis-chemistry-report-')));rmSync(dir,{recursive:true});}
});
