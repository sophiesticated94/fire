import {GpuEngine} from '../../src/gpu/GpuEngine';
import {GpuGrid,AIR} from '../../src/gpu/GpuGrid';
import {CpuReference} from './CpuReference';
(window as any).lab={GpuEngine,GpuGrid,AIR,CpuReference,engine:null,async create(options={}){this.engine?.dispose();this.engine=await GpuEngine.create({...options,testReadback:true});return this.engine.metrics}};
