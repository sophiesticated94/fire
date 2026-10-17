import {StorageBufferAttribute} from 'three/webgpu';
import {storage} from 'three/tsl';
import type {GpuGrid} from './GpuGrid';
export class Field {
  attribute:StorageBufferAttribute;node:ReturnType<typeof storage<'float'>>;
  constructor(public count:number){this.attribute=new StorageBufferAttribute(count,1);this.node=storage(this.attribute,'float',count)}
}
export class GpuFields {
  rho:Field[];velocity:Field[];pressure:Field;rhs:Field;source:Field;chunks:Field;metrics:Field;probe:Field;
  constructor(public grid:GpuGrid){
    this.rho=[new Field(grid.count),new Field(grid.count)];this.velocity=[new Field(grid.faces),new Field(grid.faces),new Field(grid.faces)];
    this.pressure=new Field(grid.count);this.rhs=new Field(grid.count);this.source=new Field(grid.count*2);
    this.chunks=new Field(Math.ceil(grid.count/64)*24);this.metrics=new Field(32);this.probe=new Field(8);
  }
  all(){return [...this.rho,...this.velocity,this.pressure,this.rhs,this.source,this.chunks,this.metrics,this.probe]}
  get bytes(){return this.all().reduce((s,f)=>s+f.count*4,0)}
}
