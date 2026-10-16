import {Scene,PerspectiveCamera,Mesh,BoxGeometry,MeshBasicNodeMaterial,BackSide,Vector3,Color,EdgesGeometry,LineSegments,LineBasicMaterial,GridHelper,Raycaster,Vector2,Plane,InstancedMesh,ConeGeometry} from 'three/webgpu';
import {uniform,wgslFn,positionLocal,storage,vec4,vec3,instanceIndex} from 'three/tsl';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import type {GpuEngine} from '../gpu/GpuEngine';

// Both compute and shading bind the same GPUBuffer-backed attributes. No volume readback.
const volume=`fn volume(at:vec3f,eye:vec3f,r:ptr<storage,array<f32>,read>,v:ptr<storage,array<f32>,read>,layer:f32,cut:f32,scale:f32)->vec4f {
 let ray=normalize(at-eye);let inv=1./ray;let a=(-vec3f(.5)-eye)*inv;let b=(vec3f(.5)-eye)*inv;
 let near=max(max(min(a.x,b.x),min(a.y,b.y)),min(a.z,b.z));let far=min(min(max(a.x,b.x),max(a.y,b.y)),max(a.z,b.z));
 var colour=vec3f(0.);var alpha=0.;let start=max(near,0.);let ds=(far-start)/96.;
 for(var j=0;j<96;j++) {let p=eye+ray*(start+(f32(j)+.5)*ds)+.5;if(cut>.5&&p.z>.5){continue;}
 let q=clamp(vec3i(vec3f(p.x*32.,p.z*32.,p.y*64.)),vec3i(0),vec3i(31,31,63));let id=u32((q.z*32+q.y)*32+q.x);
 let den=(*r)[id];let t=101325./(287.05*den);var value=clamp((t-293.15)/scale,0.,1.);
 var rgb=mix(vec3f(.14,.42,.61),vec3f(1.,.52,.19),value);
 if(layer>1.5){value=clamp((1.204118-den)/.15,0.,1.);rgb=mix(vec3f(.12,.68,.75),vec3f(.94,.79,.48),value);}
 if(layer>.5&&layer<1.5){let ix=u32((q.z*32+q.y)*33+q.x);let iy=33u*32u*64u+u32((q.z*33+q.y)*32+q.x);let iz=33u*32u*64u+32u*33u*64u+id;let u=vec3f(((*v)[ix]+(*v)[ix+1u])*.5,((*v)[iy]+(*v)[iy+32u])*.5,((*v)[iz]+(*v)[iz+1024u])*.5);value=clamp(length(u)/.4,0.,1.);rgb=mix(vec3f(.1,.55,.65),vec3f(.9,.87,.58),value);}
 let opacity=1.-exp(-value*ds*6.);colour+=(1.-alpha)*opacity*rgb;alpha+=(1.-alpha)*opacity;if(alpha>.97){break;}
 }return vec4f(colour/max(alpha,.00001),alpha);
}`;

export class WebGpuFireScene {
 readonly scene=new Scene();readonly camera=new PerspectiveCamera(38,1,.001,10);readonly controls:OrbitControls;
 private eye=uniform(new Vector3());private layer=uniform(0);private cut=uniform(0);private scale=uniform(20);
 private materials:MeshBasicNodeMaterial[][]=[];private volume:Mesh;private observer:ResizeObserver;private disposed=false;private arrows:InstancedMesh;private arrowMaterials:MeshBasicNodeMaterial[]=[];private showFlow=false;
 onProbe?:(values:number[])=>void;
 constructor(readonly host:HTMLElement,readonly engine:GpuEngine){
   const r=engine.renderer;host.append(r.domElement);r.setPixelRatio(Math.min(devicePixelRatio,1.5));r.setClearColor(new Color('#101513'));
   this.camera.position.set(.38,.24,.48);this.controls=new OrbitControls(this.camera,r.domElement);this.controls.target.set(0,.15,0);this.controls.enableDamping=true;this.controls.minDistance=.24;this.controls.maxDistance=1.2;this.controls.update();
   for(const rho of engine.fields.rho){const row:MeshBasicNodeMaterial[]=[];for(const flow of engine.fields.velocity){
     const colour=wgslFn(volume)({at:positionLocal,eye:this.eye,r:storage(rho.attribute,'float',rho.count).toReadOnly(),v:storage(flow.attribute,'float',flow.count).toReadOnly(),layer:this.layer,cut:this.cut,scale:this.scale}) as ReturnType<typeof vec4>;
     const material=new MeshBasicNodeMaterial({transparent:true,side:BackSide,depthWrite:false});material.colorNode=colour.rgb;material.opacityNode=colour.a;row.push(material);
   }this.materials.push(row);}
   this.volume=new Mesh(new BoxGeometry(1,1,1),this.materials[0][0]);this.volume.scale.set(.16,.32,.16);this.volume.position.y=.16;this.scene.add(this.volume);
   for(const flow of engine.fields.velocity){
     const node=wgslFn(`fn glyph(local:vec3f,id:u32,v:ptr<storage,array<f32>,read>,cut:f32)->vec3f {
      let q=vec3i(i32(id%8u)*4+2,i32((id/8u)%8u)*4+2,i32(id/64u)*4+2);let cell=u32((q.z*32+q.y)*32+q.x);
      let ix=u32((q.z*32+q.y)*33+q.x);let iy=33u*32u*64u+u32((q.z*33+q.y)*32+q.x);let iz=33u*32u*64u+32u*33u*64u+cell;
      let u=vec3f(((*v)[ix]+(*v)[ix+1u])*.5,((*v)[iz]+(*v)[iz+1024u])*.5,((*v)[iy]+(*v)[iy+32u])*.5);let speed=length(u);let direction=u/max(speed,1e-10);let seed=select(vec3f(0.,1.,0.),vec3f(1.,0.,0.),abs(direction.y)>.9);let right=normalize(cross(direction,seed)+vec3f(1e-20));let back=cross(right,direction);
      let size=select(min(.017,speed*.12),0.,speed<.0001||(cut>.5&&q.y>16));let centre=vec3f((f32(q.x)+.5)*.005-.08,(f32(q.z)+.5)*.005,(f32(q.y)+.5)*.005-.08);
      return centre+(right*local.x*.2+direction*local.y+back*local.z*.2)*size;
     }`)({local:positionLocal,id:instanceIndex,v:storage(flow.attribute,'float',flow.count).toReadOnly(),cut:this.cut}) as ReturnType<typeof vec3>;
     const m=new MeshBasicNodeMaterial({color:0xb9dacd});m.positionNode=node;this.arrowMaterials.push(m);
   }
   this.arrows=new InstancedMesh(new ConeGeometry(.5,1,5),this.arrowMaterials[0],1024);this.arrows.frustumCulled=false;this.arrows.visible=false;this.scene.add(this.arrows);
   const bounds=new LineSegments(new EdgesGeometry(new BoxGeometry(.16,.32,.16)),new LineBasicMaterial({color:0x65796d,transparent:true,opacity:.35}));bounds.position.y=.16;this.scene.add(bounds);
   const grid=new GridHelper(.3,12,0x81705a,0x283a31);grid.position.y=-.001;this.scene.add(grid);
   let down=[0,0];r.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY]});
   r.domElement.addEventListener('pointerup',e=>{if(Math.hypot(e.clientX-down[0],e.clientY-down[1])<4)void this.pick(e)});
   this.observer=new ResizeObserver(()=>this.resize());this.observer.observe(host);this.resize();
 }
 resize(){const w=this.host.clientWidth,h=this.host.clientHeight;if(w&&h){this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.engine.renderer.setSize(w,h)}}
 setLayer(name:string){this.layer.value={temperature:0,flow:1,density:2}[name]??0;this.showFlow=name==='flow';this.arrows.visible=this.showFlow;}
 setCutaway(value:boolean){this.cut.value=Number(value)}
 setRange(value:number){this.scale.value=value}
 view(name:string){this.camera.position.set(...(name==='side'?[0,.16,.55]:name==='top'?[.001,.7,.001]:[.38,.24,.48]) as [number,number,number]);this.controls.target.set(0,.15,0);this.controls.update()}
 render(){if(this.disposed||document.hidden)return;this.controls.update();this.volume.updateMatrixWorld();this.eye.value.copy(this.volume.worldToLocal(this.camera.position.clone()));this.volume.material=this.materials[this.engine.state][this.engine.velocity];this.arrows.material=this.arrowMaterials[this.engine.velocity];this.engine.renderer.render(this.scene,this.camera)}
 private async pick(e:PointerEvent){
   // Probe on the vertical central section; reported coordinates are cell centres.
   const box=this.host.getBoundingClientRect();const ray=new Raycaster();ray.setFromCamera(new Vector2((e.clientX-box.left)/box.width*2-1,-(e.clientY-box.top)/box.height*2+1),this.camera);
   const p=ray.ray.intersectPlane(new Plane(new Vector3(0,0,1),0),new Vector3());if(!p||Math.abs(p.x)>.08||p.y<0||p.y>.32)return;
   const g=this.engine.grid;const i=Math.min(31,Math.floor((p.x+.08)/.005)),k=Math.min(63,Math.floor(p.y/.005));const values=await this.engine.probeAt(g.index(i,16,k));if(values)this.onProbe?.([...values,(i+.5)*.005,.0825,(k+.5)*.005]);
 }
 dispose(){this.disposed=true;this.observer.disconnect();this.controls.dispose();this.scene.traverse(o=>{const mesh=o as Mesh;mesh.geometry?.dispose();if(mesh.material){for(const m of Array.isArray(mesh.material)?mesh.material:[mesh.material])m.dispose();}});for(const row of this.materials)for(const m of row)m.dispose();for(const m of this.arrowMaterials)m.dispose();this.arrows.dispose();this.engine.renderer.domElement.remove();}
}
