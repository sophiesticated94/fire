import {probeLinearPrecision} from '../../src/gpu/chemistry/LinearPrecisionProbe';
import {Gri30} from '../../src/gpu/chemistry/Gri30';
import chemistryFixtures from './chemistry-fixtures.json';
import reactorFixtures from './reactor-fixtures.json';
import {GpuEngine} from '../../src/gpu/GpuEngine';
import {GpuGrid,AIR} from '../../src/gpu/GpuGrid';
import {CpuReference} from './CpuReference';
(window as any).lab={Gri30,probeLinearPrecision,chemistryFixtures,reactorFixtures,GpuEngine,GpuGrid,AIR,CpuReference,engine:null,async create(options={}){this.engine?.dispose();this.engine=await GpuEngine.create({...options,testReadback:true});return this.engine.metrics}};
