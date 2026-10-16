import '@fontsource/dm-sans/400.css';
import '@fontsource/dm-sans/500.css';
import '@fontsource/dm-sans/600.css';
import '@fontsource/cormorant-garamond/400.css';
import '@fontsource/cormorant-garamond/500.css';
import './style.css';
import './fallback.css';
import './refinements.css';
import {FireScene} from './scene';
import {burningWindow,bounce} from './playback';
import {defaults,sceneCopy,sceneNames,type Config,type HistoryItem,type Job,type Layer,type Result,type SceneId} from './types';

const icon=(name:string)=>{
  const paths:Record<string,string>={flame:'M12 2c1 6-5 5-2 11 2-1 3-3 3-5 6 4 7 9 3 12-4 3-11 0-11-5 0-5 4-7 7-13Z',play:'m9 5 11 7-11 7Z',pause:'M8 5v14M16 5v14',reset:'M4 11a8 8 0 1 1 1 6M4 4v7h7',expand:'M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5',arrow:'M4 12h16m-6-6 6 6-6 6',info:'M12 11v6M12 7h.01M22 12A10 10 0 1 1 2 12a10 10 0 0 1 20 0Z',close:'m6 6 12 12M6 18 18 6',candle:'M8 12h8v9H8ZM12 12V9M12 2c-5 5 4 9 2 3Z',wood:'m4 17 14-7 3 5-14 7ZM3 9l14 7 3-5L6 4ZM3 9l3-5',gas:'M8 21h8M10 21V10h4v11M7 10h10M12 2c-5 5 4 7 2 3Z',chevron:'m8 4 8 8-8 8',check:'m5 12 4 4L19 6',layers:'m12 3 10 5-10 5L2 8ZM2 12l10 5 10-5M2 16l10 5 10-5',probe:'M12 2v5M12 17v5M2 12h5M17 12h5M17 12a5 5 0 1 1-10 0 5 5 0 0 1 10 0Z'};
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${(paths[name]??paths.info).split('|').map(d=>`<path d="${d}"/>`).join('')}</svg>`;
};
const $=<T extends HTMLElement=HTMLElement>(s:string)=>document.querySelector<T>(s)!;
const format=(n:number,d=1)=>n.toLocaleString('pl-PL',{minimumFractionDigits:d,maximumFractionDigits:d});
let config:Config={...defaults.burner},result:Result|undefined,history:HistoryItem[]=[],job:Job|undefined;
let layer:Layer='fire',playing=true,playTime=0,currentIndex=-1,loadingFrame=false,generation=0,speed=1,lastTick=performance.now(),pendingJobId:string|undefined;
let lastStatus='',pollHandle:number|undefined,frameAbort:AbortController|undefined;
const cache=new Map<number,Float32Array>();
let fire:FireScene|undefined;
let ignited=true,playbackMode:'continuous'|'physical'='continuous',direction=1;
let burnWindow:[number,number]|undefined,previewResult:Result|undefined,savedResult:{id:string;time:number}|undefined;

$('#app').innerHTML=`
<header class="header"><a class="brand" href="/" aria-label="IGNIS — strona główna"><span class="brand-icon">${icon('flame')}</span>IGNIS<span class="brand-separator"></span><span class="brand-caption">LABORATORIUM OGNIA</span></a><div class="header-right"><span class="live-dot"></span><span id="engine-label">Łączenie z laboratorium</span><button class="icon-button" id="about" aria-label="O modelu i źródłach">${icon('info')}</button></div></header>
<main>
  <section class="intro"><div><div class="eyebrow">ENERGIA, KTÓRĄ MOŻESZ ZOBACZYĆ</div><h1>Ogień. <em>Zrozum jego naturę.</em></h1></div><p>Trzy doświadczenia. Jedno fascynujące zjawisko.<br>Zmieniaj warunki. Odkrywaj procesy spalania.</p></section>
  <div class="workspace">
    <aside class="experiments"><div class="section-label">WYBIERZ DOŚWIADCZENIE</div>
      ${(['burner','candle','wood'] as SceneId[]).map((id,i)=>`<button class="experiment ${i===0?'active':''}" data-scene="${id}"><span class="experiment-number">0${i+1}</span><span class="experiment-icon">${icon(id==='burner'?'gas':id)}</span><strong>${sceneNames[id]}</strong><span class="experiment-desc">${['Mieszanie i reakcja','Dyfuzja i światło','Suszenie i piroliza'][i]}</span><span class="experiment-arrow">↗</span></button>`).join('')}
      <div class="experiment-note"><span class="tiny-flame">${icon('flame')}</span><p>Nie ma ognia bez spotkania<br>paliwa, tlenu i ciepła.</p><button class="text-button" id="explain">Poznaj to zjawisko <span>↗</span></button></div>
    </aside>
    <section class="stage" aria-label="Interaktywna scena 3D">
      <div class="stage-heading"><span id="scene-tag">01 / SPALANIE GAZU</span><span class="stage-live"><i></i><span id="result-label">PRZYGOTOWANIE SCENY</span></span></div>
      <div class="layer-tabs" role="tablist" aria-label="Warstwa wizualizacji">${[['fire','Płomień'],['temperature','Temperatura'],['flow','Przepływ'],['oxygen','Tlen']].map(([id,label],i)=>`<button role="tab" aria-selected="${i===0}" class="layer-tab ${i===0?'active':''}" data-layer="${id}">${label}</button>`).join('')}</div>
      <div id="viewport"></div>
      <div class="result-conditions" id="result-conditions"></div>
      <div class="ignition-controls"><button id="ignition" aria-pressed="true">${icon('flame')}<span>Zgaś</span></button><span id="fire-state" role="status">Pokaz płomienia · zapis CFD</span></div>
      <div class="empty-state" id="empty-state"><span class="loading-ring"></span><span id="empty-message">Wczytywanie obliczonego doświadczenia…</span></div>
      <div class="stage-caption"><span class="caption-line"></span><span id="stage-annotation">PALIWO + TLEN → ENERGIA</span></div>
      <div class="legend" id="legend" hidden><span id="legend-title">TEMPERATURA / °C</span><div class="legend-gradient"></div><div class="legend-values"><span id="legend-min">20</span><span id="legend-max">1600</span></div></div>
      <div class="probe" id="probe" hidden></div>
      <div class="stage-tools"><div class="camera-tools"><button class="active" data-view="3d">3D</button><button data-view="side">Bok</button><button data-view="top">Góra</button></div><button class="icon-button" id="presentation" aria-label="Tryb prezentacji">${icon('expand')}</button></div>
      <div class="stage-hint">Przeciągnij, aby obrócić <span>·</span> Kliknij, aby zmierzyć</div>
      <div class="stage-scale"><span></span><b id="scale-label">5 cm</b></div>
      <div class="metrics"><div><span>MAKS. TEMPERATURA GAZU</span><strong id="metric-temp">— <small>°C</small></strong></div><div><span>MOC SPALANIA</span><strong id="metric-hrr">— <small>W</small></strong></div><div><span>MAKS. PRĘDKOŚĆ GAZU</span><strong id="metric-speed">— <small>m/s</small></strong></div></div>
    </section>
    <aside class="parameters"><div class="parameters-heading"><span class="section-label">WARUNKI EKSPERYMENTU</span><button id="reset" class="icon-button" aria-label="Przywróć ustawienia">${icon('reset')}</button></div><div id="controls"></div>
      <div class="select-row"><label for="quality">Siatka obliczeń</label><select id="quality"><option value="preview">Podglądowa</option><option value="fine">Dokładniejsza · 3,4× komórek</option></select></div>
      <p class="model-caution" id="model-caution" hidden>Drewno: wynik jest silnie zależny od siatki. Model służy demonstracji procesów.</p>
      <div class="parameter-divider"></div>
      <label class="switch-row"><span>Przekrój płomienia</span><input type="checkbox" id="cutaway"><span class="switch"></span></label>
      <div id="slice-control" hidden><label class="slice-label" for="slice">Położenie przekroju</label><input type="range" id="slice" min="-0.45" max="0.45" step="0.025" value="0"></div>
      <label class="switch-row"><span>Oszczędne renderowanie</span><input type="checkbox" id="low-render"><span class="switch"></span></label>
      <button class="compute-button" id="compute">${icon('flame')}<span>Oblicz doświadczenie</span>${icon('arrow')}</button>
      <p class="compute-note" id="compute-note">Nowe warunki wymagają obliczeń CFD.<br>Odtwarzanie wyników działa płynnie.</p>
      <div id="job-status" hidden><div class="job-title"><span id="job-title">Obliczanie</span><button id="cancel">Anuluj</button></div><progress id="job-progress" max="1" value="0"></progress><p id="job-detail"></p></div>
      <button id="preview-toggle" class="preview-toggle" hidden disabled>Podgląd obliczeń</button><p id="preview-note" class="compute-note" hidden>Oczekiwanie na kompletne klatki CFD.</p>
      <div id="error-message" role="alert" hidden></div>
      <div class="history-select"><label for="history">Zapisane doświadczenia</label><select id="history"><option value="">Wybierz wynik…</option></select></div>
    </aside>
  </div>
  <section class="playback"><button class="play-button" id="play" aria-label="Wstrzymaj odtwarzanie">${icon('pause')}</button><button class="icon-button" id="rewind" aria-label="Odtwórz od początku">${icon('reset')}</button><div class="timeline"><div class="timeline-label"><span>CZAS ZAPISU CFD</span><strong><span id="current-time">0,00</span><small> / <span id="end-time">—</span> s</small></strong></div><input id="timeline" aria-label="Czas doświadczenia" type="range" min="0" max="6" step="0.01" value="0"></div><select id="playback-mode" aria-label="Tryb odtwarzania"><option value="continuous">Ciągły pokaz</option><option value="physical">Pełny przebieg</option></select><select id="speed" aria-label="Prędkość odtwarzania"><option value="0.25">0,25×</option><option value="0.5">0,5×</option><option value="1" selected>1×</option><option value="2">2×</option></select><div class="mini-chart"><div><span>MOC SPALANIA</span><small>W · czas fizyczny</small></div><canvas id="chart" width="560" height="100" aria-label="Wykres mocy spalania w czasie"></canvas></div></section>
  <section class="learning"><div class="learning-intro"><div class="eyebrow">CO WŁAŚCIWIE WIDZISZ?</div><h2 id="learning-title">Anatomia płomienia</h2><p id="learning-description"></p></div><div id="learning-cards"></div></section>
  <footer><span>IGNIS <span class="footer-dot">/</span> Fizyka, która rozświetla świat.</span><span>Wyniki CFD · Rekonstrukcja światła · <button id="sources">Model i źródła ↗</button></span></footer>
</main>
<dialog id="details"><button class="dialog-close icon-button" aria-label="Zamknij">${icon('close')}</button><div class="eyebrow">ZA ŚWIATŁEM KRYJE SIĘ FIZYKA</div><h2>Czym jest ogień?</h2><p>Ogień to zjawisko towarzyszące spalaniu: reakcjom chemicznym, które uwalniają energię. Płomień jest obszarem gorących, reagujących gazów. Zwykły płomień jest słabo zjonizowany i nie należy utożsamiać go z silnie zjonizowaną plazmą.</p><div class="equation" id="equation"></div><h3>Co jest obliczane?</h3><p>FDS rozwiązuje przestrzenny przepływ o małych prędkościach oraz transport ciepła i składników. Odczyty pochodzą z komórek siatki. Spalanie i promieniowanie korzystają z modeli przybliżonych. Sama obecność CFD nie gwarantuje dokładności pomiarowej.</p><p id="scene-limitations"></p><h3>Światło i kolor</h3><p>Wizualizacja objętościowa rekonstruuje światło z wydzielania ciepła, temperatury i sadzy. Niebieska barwa jest ilustracją emisji; szczegółowa chemiluminescencja nie jest obliczana. Kolor płomienia nie służy jako termometr.</p><h3>Dane i powtarzalność</h3><p id="result-details">Wybierz obliczony eksperyment.</p><div class="dialog-links"><a href="https://pages.nist.gov/fds/manuals.html" target="_blank" rel="noreferrer">Dokumentacja NIST FDS ↗</a><a href="https://github.com/firemodels/fds/blob/FDS-6.11.1/Verification/Pyrolysis/surf_mass_part_char_cart_fuel.fds" target="_blank" rel="noreferrer">Źródło modelu materiału ↗</a><a id="download-input" hidden>Pobierz wejście FDS ↓</a></div></dialog>
`;

const definitions:Record<string,{label:string;min:number;max:number;step:number;unit:string;digits?:number;help:string}>={
  fuel:{label:'Dopływ paliwa',min:0,max:30,step:.2,unit:'mg/s',help:'Zadany strumień masy paliwa na wylocie.'},
  oxygen:{label:'Tlen w otoczeniu',min:12,max:23,step:.1,unit:'% obj.',help:'Udział objętościowy O₂; resztę atmosfery zastępuje azot.'},
  wind:{label:'Boczny przepływ',min:0,max:.6,step:.01,unit:'m/s',digits:2,help:'Prędkość napływu w kierunku +X.'},
  primary_air:{label:'Powietrze pierwotne',min:0,max:1.2,step:.05,unit:'λ',digits:2,help:'Ułamek stechiometrycznej ilości powietrza domieszanego przed wylotem.'},
  ambient:{label:'Temperatura otoczenia',min:0,max:50,step:1,unit:'°C',digits:0,help:'Początkowa temperatura gazów i napływającego powietrza.'},
  moisture:{label:'Wilgotność drewna',min:0,max:30,step:1,unit:'% mas.',digits:0,help:'Udział wody w całkowitej mokrej masie próbki.'},
  ignition:{label:'Ogrzewanie zapłonowe',min:0,max:70,step:1,unit:'kW/m²',digits:0,help:'Zewnętrzny strumień ciepła na powierzchni próbki. Wyłącza się przed końcem doświadczenia.'},
  duration:{label:'Czas doświadczenia',min:1,max:30,step:1,unit:'s',digits:0,help:'Czas fizyczny, którego obliczenie może trwać wiele minut.'},
};

function renderControls(){
  const keys=config.scene==='wood'?['moisture','ignition','wind','oxygen','duration']:config.scene==='candle'?['fuel','oxygen','wind','duration']:['fuel','primary_air','ambient','oxygen','wind','duration'];
  $('#controls').innerHTML=keys.map(key=>{const d={...definitions[key]};if(key==='fuel'&&config.scene==='candle'){d.max=3;d.step=.1}const value=config[key as keyof Config] as number;return `<div class="control"><div class="control-label"><label for="param-${key}" title="${d.help}">${d.label}</label><div class="number-wrap"><input type="number" id="number-${key}" aria-label="${d.label} — wartość" min="${d.min}" max="${d.max}" step="${d.step}" value="${value}"><span>${d.unit}</span></div></div><input type="range" id="param-${key}" data-param="${key}" aria-label="${d.label}" min="${d.min}" max="${d.max}" step="${d.step}" value="${value}"><div class="range-extents"><span>${format(d.min,d.digits??1)}</span><span>${format(d.max,d.digits??1)} ${d.unit}</span></div></div>`}).join('');
  $('#controls').querySelectorAll<HTMLInputElement>('[data-param]').forEach(input=>{
    const key=input.dataset.param as keyof Config;const num=$<HTMLInputElement>(`#number-${key}`);
    const update=(source:HTMLInputElement)=>{
      const value=Number(source.value);if(!Number.isFinite(value)||value<Number(input.min)||value>Number(input.max)){source.setCustomValidity('Wartość poza zakresem');return}source.setCustomValidity('');
      (config as unknown as Record<string,unknown>)[key]=value;input.value=String(value);num.value=String(value);markDirty();
    };input.addEventListener('input',()=>update(input));num.addEventListener('change',()=>update(num));
  });
  $<HTMLSelectElement>('#quality').value=config.quality;
}
function markDirty(){const same=result&&JSON.stringify(normalize(config))===JSON.stringify(normalize(result.config));$('#compute-note').innerHTML=same?'Oglądasz wynik dla tych warunków.<br>Możesz zmienić parametry doświadczenia.':'Nowe warunki wymagają obliczeń CFD.<br>Oglądany wynik zachowuje swoje ustawienia.';$('#compute').classList.toggle('changed',!same)}
function normalize(c:Config){const x={...c};if(x.scene==='wood'){x.fuel=0;x.primary_air=0}else{x.moisture=0;x.ignition=0;if(x.scene==='candle')x.primary_air=0}return x}

function updateLearning(){const c=sceneCopy[config.scene];$('#scene-tag').textContent=c.tag;$('#learning-title').textContent=c.title;$('#learning-description').textContent=c.description;$('#equation').textContent=c.equation;$('#model-caution').hidden=config.scene!=='wood';
  $('#learning-cards').innerHTML=[0,1,2].map(i=>`<button class="learning-card" data-learn="${i}"><span class="learning-number">0${i+1}</span><h3>${c.notes[i*2]}</h3><p>${c.notes[i*2+1]}</p><span class="learn-arrow">↗</span></button>`).join('');
  $('#learning-cards').querySelectorAll('button').forEach(b=>b.addEventListener('click',openDetails));
  $('#scene-limitations').textContent=config.scene==='wood'?'Drewno: kinetyka i właściwości pochodzą z przypadku weryfikacyjnego FDS, nie z pomiaru konkretnego gatunku. Dodany model wilgoci jest założeniem demonstracyjnym. Pozostałość zwęglona jest obojętna; utlenianie żaru nie jest modelowane. W kontrolnym przebiegu z ogrzewaniem 35 kW/m² zagęszczenie siatki zmieniło średnią moc w oknie 1–2 s o ponad 100%. Wyniki nie są skalibrowaną prognozą rzeczywistego doświadczenia.':config.scene==='candle'?'Świeca: n-heptan zastępuje palne pary. Zadany jest dopływ paliwa; model nie oblicza topienia wosku ani transportu w knocie. Współczynniki emisji sadzy i CO są zadane.':'Palnik: metan z domieszką powietrza pierwotnego. Uproszczona chemia i zadane współczynniki sadzy/CO nie zastępują szczegółowego modelu kinetyki płomienia wstępnie zmieszanego.';
}
async function api<T>(path:string,options?:RequestInit):Promise<T>{const r=await fetch(`/api${path}`,options);if(!r.ok){let message=`Błąd ${r.status}`;try{const e=await r.json();message=typeof e.detail==='string'?e.detail:JSON.stringify(e.detail)}catch{}throw new Error(message)}return r.json()}
function showError(message:string){$('#error-message').textContent=message;$('#error-message').hidden=false}
async function refreshHistory(){
  history=await api<HistoryItem[]>('/experiments');
  $('#history').innerHTML='<option value="">Wybierz wynik…</option>'+history.map(h=>{
    const c=h.config;
    const conditions=c.scene==='wood'?`${format(c.moisture,0)}% wody · ${format(c.ignition,0)} kW/m²`:`${format(c.fuel,1)} mg/s · O₂ ${format(c.oxygen,1)}%${c.wind?` · ${format(c.wind,2)} m/s`:''}`;
    return `<option value="${h.id}">${h.featured?'★ ':''}${sceneNames[c.scene]} · ${c.duration}s · ${conditions} · ${c.quality==='fine'?'dokładniejsza':'podgląd'}</option>`;
  }).join('');
}
async function chooseScene(id:SceneId){
  config={...defaults[id]};renderControls();updateLearning();
  document.querySelectorAll<HTMLElement>('[data-scene]').forEach(b=>b.classList.toggle('active',b.dataset.scene===id));
  const candidates=history.filter(h=>h.config.scene===id);const sample=candidates.find(h=>h.featured)??candidates.find(h=>h.sample)??candidates.find(h=>h.config.duration>=defaults[id].duration)??candidates[0];
  if(sample)await loadResult(sample.id,false);
  else{generation++;frameAbort?.abort();cache.clear();result=undefined;currentIndex=-1;fire?.setApparatus(id);if(fire){fire.frame=undefined;fire.result=undefined;(fire.texture.image.data as Float32Array).fill(0);fire.texture.needsUpdate=true;fire.light.intensity=0}$('#empty-state').hidden=false;$('#empty-message').textContent='Gotowe do pierwszego doświadczenia. Wybierz „Oblicz”.';$('#result-label').textContent='BRAK OBLICZONEGO WYNIKU';updateMetrics();drawChart()}
  markDirty();
}
async function loadResult(id:string,adoptConfig=true,preferredTime?:number,partial?:Result){
  const token=++generation;frameAbort?.abort();cache.clear();loadingFrame=false;
  $('#empty-state').hidden=false;$('#empty-message').textContent='Wczytywanie pól przestrzennych…';
  try{const next=partial??await api<Result>(`/experiments/${id}/result`);if(token!==generation)return;result=next;
    if(adoptConfig){config={...next.config};renderControls();updateLearning();document.querySelectorAll<HTMLElement>('[data-scene]').forEach(b=>b.classList.toggle('active',b.dataset.scene===config.scene))}
    fire?.setResult(next);updateLayer();currentIndex=-1;
    playTime=Math.min(1.8,next.times[next.times.length-1]*.5);
    if(next.config.scene==='wood'){
      let peak=0;for(let i=1;i<next.extrema.length;i++)if(next.extrema[i].temperature>next.extrema[peak].temperature)peak=i;
      playTime=next.times[peak];
    }
    burnWindow=burningWindow(next);direction=1;
    if(preferredTime!==undefined)playTime=Math.min(preferredTime,next.times.at(-1)??0);
    else if(next.complete===false)playTime=next.times[0]??0;
    else if(playbackMode==='continuous'&&burnWindow)playTime=burnWindow[0];
    fire?.setIgnited(ignited);updateIgnition();
    lastTick=performance.now();
    $<HTMLInputElement>('#timeline').max=String(next.times[next.times.length-1]);$('#end-time').textContent=format(next.times[next.times.length-1],2);
    $('#result-label').textContent=`${next.complete===false?'WYNIK CZĘŚCIOWY · ':''}FDS · ${next.dimensions.map(String).join(' × ')}`;
    const rc=next.config;
    $('#result-conditions').textContent=rc.scene==='wood'?`WYNIK: wilgotność ${format(rc.moisture,0)}% · ogrzewanie ${format(rc.ignition,0)} kW/m² · napływ ${format(rc.wind,2)} m/s`:`WYNIK: paliwo ${format(rc.fuel,1)} mg/s · O₂ ${format(rc.oxygen,1)}% · napływ ${format(rc.wind,2)} m/s`;
    $('#scale-label').textContent=`Δx ${format((next.coordinates.x[1]-next.coordinates.x[0])*1000,2)} mm · komórka siatki`;
    $('.stage-scale').querySelector('span')!.style.display='none';
    $('#result-label').title=JSON.stringify(next.config,null,2);
    $('#probe').hidden=true;
    $('#result-details').textContent=`FDS 6.11.1 · ${next.model} · siatka ${next.dimensions.join(' × ')} · ${format(next.times[next.times.length-1],2)} s czasu fizycznego · obliczenia ${format(next.elapsed,1)} s. Identyfikator: ${next.id}. Wynik ma własny, zapisany zestaw parametrów.`;
    const download=$<HTMLAnchorElement>('#download-input');download.href=`/api/experiments/${id}/input`;download.hidden=false;
    $<HTMLSelectElement>('#history').value=id;markDirty();await showFrame(nearestTime(playTime));
  }catch(e){if(token===generation){showError((e as Error).message);$('#empty-message').textContent='Nie udało się wczytać wyniku.'}}
}
function nearestTime(t:number){if(!result)return 0;let best=0;for(let i=1;i<result.times.length;i++)if(Math.abs(result.times[i]-t)<Math.abs(result.times[best]-t))best=i;return best}
async function fetchFrame(index:number,signal?:AbortSignal){if(!result)throw new Error('Brak wyniku');const selected=result,token=generation;const cached=cache.get(index);if(cached)return cached;const suffix=selected.complete===false?`preview/frames/${index}?attempt=${selected.attempt}`:`frames/${index}`;const r=await fetch(`/api/experiments/${selected.id}/${suffix}`,{signal});if(!r.ok)throw new Error('Nie udało się pobrać klatki');const data=new Float32Array(await r.arrayBuffer());if(data.length!==selected.dimensions.reduce((a,b)=>a*b,1)*7)throw new Error('Nieprawidłowy rozmiar pola');if(token===generation){cache.set(index,data);while(cache.size>8)cache.delete(cache.keys().next().value!)}return data}
async function showFrame(index:number){
  if(!result||loadingFrame||index===currentIndex)return;
  loadingFrame=true;const token=generation;frameAbort=new AbortController();
  try{const data=await fetchFrame(index,frameAbort.signal);if(token!==generation)return;fire?.setFrame(data);currentIndex=index;$('#empty-state').hidden=true;updateMetrics();drawChart();updateIgnition()}
  catch(e){if(token===generation&&(e as Error).name!=='AbortError'){playing=false;updatePlayButton();showError((e as Error).message)}}
  finally{if(token===generation)loadingFrame=false}
}
function updateMetrics(){
  const ext=result?.extrema[currentIndex];$('#metric-temp').innerHTML=ext?`${format(ext.temperature,0)} <small>°C</small>`:'— <small>°C</small>';
  $('#metric-speed').innerHTML=ext?`${format(ext.velocity,2)} <small>m/s</small>`:'— <small>m/s</small>';
  const hrr=result?.series.HRR,ts=result?.series.Time;
  if(hrr?.length&&ts?.length){const t=result?.times[currentIndex]??0;let i=0;for(let j=1;j<ts.length;j++)if(Math.abs(ts[j]-t)<Math.abs(ts[i]-t))i=j;$('#metric-hrr').innerHTML=`${format(hrr[i]*1000,0)} <small>W</small>`}else $('#metric-hrr').innerHTML='— <small>W</small>';
}
function drawChart(){
  const canvas=$<HTMLCanvasElement>('#chart'),ctx=canvas.getContext('2d')!;const w=canvas.width,h=canvas.height;ctx.clearRect(0,0,w,h);
  ctx.strokeStyle='#303831';ctx.lineWidth=1;for(let y=20;y<h;y+=25){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}
  if(!result?.series.HRR?.length)return;
  const values=result.series.HRR,times=result.series.Time,max=Math.max(...values,.001),end=times[times.length-1];
  const gradient=ctx.createLinearGradient(0,0,0,h);gradient.addColorStop(0,'#c6996840');gradient.addColorStop(1,'#c6996800');
  ctx.beginPath();values.forEach((v,i)=>{const x=times[i]/end*w,y=h-8-v/max*(h-20);i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.strokeStyle='#cba475';ctx.lineWidth=2.2;ctx.stroke();ctx.lineTo(w,h);ctx.lineTo(0,h);ctx.closePath();ctx.fillStyle=gradient;ctx.fill();
  const displayTime=result.times[currentIndex]??0;ctx.beginPath();ctx.moveTo(displayTime/end*w,0);ctx.lineTo(displayTime/end*w,h);ctx.strokeStyle='#e6ddc38a';ctx.lineWidth=1;ctx.stroke();
}
function updateLayer(){
  fire?.setLayer(layer);document.querySelectorAll<HTMLElement>('[data-layer]').forEach(b=>{b.classList.toggle('active',b.dataset.layer===layer);b.setAttribute('aria-selected',String(b.dataset.layer===layer))});
  $('#legend').hidden=layer==='fire';$('#legend-title').textContent={fire:'',temperature:'TEMPERATURA / °C',flow:'PRĘDKOŚĆ / m/s',oxygen:'TLEN / % OBJ.'}[layer];
  $('#legend-min').textContent=layer==='temperature'?String(result?.config.ambient??20):'0';$('#legend-max').textContent=layer==='temperature'?`≥ ${(result?.config.ambient??20)+1350}`:layer==='oxygen'?'23':'≥ 2';$('#legend').dataset.layer=layer;
  $('#stage-annotation').textContent={fire:'PALIWO + TLEN → ENERGIA',temperature:'CIEPŁO W PRZESTRZENI',flow:'GORĄCE GAZY UNOSZĄ SIĘ',oxygen:'GDZIE DOCIERA TLEN?'}[layer];
}
async function compute(){
  $('#error-message').hidden=true;
  if([...$('#controls').querySelectorAll<HTMLInputElement>('input[type=number]')].some(x=>!x.reportValidity()))return;
  try{const next=await api<Job>('/experiments',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(config)});job=next;
    if(job.status==='completed'){await refreshHistory();await loadResult(job.id);return}
    pendingJobId=job.id;previewResult=undefined;savedResult=undefined;$('#preview-toggle').hidden=false;$<HTMLButtonElement>('#preview-toggle').disabled=true;$('#preview-note').hidden=false;renderJob();startPolling();
  }catch(e){showError((e as Error).message)}
}
function renderJob(){
  const active=job&&['running','converting','cancelling'].includes(job.status);$('#job-status').hidden=!active;$<HTMLButtonElement>('#compute').disabled=!!active;
  if(!job)return;$<HTMLProgressElement>('#job-progress').value=job.progress;
  $('#job-title').textContent=job.status==='converting'?'Przygotowanie wizualizacji':job.status==='cancelling'?'Zatrzymywanie…':`Obliczenia · ${Math.round(job.progress*100)}%`;
  $('#job-detail').textContent=`${format(job.physicalTime??0,2)} / ${job.config?.duration??config.duration} s czasu fizycznego · ${format(job.elapsed??0,0)} s pracy${job.profile?` · ${job.profile.mode.toUpperCase()} · ${job.profile.ranks>1?job.profile.ranks+' procesy':job.profile.threads+' wątki'}`:''}`;
}
function startPolling(){if(pollHandle)clearTimeout(pollHandle);pollHandle=window.setTimeout(poll,800)}
async function poll(){
  if(!pendingJobId)return;
  try{job=await api<Job>(`/experiments/${pendingJobId}`);renderJob();try{await refreshPreview(job)}catch(e){showError(`Podgląd niedostępny. ${(e as Error).message}`)}
    if(job.status==='completed'){const keep=result?.id===job.id&&result.complete===false;pendingJobId=undefined;await refreshHistory();await loadResult(job.id,true,keep?playTime:undefined);$('#preview-toggle').hidden=true;$('#preview-note').hidden=true;savedResult=undefined}
    else if(job.status==='failed'||job.status==='interrupted'){showError(job.error??'Obliczenia nie zakończyły się prawidłowo.');pendingJobId=undefined}
    else if(job.status==='cancelled'){pendingJobId=undefined;$('#compute-note').textContent='Obliczenia anulowane. Poprzedni wynik jest nadal dostępny.'}
    else startPolling();
  }catch(e){showError(`Brak połączenia z serwerem. ${(e as Error).message}`);startPolling()}
}
function updatePlayButton(){$('#play').innerHTML=icon(playing?'pause':'play');$('#play').setAttribute('aria-label',playing?'Wstrzymaj odtwarzanie':'Odtwórz wynik')}
function togglePlayback(){if(!playing&&playbackMode==='physical'&&result&&result.complete!==false&&playTime>=(result.times.at(-1)??0)){playTime=0;void showFrame(0)}playing=!playing;lastTick=performance.now();updatePlayButton()}
function updateIgnition(){
  $('#ignition').setAttribute('aria-pressed',String(ignited));$('#ignition span').textContent=ignited?'Zgaś':'Zapłon';
  $('#fire-state').textContent=!ignited?'Płomień zgaszony · odczyty: zapis CFD':(result?.extrema[currentIndex]?.hrr??0)>1e-6?'Płomień zapalony · zapis CFD':'Brak spalania w tej klatce · zapis CFD';
}
async function refreshPreview(current:Job){
  const response=await fetch(`/api/experiments/${current.id}/preview/manifest`,{cache:'no-store'});
  if(response.status===409||response.status===404)return;
  if(!response.ok)throw new Error('Nie udało się odczytać podglądu obliczeń.');
  const next:Result=await response.json();previewResult=next;
  $('#preview-toggle').hidden=false;$<HTMLButtonElement>('#preview-toggle').disabled=!next.times.length;
  $('#preview-note').hidden=false;$('#preview-note').textContent=`${current.status==='cancelled'?'Anulowany · ':current.status==='failed'?'Przerwany · ':''}Wynik częściowy · ${next.times.length} klatek · ${format(next.times.at(-1)??0,2)} s`;
  if(result?.complete===false&&result.id===next.id&&result.attempt===next.attempt){
    // Existing textures and cached frames stay valid; only the manifest grows.
    result={...next,complete:false};burnWindow=burningWindow(result);
    $<HTMLInputElement>('#timeline').max=String(next.times.at(-1)??0);$('#end-time').textContent=format(next.times.at(-1)??0,2);
  }
}
$('#preview-toggle').addEventListener('click',async()=>{
  try{
    if(result?.complete===false&&savedResult){const previous=savedResult;savedResult=undefined;await loadResult(previous.id,false,previous.time);$('#preview-toggle').textContent='Podgląd obliczeń'}
    else if(previewResult?.times.length){if(result&&result.complete!==false)savedResult={id:result.id,time:playTime};await loadResult(previewResult.id,false,undefined,{...previewResult,complete:false});$('#preview-toggle').textContent=savedResult?'Wróć do poprzedniego wyniku':'Podgląd obliczeń'}
  }catch(e){showError((e as Error).message)}
});
$('#ignition').addEventListener('click',()=>{ignited=!ignited;fire?.setIgnited(ignited);updateIgnition()});
$('#playback-mode').addEventListener('change',e=>{playbackMode=(e.target as HTMLSelectElement).value as typeof playbackMode;direction=1;if(playbackMode==='continuous'&&burnWindow){playTime=Math.max(burnWindow[0],Math.min(playTime,burnWindow[1]));void showFrame(nearestTime(playTime))}});
function openDetails(){($<HTMLDialogElement>('#details')).showModal()}

document.querySelectorAll<HTMLElement>('[data-scene]').forEach(b=>b.addEventListener('click',()=>void chooseScene(b.dataset.scene as SceneId)));
document.querySelectorAll<HTMLElement>('[data-layer]').forEach(b=>b.addEventListener('click',()=>{layer=b.dataset.layer as Layer;updateLayer()}));
document.querySelectorAll<HTMLElement>('[data-view]').forEach(b=>b.addEventListener('click',()=>{fire?.view(b.dataset.view!);document.querySelectorAll('[data-view]').forEach(x=>x.classList.toggle('active',x===b))}));
$('#reset').addEventListener('click',()=>{config={...defaults[config.scene]};renderControls();markDirty()});
$('#quality').addEventListener('change',e=>{config.quality=(e.target as HTMLSelectElement).value as Config['quality'];markDirty()});
$('#compute').addEventListener('click',()=>void compute());
$('#cancel').addEventListener('click',async()=>{if(pendingJobId)try{job=await api<Job>(`/experiments/${pendingJobId}/cancel`,{method:'POST'});renderJob()}catch(e){showError((e as Error).message)}});
$('#cutaway').addEventListener('change',e=>{const on=(e.target as HTMLInputElement).checked;fire?.setCutaway(on);$('#slice-control').hidden=!on});
$('#slice').addEventListener('input',e=>fire?.setSlice(Number((e.target as HTMLInputElement).value)));
$('#low-render').addEventListener('change',e=>fire?.setQuality((e.target as HTMLInputElement).checked));
$('#history').addEventListener('change',e=>{const id=(e.target as HTMLSelectElement).value;if(id)void loadResult(id)});
$('#play').addEventListener('click',togglePlayback);
$('#rewind').addEventListener('click',()=>{playbackMode='physical';$<HTMLSelectElement>('#playback-mode').value='physical';playTime=0;void showFrame(0)});
$('#speed').addEventListener('change',e=>{speed=Number((e.target as HTMLSelectElement).value)});
$('#timeline').addEventListener('input',e=>{playing=false;playbackMode='physical';$<HTMLSelectElement>('#playback-mode').value='physical';updatePlayButton();playTime=Number((e.target as HTMLInputElement).value);void showFrame(nearestTime(playTime))});
$('#presentation').addEventListener('click',()=>{document.body.classList.toggle('presenting');fire?.resize()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.body.classList.remove('presenting');if(e.code==='Space'&&!['INPUT','SELECT','BUTTON','TEXTAREA'].includes((e.target as HTMLElement).tagName)&&!$<HTMLDialogElement>('#details').open){e.preventDefault();togglePlayback()}});
for(const id of ['about','sources','explain'])$(`#${id}`).addEventListener('click',openDetails);
$('.dialog-close').addEventListener('click',()=>$<HTMLDialogElement>('#details').close());
$<HTMLDialogElement>('#details').addEventListener('click',e=>{if(e.target===$('#details'))$<HTMLDialogElement>('#details').close()});
document.addEventListener('visibilitychange',()=>{lastTick=performance.now()});
window.addEventListener('beforeunload',()=>fire?.dispose());

renderControls();updateLearning();
try{
  fire=new FireScene($('#viewport'));
  fire.onProbe=(position,values,solid)=>{
    $('#probe').hidden=false;
    $('#probe').innerHTML=`<div class="probe-title">${icon('probe')} SONDA · ŚRODEK KOMÓRKI<button id="close-probe" aria-label="Zamknij sondę">×</button></div><p>x ${format(position[0]*100,2)} · y ${format(position[1]*100,2)} · z ${format(position[2]*100,2)} cm</p>${solid?'<p>Komórka wewnątrz materiału.<br>Wybierz punkt w gazie, aby odczytać jego parametry.</p>':`<div><span>${format(values[0],0)} °C</span><span>O₂ ${format(values[3]*100,1)}%</span><span>${format(Math.hypot(...values.slice(4)),2)} m/s</span></div>`}`;
    $('#close-probe').addEventListener('click',()=>{$('#probe').hidden=true;fire?.clearProbe()});
  };
}catch(e){$('#viewport').classList.add('no-webgl');$('#viewport').innerHTML='<p class="graphics-error" role="status">Grafika 3D wymaga WebGL2.<br>Obliczenia, odczyty i wykresy pozostają dostępne.</p>';console.warn('Brak WebGL2:',e)}

async function init(){try{const health=await api<{solverAvailable:boolean;active:string|null}>('/health');$('#engine-label').textContent=health.solverAvailable?'FDS 6.11.1 · lokalnie':'FDS · wymaga przygotowania';if(!health.solverAvailable)showError('Brak lokalnego solvera. Uruchom scripts/setup.ps1.');await refreshHistory();await chooseScene('burner');if(health.active){pendingJobId=health.active;startPolling()}}catch(e){$('#engine-label').textContent='Serwer obliczeń jest wyłączony';$('#empty-message').textContent='Uruchom start.ps1, aby otworzyć laboratorium.';showError((e as Error).message)}}
void init();
function tick(now:number){const delta=Math.min((now-lastTick)/1000,.1);lastTick=now;if(result&&!document.hidden){if(playing&&currentIndex>=0){const end=result.times.at(-1)??0;if(result.complete===false){playTime=Math.min(end,playTime+delta*speed)}else if(playbackMode==='continuous'&&burnWindow){const next=bounce(playTime,delta*speed,direction,burnWindow);playTime=next.time;direction=next.direction}else{playTime=Math.min(end,playTime+delta*speed);if(playTime>=end){playing=false;updatePlayButton()}}}const i=nearestTime(playTime);if(i!==currentIndex)void showFrame(i);$('#current-time').textContent=format(result.times[currentIndex]??0,2);if(!loadingFrame)$<HTMLInputElement>('#timeline').value=String(result.times[currentIndex]??0)}requestAnimationFrame(tick)}
requestAnimationFrame(tick);
