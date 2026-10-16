import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import type {Layer,Result,SceneId} from './types';

const vertex = `varying vec3 localPosition; void main(){localPosition=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`;
const fragment = `
precision highp float;
precision highp sampler3D;
uniform sampler3D field;
uniform vec3 localCamera;
uniform int layer;
uniform bool cutaway;
uniform float sliceY;
uniform float opacityScale;
uniform float ambient;
varying vec3 localPosition;
vec3 heatmap(float t){
  vec3 a=vec3(.06,.08,.20),b=vec3(.16,.32,.61),c=vec3(.89,.26,.10),d=vec3(1.,.92,.57);
  return t<.33?mix(a,b,t*3.):t<.66?mix(b,c,(t-.33)*3.):mix(c,d,clamp((t-.66)*3.,0.,1.));
}
void main(){
  vec3 ray=normalize(localPosition-localCamera);
  vec3 inv=1./ray;
  vec3 t0=(-.5-localCamera)*inv,t1=(.5-localCamera)*inv;
  vec3 mn=min(t0,t1),mx=max(t0,t1);
  float nearT=max(max(mn.x,mn.y),mn.z),farT=min(min(mx.x,mx.y),mx.z);
  if(nearT>farT)discard;
  float begin=max(nearT,0.);
  float dt=(farT-begin)/128.;
  vec4 color=vec4(0.);
  for(int i=0;i<128;i++){
    vec3 p=localCamera+ray*(begin+(float(i)+.5)*dt);
    if(cutaway && p.z>sliceY)continue;
    vec3 uv=vec3(p.x+.5,p.z+.5,p.y+.5);
    vec4 f=texture(field,uv);
    float temp=f.r, q=max(f.g,0.), soot=max(f.b,0.);
    float hot=clamp((temp-ambient)/1350.,0.,1.);
    vec3 rgb;float alpha;
    if(layer==0){
      float reaction=1.-exp(-q*.00006);
      float incandescent=clamp((temp-470.)/800.,0.,1.)*(1.-exp(-soot*22000.));
      float strength=max(reaction,incandescent);
      float base=clamp((temp-350.)/1000.,0.,1.);
      vec3 blue=vec3(.09,.27,1.3);
      vec3 orange=mix(vec3(1.65,.17,.012),vec3(2.8,1.25,.24),base);
      rgb=mix(blue,orange,clamp(soot*16000.+.15,0.,1.));
      float smoke=(1.-exp(-soot*1200.))*(1.-clamp((temp-300.)/700.,0.,1.));
      alpha=(strength*2.3+smoke*.5)*dt*opacityScale;
      rgb=mix(rgb,vec3(.13,.14,.15),smoke/(strength+smoke+.001));
    }else if(layer==1){
      rgb=heatmap(hot); alpha=clamp(hot*1.6,0.,1.)*dt*3.;
    }else if(layer==3){
      float oxygen=clamp(f.a/.23,0.,1.);
      rgb=mix(vec3(.97,.24,.08),vec3(.08,.65,.75),oxygen);
      alpha=dt*1.3;
    }else{
      rgb=mix(vec3(.12,.26,.34),vec3(.99,.53,.19),hot);alpha=hot*dt*.8;
    }
    alpha=1.-exp(-max(alpha,0.));
    color.rgb+=(1.-color.a)*rgb*alpha;
    color.a+=(1.-color.a)*alpha;
    if(color.a>.98)break;
  }
  if(color.a<.003)discard;
  gl_FragColor=vec4(color.rgb/max(color.a,.001),color.a);
}`;

export class FireScene {
  renderer:THREE.WebGLRenderer; scene=new THREE.Scene(); camera=new THREE.PerspectiveCamera(36,1,.01,80);
  controls:OrbitControls; composer:EffectComposer; bloom:UnrealBloomPass;
  apparatus=new THREE.Group(); volume:THREE.Mesh<THREE.BoxGeometry,THREE.ShaderMaterial>;
  light=new THREE.PointLight(0xffa552,0,9,2); texture:THREE.Data3DTexture;
  arrows=new THREE.Group(); probeMarker:THREE.Mesh; result?:Result; frame?:Float32Array;
  layer:Layer='fire'; scale=9.375; disposed=false; observer:ResizeObserver;
  onProbe?:(position:[number,number,number],values:number[],solid?:boolean)=>void;
  private probeIndices?:[number,number,number];
  private meshes:THREE.Object3D[]=[];
  constructor(public host:HTMLElement){
    this.renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,powerPreference:'high-performance'});
    this.renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));this.renderer.setClearColor(0x101210,0);
    this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.15;
    this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;
    host.append(this.renderer.domElement);
    this.camera.position.set(4.1,2.7,6.9);
    this.controls=new OrbitControls(this.camera,this.renderer.domElement);
    this.controls.target.set(0,1.2,0);this.controls.enableDamping=true;this.controls.minDistance=3;this.controls.maxDistance=14;
    this.controls.maxPolarAngle=Math.PI*.54;this.controls.update();
    this.scene.add(new THREE.HemisphereLight(0xdce6e1,0x282119,2.5));
    const key=new THREE.DirectionalLight(0xffe7c9,3);key.position.set(3,6,4);key.castShadow=true;
    key.shadow.normalBias=.015;key.shadow.bias=-.00015;
    key.shadow.mapSize.set(1024,1024);this.scene.add(key);
    const rim=new THREE.DirectionalLight(0x8cbbca,2.4);rim.position.set(-4,3,-3);this.scene.add(rim);
    const pedestal=new THREE.Mesh(new THREE.CylinderGeometry(1.36,1.43,.16,96),new THREE.MeshStandardMaterial({color:0x262b28,roughness:.38,metalness:.65}));
    pedestal.position.y=-.11;pedestal.receiveShadow=true;this.scene.add(pedestal);
    const ring=new THREE.Mesh(new THREE.TorusGeometry(1.365,.008,8,120),new THREE.MeshStandardMaterial({color:0xb48a58,metalness:.8,roughness:.4}));
    ring.rotation.x=Math.PI/2;ring.position.y=-.03;this.scene.add(ring);
    const bottom=new THREE.Mesh(new THREE.CylinderGeometry(1.25,1.30,.06,96),new THREE.MeshStandardMaterial({color:0x090b0a,metalness:.5,roughness:.3}));
    bottom.position.y=-.22;this.scene.add(bottom);
    const grid=new THREE.GridHelper(2.4,16,0x3e4740,0x303831);grid.position.y=-.024;
    (grid.material as THREE.Material).transparent=true;(grid.material as THREE.Material).opacity=.28;this.scene.add(grid);
    this.scene.add(this.apparatus);this.light.position.set(0,.9,0);this.scene.add(this.light);
    this.texture=this.makeTexture(new Float32Array(4),[1,1,1]);
    const material=new THREE.ShaderMaterial({vertexShader:vertex,fragmentShader:fragment,uniforms:{field:{value:this.texture},localCamera:{value:new THREE.Vector3()},layer:{value:0},cutaway:{value:false},sliceY:{value:0},opacityScale:{value:2.8},ambient:{value:20}},transparent:true,side:THREE.BackSide,depthWrite:false,depthTest:true});
    this.volume=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),material);this.volume.scale.set(1.5,3,1.5);this.volume.position.y=1.5;this.volume.renderOrder=2;this.scene.add(this.volume);
    this.scene.add(this.arrows);
    this.probeMarker=new THREE.Mesh(new THREE.SphereGeometry(.025,12,12),new THREE.MeshBasicMaterial({color:0xf0d8ac,depthTest:false}));
    this.probeMarker.visible=false;this.probeMarker.renderOrder=8;this.scene.add(this.probeMarker);
    this.composer=new EffectComposer(this.renderer);this.composer.addPass(new RenderPass(this.scene,this.camera));
    this.bloom=new UnrealBloomPass(new THREE.Vector2(800,600),.5,.45,.9);this.composer.addPass(this.bloom);this.composer.addPass(new OutputPass());
    this.observer=new ResizeObserver(()=>this.resize());this.observer.observe(host);this.resize();
    this.setApparatus('burner');
    let downX=0,downY=0;
    this.renderer.domElement.addEventListener('pointerdown',e=>{downX=e.clientX;downY=e.clientY});
    this.renderer.domElement.addEventListener('pointerup',e=>{if(Math.hypot(e.clientX-downX,e.clientY-downY)<4)this.pick(e)});
    this.renderer.setAnimationLoop(()=>{if(!this.disposed&&this.active&&!document.hidden){this.controls.update();this.volume.material.uniforms.localCamera.value.copy(this.volume.worldToLocal(this.camera.position.clone()));this.composer.render()}});
  }
  private active=true;
  setActive(value:boolean){this.active=value;this.controls.enabled=value;}
  makeTexture(data:Float32Array,dims:[number,number,number]){
    const tex=new THREE.Data3DTexture(data,...dims);tex.format=THREE.RGBAFormat;tex.type=THREE.FloatType;
    tex.minFilter=THREE.LinearFilter;tex.magFilter=THREE.LinearFilter;tex.unpackAlignment=1;tex.needsUpdate=true;return tex;
  }
  resize(){const w=this.host.clientWidth,h=this.host.clientHeight;if(w&&h){this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.renderer.setSize(w,h);this.composer.setSize(w,h)}}
  setResult(result:Result){
    this.result=result;this.frame=undefined;
    const c=result.coordinates;
    const span=(a:number[])=>a.length>1?a[a.length-1]-a[0]+(a[1]-a[0]):1;
    const size=[span(c.x),span(c.y),span(c.z)];this.scale=3/size[2];
    this.volume.scale.set(size[0]*this.scale,3,size[1]*this.scale);this.volume.position.set(0,1.5,0);
    this.volume.material.uniforms.ambient.value=result.config.ambient;
    this.setApparatus(result.config.scene);
    this.texture.dispose();this.texture=this.makeTexture(new Float32Array(result.dimensions.reduce((a,b)=>a*b,1)*4),result.dimensions);
    this.volume.material.uniforms.field.value=this.texture;this.probeMarker.visible=false;this.probeIndices=undefined;
  }
  setFrame(frame:Float32Array){
    if(!this.result)return;this.frame=frame;
    const target=this.texture.image.data as Float32Array;
    for(let i=0,j=0;i<frame.length;i+=7,j+=4){target[j]=frame[i];target[j+1]=frame[i+1];target[j+2]=frame[i+2];target[j+3]=frame[i+3]}
    this.texture.needsUpdate=true;
    let heat=0;for(let i=1;i<frame.length;i+=7)heat+=Math.max(frame[i],0);
    const c=this.result.coordinates;
    const cellVolume=(c.x[1]-c.x[0])*(c.y[1]-c.y[0])*(c.z[1]-c.z[0]);
    this.flameLight=Math.min(5,Math.sqrt(heat*cellVolume)*4);this.syncIgnition();
    this.updateArrows();
    this.emitProbe();
  }
  private ignited=true;
  private flameLight=0;
  setIgnited(value:boolean){this.ignited=value;this.syncIgnition()}
  private syncIgnition(){this.volume.visible=this.layer!=='fire'||this.ignited;this.light.intensity=this.layer==='fire'&&this.ignited?this.flameLight:0;this.host.dataset.flameVisible=String(this.layer==='fire'&&this.ignited&&this.flameLight>0)}
  setLayer(layer:Layer){this.layer=layer;this.volume.material.uniforms.layer.value={fire:0,temperature:1,flow:2,oxygen:3}[layer];this.bloom.strength=layer==='fire'?.55:.08;this.arrows.visible=layer==='flow';this.updateArrows();this.syncIgnition()}
  setCutaway(value:boolean){this.volume.material.uniforms.cutaway.value=value;this.updateArrows()}
  setSlice(value:number){this.volume.material.uniforms.sliceY.value=value;this.updateArrows()}
  setQuality(low:boolean){this.renderer.setPixelRatio(low?1:Math.min(devicePixelRatio,1.5));this.resize()}
  view(name:string){if(name==='side')this.camera.position.set(0,1.5,7.6);else if(name==='top')this.camera.position.set(.001,8,.001);else this.camera.position.set(4.1,2.7,6.9);this.controls.target.set(0,1.2,0);this.controls.update()}
  setApparatus(kind:SceneId){
    for(const obj of this.meshes)this.disposeObject(obj);this.meshes=[];this.apparatus.clear();
    const metal=new THREE.MeshStandardMaterial({color:0x9b8063,metalness:.85,roughness:.28});
    const black=new THREE.MeshStandardMaterial({color:0x282c29,metalness:.75,roughness:.32});
    const add=(geometry:THREE.BufferGeometry,material:THREE.Material,y:number)=>{const m=new THREE.Mesh(geometry,material);m.position.y=y;m.castShadow=true;m.receiveShadow=true;this.apparatus.add(m);this.meshes.push(m);return m};
    if(kind==='burner'){
      add(new THREE.CylinderGeometry(.23,.3,.055,64),black,.03);
      add(new THREE.CylinderGeometry(.083,.11,.27,48),metal,.19);
      add(new THREE.CylinderGeometry(.11,.09,.05,48),black,.35);
      add(new THREE.TorusGeometry(.083,.009,8,48),metal,.375).rotation.x=Math.PI/2;
      for(let i=0;i<8;i++){const slit=add(new THREE.BoxGeometry(.024,.045,.012),black,.24);slit.position.x=Math.cos(i*Math.PI/4)*.084;slit.position.z=Math.sin(i*Math.PI/4)*.084;slit.rotation.y=-i*Math.PI/4}
      const valve=add(new THREE.CylinderGeometry(.04,.04,.09,24),metal,.1);valve.rotation.z=Math.PI/2;valve.position.x=.14;
    }else if(kind==='candle'){
      const wax=new THREE.MeshStandardMaterial({color:0xe0d3b4,roughness:.68});
      add(new THREE.CylinderGeometry(.13,.16,.035,64),metal,.018);
      add(new THREE.CylinderGeometry(.078,.082,.31,64),wax,.19);
      add(new THREE.CylinderGeometry(.065,.078,.025,64),wax,.35);
      add(new THREE.CylinderGeometry(.006,.009,.035,12),black,.375);
    }else{
      const pixels=new Uint8Array(128*256*4);
      for(let y=0;y<256;y++)for(let x=0;x<128;x++){
        const wave=Math.sin(x*.53+Math.sin(y*.024)*2.8+Math.sin(y*.1)*.25);
        const noise=Math.sin(x*127.1+y*311.7)*43758.5453;
        const grain=.86+wave*.10+(noise-Math.floor(noise))*.10;
        const i=(y*128+x)*4;pixels[i]=141*grain;pixels[i+1]=99*grain;pixels[i+2]=64*grain;pixels[i+3]=255;
      }
      const map=new THREE.DataTexture(pixels,128,256,THREE.RGBAFormat);map.colorSpace=THREE.SRGBColorSpace;map.needsUpdate=true;
      const timber=new THREE.MeshStandardMaterial({map,roughness:.96});
      const height=(this.result?.solidBounds?.[0]?.[5]??.03)*this.scale;
      add(new THREE.BoxGeometry(.675,height,.675,5,2,5),timber,height/2);
      // Surface fissures are geometry, never invented ember combustion.
      const grain=new THREE.MeshStandardMaterial({color:0x2c221a,roughness:1});
      for(let i=0;i<9;i++){const g=add(new THREE.BoxGeometry(.001,.001,.58-(i%3)*.06),grain,height+.001);g.position.x=-.29+i*.071;g.position.z=(i%2)*.02;g.rotation.y=.03*Math.sin(i*2);g.castShadow=false}
    }
  }
  updateArrows(){
    while(this.arrows.children.length){const a=this.arrows.children[0];this.arrows.remove(a);this.disposeObject(a)}
    if(this.layer!=='flow'||!this.frame||!this.result)return;
    const {dimensions:d,coordinates:c}=this.result;
    const step=Math.max(3,Math.round(d[0]/7));
    for(let z=2;z<d[2]-1;z+=step)for(let y=2;y<d[1]-1;y+=step)for(let x=2;x<d[0]-1;x+=step){
      const i=((z*d[1]+y)*d[0]+x)*7;
      const dir=new THREE.Vector3(this.frame[i+4],this.frame[i+6],this.frame[i+5]);const speed=dir.length();if(speed<.035)continue;
      if(this.volume.material.uniforms.cutaway.value && (y/(d[1]-1)-.5)>this.volume.material.uniforms.sliceY.value)continue;
      const pos=new THREE.Vector3(c.x[x]*this.scale,c.z[z]*this.scale,c.y[y]*this.scale);
      const arrow=new THREE.ArrowHelper(dir.normalize(),pos,Math.min(.22,.04+speed*.12),new THREE.Color().setHSL(.55-Math.min(speed,2)*.22,.65,.62),.035,.02);
      this.arrows.add(arrow);
    }
  }
  pick(event:PointerEvent){
    if(!this.result||!this.frame)return;
    const rect=this.renderer.domElement.getBoundingClientRect();const mouse=new THREE.Vector2((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
    const ray=new THREE.Raycaster();ray.setFromCamera(mouse,this.camera);
    // Probe the displayed central cross-section, in physical FDS coordinates.
    const plane=new THREE.Plane(new THREE.Vector3(0,0,1),-this.volume.material.uniforms.sliceY.value*this.volume.scale.z);
    const p=new THREE.Vector3();if(!ray.ray.intersectPlane(plane,p))return;
    const physical:[number,number,number]=[p.x/this.scale,p.z/this.scale,p.y/this.scale];
    const c=this.result.coordinates,d=this.result.dimensions;
    const nearest=(a:number[],v:number)=>Math.round((v-a[0])/(a[1]-a[0]));
    const indices=[nearest(c.x,physical[0]),nearest(c.y,physical[1]),nearest(c.z,physical[2])];
    if(indices.some((n,i)=>n<0||n>=d[i]))return;
    this.probeIndices=indices as [number,number,number];
    this.emitProbe();
  }
  clearProbe(){this.probeIndices=undefined;this.probeMarker.visible=false}
  private emitProbe(){
    if(!this.result||!this.frame||!this.probeIndices)return;
    const c=this.result.coordinates,d=this.result.dimensions;
    const [x,y,z]=this.probeIndices;const i=((z*d[1]+y)*d[0]+x)*7;
    const snapped:[number,number,number]=[c.x[x],c.y[y],c.z[z]];
    this.probeMarker.position.set(snapped[0]*this.scale,snapped[2]*this.scale,snapped[1]*this.scale);this.probeMarker.visible=true;
    const solid=this.result.solidBounds?.some(b=>snapped[0]>=b[0]&&snapped[0]<=b[1]&&snapped[1]>=b[2]&&snapped[1]<=b[3]&&snapped[2]>=b[4]&&snapped[2]<=b[5]);
    this.onProbe?.(snapped,Array.from(this.frame.slice(i,i+7)),solid);
  }
  disposeObject(o:THREE.Object3D){o.traverse(child=>{const m=child as THREE.Mesh;if(m.geometry)m.geometry.dispose();if(m.material){for(const mat of Array.isArray(m.material)?m.material:[m.material]){const mapped=mat as THREE.MeshStandardMaterial;mapped.map?.dispose();mat.dispose()}}})}
  dispose(){
    this.disposed=true;this.renderer.setAnimationLoop(null);this.observer.disconnect();this.controls.dispose();
    this.texture.dispose();this.disposeObject(this.scene);
    this.scene.traverse(o=>{if(o instanceof THREE.DirectionalLight||o instanceof THREE.PointLight||o instanceof THREE.SpotLight)o.shadow.dispose()});
    for(const pass of this.composer.passes)pass.dispose();this.composer.dispose();this.renderer.dispose();this.renderer.domElement.remove();
  }
}
