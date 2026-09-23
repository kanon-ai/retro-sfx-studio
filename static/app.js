'use strict';
const $=id=>document.getElementById(id);
let patch,bank=[],info,context,source,gain,lastBuffer=null,lastKey='',revision=0,playing=false,requestSerial=0;
let timer,activePreset=0,knobs=[],history=[],future=[];
const clone=x=>JSON.parse(JSON.stringify(x));
const noteName=n=>['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'][((Math.round(n)%12)+12)%12]+(Math.floor(n/12)-1);
function status(message,error=false){$('status').textContent=message;document.body.classList.toggle('error',error);}
function remember(){history.push(clone(patch));if(history.length>80)history.shift();future=[];}
function store(){try{localStorage.setItem('retro-sfx-patch-v1',JSON.stringify(patch));}catch{} }
function changed(){requestSerial++;revision++;$('dirty').textContent='EDITED';lastKey='';drawGraphs();updateReadout();store();$('renderState').textContent='EDITED';$('scopeEmpty').textContent='EDITED · PRESS PLAY TO RENDER';$('scopeEmpty').hidden=false;}
function get(path){return path.split('.').reduce((obj,k)=>obj[k],patch);}
function set(path,value){const parts=path.split('.');const end=parts.pop();let obj=patch;for(const k of parts)obj=obj[k];obj[end]=value;changed();}
function makeKnob(parent,path,label,min,max,step,unit='',title=''){
 const wrap=document.createElement('div');wrap.className='knob-control';
 const lab=document.createElement('span');lab.className='knob-label';lab.textContent=label;wrap.append(lab);
 const dial=document.createElement('div');dial.className='knob-dial';dial.tabIndex=0;dial.role='slider';dial.setAttribute('aria-label',title||label);dial.setAttribute('aria-valuemin',min);dial.setAttribute('aria-valuemax',max);dial.title=title||label;
 const face=document.createElement('span');face.className='knob-face';dial.append(face);wrap.append(dial);
 const val=document.createElement('div');val.className='knob-value';const input=document.createElement('input');input.type='number';input.min=min;input.max=max;input.step=step;input.setAttribute('aria-label',(title||label)+' 数値');
 const units=document.createElement('span');units.textContent=unit;val.append(input,units);wrap.append(val);parent.append(wrap);
 const decimals=step<1?(String(step).split('.')[1]||'').length:0;
 const round=v=>+Math.max(min,Math.min(max,Math.round(v/step)*step)).toFixed(decimals);
 const refresh=(preserve=false)=>{const v=get(path);const fraction=(v-min)/(max-min);dial.style.setProperty('--angle',`${fraction*270}deg`);dial.style.setProperty('--rotation',`${-135+fraction*270}deg`);if(!preserve)input.value=Number(v).toFixed(decimals);dial.setAttribute('aria-valuenow',v);dial.setAttribute('aria-valuetext',v+' '+unit);};
 const apply=v=>{set(path,round(v));refresh();};
 input.addEventListener('focus',remember);
 input.addEventListener('input',()=>{if(input.validity.valid&&Number.isFinite(input.valueAsNumber)){set(path,round(input.valueAsNumber));refresh(true);}});
 input.addEventListener('change',()=>{if(Number.isFinite(input.valueAsNumber))apply(input.valueAsNumber);else refresh();});
 dial.addEventListener('pointerdown',e=>{if(e.button!==0||input.disabled)return;e.preventDefault();dial.focus();dial.setPointerCapture(e.pointerId);remember();const y=e.clientY,v=get(path);const move=ev=>apply(v+(y-ev.clientY)*(max-min)/(ev.shiftKey?1600:180));const up=()=>{dial.removeEventListener('pointermove',move);dial.removeEventListener('pointerup',up);dial.removeEventListener('pointercancel',up);};dial.addEventListener('pointermove',move);dial.addEventListener('pointerup',up);dial.addEventListener('pointercancel',up);});
 dial.addEventListener('keydown',e=>{if(input.disabled)return;if(['ArrowUp','ArrowRight','ArrowDown','ArrowLeft','Home','End'].includes(e.key)){e.preventDefault();remember();apply(e.key==='Home'?min:e.key==='End'?max:get(path)+(['ArrowUp','ArrowRight'].includes(e.key)?step:-step)*(e.shiftKey?10:1));}});
 knobs.push({refresh,input,dial,path});refresh();return wrap;
}
function renderControls(){
 knobs=[];
 const groups=[['pitchKnobs',[['note','NOTE',12,108,1,'','基準音 MIDI'],['sweep','SWEEP',-72,72,1,'st','ピッチスイープ 半音'],['curve','CURVE',.2,4,.1,'','スイープ曲線'],['duration','LENGTH',.06,5,.01,'s','発音時間']]],['ampKnobs',[['attack','ATTACK',0,2,.001,'s','アタック時間'],['decay','DECAY',0,2,.01,'s','ディケイ時間'],['sustain','SUSTAIN',0,1,.01,'','サステイン音量'],['release','RELEASE',0,2,.01,'s','リリース時間']]],['motionKnobs',[['vibrato','DEPTH',0,12,.1,'st','ビブラート深さ'],['speed','RATE',.1,30,.1,'Hz','ビブラート速度'],['level','LEVEL',0,1,.01,'','音量'],['tail','TAIL',.05,2,.05,'s','発音終了後の余白']]],['psgKnobs',[['noisePeriod','NOISE IN',1,31,1,'','ノイズ開始周期'],['noiseEnd','NOISE OUT',1,31,1,'','ノイズ終了周期']]]];
 for(const [id,defs]of groups){$(id).replaceChildren();for(const args of defs)makeKnob($(id),...args);}
 renderTimbre();renderSteps();refresh();
}
const routes=['1 → 2 → 3 → 4 → OUT','(1 + 2) → 3 → 4 → OUT','(1 + 2 → 3) → 4 → OUT','(1 → 2 + 3) → 4 → OUT','1 → 2 → OUT  /  3 → 4 → OUT','1 → (2 + 3 + 4) → OUT','1 → 2 → OUT  /  3 + 4 → OUT','1 + 2 + 3 + 4 → OUT'];
function ssg(){return patch.chip==='PSG'||(['OPN','OPNA'].includes(patch.chip)&&patch.mode==='SSG');}
function renderTimbre(){
 const isSSG=ssg(),opll=patch.chip==='OPLL';$('psgControls').hidden=!isSSG;$('operators').hidden=isSSG;$('fmSelects').hidden=isSSG;$('algorithmView').hidden=isSSG;$('algorithmLabel').hidden=opll;$('instrumentLabel').hidden=!opll;
 $('modeLabel').hidden=!['OPN','OPNA'].includes(patch.chip);$('pan').disabled=!(patch.chip==='OPM'||patch.chip==='OPNA'&&!isSSG);
 $('timbreTitle').textContent=isSSG?'矩形波 / ノイズ':opll?'2オペレーター / 内蔵音色':'4オペレーター FM';
 $('algorithmView').textContent=opll?'MODULATOR → CARRIER → OUT':routes[patch.algorithm];
 $('operators').className='operators'+(opll?' two-ops':'')+(opll&&patch.instrument!==0?' rom-mode':'');
 $('operators').replaceChildren();knobs=knobs.filter(k=>!k.path.startsWith('operators.'));
 if(!isSSG){for(let i=0;i<(opll?2:4);i++){
  const op=document.createElement('div');op.className='operator';const title=document.createElement('div');title.className='operator-title';title.textContent=opll?(i===0?'M · MODULATOR':'C · CARRIER'):`OPERATOR ${i+1}`;const subtitle=document.createElement('small');subtitle.textContent=opll&&patch.instrument!==0?'ROM VOICE / READ ONLY':'ENVELOPE + FREQUENCY';title.append(subtitle);op.append(title);
  const row=document.createElement('div');row.className='knob-grid';op.append(row);makeKnob(row,`operators.${i}.mul`,'MUL',0,15,1,'',`OP${i+1} 倍率 0は0.5倍`);
  if(!opll||i===0)makeKnob(row,`operators.${i}.tl`,'TL',0,opll?63:127,1,'',`OP${i+1} 減衰量`);
  makeKnob(row,`operators.${i}.`+(opll?'wave':'dt'),opll?'WAVE':'DT',0,opll?1:7,1,'',opll?'波形 0サイン 1半波':'デチューン 0～3正 4～7負');
  const rates=document.createElement('div');rates.className='operator-rates';for(const k of(opll?['ar','dr','sl','rr']:['ar','dr','sr','sl','rr'])){const lab=document.createElement('label');lab.textContent=k.toUpperCase();const input=document.createElement('input');input.type='number';input.min=0;input.max=['sl','rr'].includes(k)||opll?15:31;input.value=patch.operators[i][k];input.setAttribute('aria-label',`OP${i+1} ${k.toUpperCase()}`);input.disabled=opll&&patch.instrument!==0;input.addEventListener('input',()=>{if(input.validity.valid&&Number.isFinite(input.valueAsNumber)){remember();set(`operators.${i}.${k}`,input.valueAsNumber);}});input.addEventListener('change',()=>{remember();const v=Number.isFinite(input.valueAsNumber)?Math.round(input.valueAsNumber):0;set(`operators.${i}.${k}`,Math.max(0,Math.min(+input.max,v)));input.value=get(`operators.${i}.${k}`);});lab.append(input);rates.append(lab);}op.append(rates);$('operators').append(op);
 }}
 for(const k of knobs.filter(k=>k.path.startsWith('operators.'))){k.input.disabled=opll&&patch.instrument!==0;k.dial.tabIndex=k.input.disabled?-1:0;k.dial.setAttribute('aria-disabled',k.input.disabled);}
 $('feedback').disabled=opll&&patch.instrument!==0;
 $('chipHint').textContent=isSSG?'CH. A · TONE / NOISE · MONO':opll?'CH. 1 · USER VOICE + 15 ROM VOICES · MONO':patch.chip==='OPN'?'CH. 1 · 4 OPERATORS · MONO':'CH. 1 · 4 OPERATORS · STEREO';
}
function refresh(){
 for(const k of knobs)k.refresh();$('patchName').value=patch.name;$('lcdChip').textContent=patch.chip;
 $('mode').value=patch.mode;$('pan').value=patch.pan;$('algorithm').value=patch.algorithm;$('feedback').value=patch.feedback;$('opllInstrument').value=patch.instrument;
 for(const button of $('chips').children)button.classList.toggle('active',button.dataset.chip===patch.chip);
 for(const k of['tone','noise','sequenceOn'])$(k).setAttribute('aria-pressed',patch[k]);$('sequenceOn').textContent=patch.sequenceOn?'ON':'OFF';$('steps').classList.toggle('enabled',patch.sequenceOn);
 $('patchNumber').textContent=`P${String(activePreset+1).padStart(2,'0')}`;drawGraphs();updateReadout();
}
function renderSteps(){
 $('steps').replaceChildren();patch.sequence.forEach((v,i)=>{const cell=document.createElement('div');cell.className='step';const label=document.createElement('span');label.textContent=String(i+1).padStart(2,'0');const slider=document.createElement('input');slider.type='range';slider.min=-24;slider.max=24;slider.value=v;slider.setAttribute('aria-label',`ステップ${i+1} 半音差`);const n=document.createElement('input');n.type='number';n.min=-24;n.max=24;n.value=v;n.setAttribute('aria-label',`ステップ${i+1} 数値`);slider.addEventListener('pointerdown',remember);slider.addEventListener('input',()=>{n.value=slider.value;set(`sequence.${i}`,+slider.value);});n.addEventListener('input',()=>{if(n.validity.valid&&Number.isFinite(n.valueAsNumber)){remember();slider.value=n.value;set(`sequence.${i}`,n.valueAsNumber);}});n.addEventListener('change',()=>{remember();const value=Number.isFinite(n.valueAsNumber)?Math.max(-24,Math.min(24,Math.round(n.valueAsNumber))):0;n.value=slider.value=value;set(`sequence.${i}`,value);});cell.append(label,slider,n);$('steps').append(cell);});
}
function canvas(id){const c=$(id),r=c.getBoundingClientRect(),dpr=window.devicePixelRatio||1;c.width=Math.round(r.width*dpr);c.height=Math.round(r.height*dpr);const ctx=c.getContext('2d');ctx.scale(dpr,dpr);return [ctx,r.width,r.height];}
function grid(ctx,w,h,color){ctx.strokeStyle=color;ctx.lineWidth=.5;ctx.beginPath();for(let x=0;x<=w;x+=w/16){ctx.moveTo(x,0);ctx.lineTo(x,h);}for(let y=0;y<=h;y+=h/4){ctx.moveTo(0,y);ctx.lineTo(w,y);}ctx.stroke();}
function env(t){const d=patch.duration,r=Math.min(patch.release,d),gate=d-r,s=Math.min(1,gate/Math.max(patch.attack+patch.decay,1e-9)),a=patch.attack*s,dec=patch.decay*s;const held=x=>a>0&&x<a?x/a:dec>0&&x<a+dec?1-(1-patch.sustain)*(x-a)/dec:patch.sustain;if(t>=d)return 0;if(r&&t>=gate)return held(gate)*Math.max(0,(d-t)/r);return held(t);}
function drawGraphs(){if(!patch)return;for(const id of['pitchGraph','envelopeGraph']){const[ctx,w,h]=canvas(id);grid(ctx,w,h,'#3d4851');ctx.strokeStyle='#8bb8dd';ctx.lineWidth=1.4;ctx.beginPath();for(let i=0;i<=250;i++){const x=i/250,t=x*patch.duration;let y;if(id==='pitchGraph'){const semi=patch.sweep*x**patch.curve+patch.vibrato*Math.sin(t*patch.speed*Math.PI*2)+(patch.sequenceOn?patch.sequence[Math.min(7,Math.floor(x*8))]:0);y=h/2-semi/Math.max(24,Math.abs(patch.sweep)+24)*h*.42;}else y=h-5-env(t)*(h-12);if(i===0)ctx.moveTo(0,y);else ctx.lineTo(x*w,y);}ctx.stroke();ctx.fillStyle='#91a8bb';ctx.font='8px monospace';ctx.fillText(id==='pitchGraph'?'PITCH / TIME':'AMPLITUDE / TIME',6,10);}}
function drawScope(buffer){const[ctx,w,h]=canvas('scope');grid(ctx,w,h,'#1e364a35');ctx.strokeStyle='#1d3548';ctx.lineWidth=1;ctx.beginPath();if(buffer){const data=buffer.getChannelData(0);for(let x=0;x<w;x++){let lo=0,hi=0;const start=Math.floor(x*data.length/w),end=Math.floor((x+1)*data.length/w);for(let i=start;i<end;i++){lo=Math.min(lo,data[i]);hi=Math.max(hi,data[i]);}ctx.moveTo(x,h/2-lo*h*.46);ctx.lineTo(x,h/2-hi*h*.46);}}else{ctx.moveTo(0,h/2);ctx.lineTo(w,h/2);}ctx.stroke();}
function updateReadout(){$('readout').textContent=`${noteName(patch.note)} · ${(440*2**((patch.note-69)/12)).toFixed(1)} Hz`;$('durationReadout').textContent=(patch.duration+patch.tail).toFixed(3)+' s';$('noteName').textContent=noteName(patch.note);for(const k of $('keyboard').children)k.classList.toggle('selected',+k.dataset.note===patch.note);}
function stop(invalidate=true){if(invalidate)requestSerial++;if(source){source.onended=null;try{source.stop();}catch{}source=null;}playing=false;$('play').innerHTML='▶ <span>PLAY</span>';}
async function audio(){if(!context){context=new AudioContext();gain=context.createGain();gain.connect(context.destination);}await context.resume();gain.gain.value=+$('monitor').value/100;}
async function post(route,p=patch){const res=await fetch('/api/'+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});if(!res.ok){let msg='出力に失敗しました';try{msg=(await res.json()).error||msg;}catch{}throw Error(msg);}return res;}
async function play(){
 const serial=++requestSerial,current=clone(patch),key=JSON.stringify(current);stop(false);$('renderState').textContent='RENDER';status('音源レジスターから効果音を生成しています…');
 try{await audio();let buffer;if(lastBuffer&&key===lastKey)buffer=lastBuffer;else{const res=await post('render',current);buffer=await context.decodeAudioData(await res.arrayBuffer());}if(serial!==requestSerial)return;
  lastBuffer=buffer;lastKey=key;drawScope(buffer);$('scopeEmpty').hidden=true;let peak=0;for(let c=0;c<buffer.numberOfChannels;c++)for(const sample of buffer.getChannelData(c))peak=Math.max(peak,Math.abs(sample));$('peak').textContent=peak>=.999?'CLIP':peak===0?'SILENT':`${(20*Math.log10(peak)).toFixed(1)} dBFS`;
  source=context.createBufferSource();source.buffer=buffer;source.loop=$('loop').getAttribute('aria-pressed')==='true';source.connect(gain);source.onended=()=>{playing=false;source=null;$('play').innerHTML='▶ <span>PLAY</span>';$('renderState').textContent='READY';};source.start();playing=true;$('play').innerHTML='▶ <span>PLAYING</span>';$('renderState').textContent='PLAY';status(`${current.chip} · ${current.name} · ${buffer.duration.toFixed(3)}秒${peak>=.999?' · CLIP：LEVELを下げてください':''}`);
 }catch(e){if(serial===requestSerial){$('renderState').textContent='ERROR';status(e.message,true);}}
}
function saveBlob(blob,name){const a=document.createElement('a');const url=URL.createObjectURL(blob);a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function filename(){return (patch.name.replace(/[<>:"/\\|?*\x00-\x1f]/g,'_').replace(/[. ]+$/g,'')||'sound')+'-'+patch.chip;}
async function exportFile(route,ext){try{status(`${ext.toUpperCase()}を書き出しています…`);const name=filename(),res=await post(route);saveBlob(await res.blob(),name+'.'+ext);status(`${name}.${ext} を書き出しました。`);}catch(e){status(e.message,true);}}
function normalizeChip(){if(patch.chip==='OPLL'){for(const op of patch.operators){op.ar=Math.min(15,op.ar);op.dr=Math.min(15,op.dr);}patch.operators[0].tl=Math.min(63,patch.operators[0].tl);}}
function loadPreset(i){stop();remember();activePreset=(i+bank.length)%bank.length;patch=clone(bank[activePreset]);normalizeChip();$('preset').value=activePreset;renderControls();changed();$('dirty').textContent='PRESET';status(`${patch.name} を読み込みました。`);}
function setupKeyboard(){const white=[];for(let n=60;n<=84;n++){if(![1,3,6,8,10].includes(n%12))white.push(n);}for(const n of white){const button=document.createElement('button');button.className='key white-key';button.dataset.note=n;button.textContent=n%12===0?noteName(n):'';button.setAttribute('aria-label',noteName(n)+' を試聴');button.onclick=()=>{remember();patch.note=n;changed();for(const k of knobs)k.refresh();play();};$('keyboard').append(button);}for(let n=61;n<84;n++){if(![1,3,6,8,10].includes(n%12))continue;const before=white.filter(v=>v<n).length;const b=document.createElement('button');b.className='key black-key';b.dataset.note=n;b.style.left=`calc(${before/white.length*100}% - 2.2%)`;b.setAttribute('aria-label',noteName(n)+' を試聴');b.onclick=()=>{remember();patch.note=n;changed();for(const k of knobs)k.refresh();play();};$('keyboard').append(b);}}
async function init(){
 try{info=await(await fetch('/api/info')).json();bank=info.presets;patch=clone(info.default);try{const saved=localStorage.getItem('retro-sfx-patch-v1');if(saved){const res=await post('validate',JSON.parse(saved));patch=await res.json();}}catch{}
 for(const [name,data]of Object.entries(info.chips)){const b=document.createElement('button');b.className='chip-button';b.dataset.chip=name;b.append(document.createTextNode(name));const sub=document.createElement('small');sub.textContent={PSG:'MSX / YM2149',OPLL:'MSX / YM2413',OPN:'PC-98 / YM2203',OPNA:'PC-98 / YM2608',OPM:'X68000 / YM2151'}[name];b.append(sub);b.onclick=()=>{stop();remember();patch.chip=name;normalizeChip();renderControls();changed();};$('chips').append(b);}
 bank.forEach((p,i)=>{const o=new Option(`${String(i+1).padStart(2,'0')}  ${p.name}`,i);$('preset').append(o);});for(let i=0;i<8;i++)$('algorithm').append(new Option(String(i).padStart(2,'0'),i));['USER','Violin','Guitar','Piano','Flute','Clarinet','Oboe','Trumpet','Organ','Horn','Synthesizer','Harpsichord','Vibraphone','Synth bass','Acoustic bass','Electric guitar'].forEach((n,i)=>$('opllInstrument').append(new Option(`${i}: ${n}`,i)));
 setupKeyboard();normalizeChip();renderControls();drawScope(null);status('READY · プリセットを選ぶか、ノブを調整してPLAYで試聴できます。');
 $('preset').onchange=()=>loadPreset(+$('preset').value);$('previous').onclick=()=>loadPreset(activePreset-1);$('next').onclick=()=>loadPreset(activePreset+1);$('play').onclick=play;$('stop').onclick=()=>{stop();$('renderState').textContent='STOP';status('停止しました。');};$('loop').onclick=()=>{const on=$('loop').getAttribute('aria-pressed')!=='true';$('loop').setAttribute('aria-pressed',on);if(source)source.loop=on;};$('monitor').oninput=()=>{if(gain)gain.gain.value=+$('monitor').value/100;};
 $('patchName').onchange=()=>{remember();patch.name=$('patchName').value.trim()||'Untitled';$('patchName').value=patch.name;changed();};
 for(const id of['pan','mode','algorithm','feedback','opllInstrument'])$(id).onchange=()=>{remember();const field=id==='opllInstrument'?'instrument':id;let value=['algorithm','feedback','opllInstrument'].includes(id)?+$(id).value:$(id).value;if(id==='feedback')value=Math.max(0,Math.min(7,Math.round(Number.isFinite(value)?value:0)));patch[field]=value;renderTimbre();refresh();changed();};
 $('feedback').addEventListener('input',()=>{if($('feedback').validity.valid){remember();set('feedback',+$('feedback').value);}});
 for(const key of['tone','noise','sequenceOn'])$(key).onclick=()=>{remember();patch[key]=!patch[key];refresh();changed();};$('sequenceReset').onclick=()=>{remember();patch.sequence=Array(8).fill(0);renderSteps();refresh();changed();};
 $('random').onclick=()=>{remember();patch.sweep=Math.round(Math.random()*48-24);patch.feedback=Math.floor(Math.random()*8);patch.curve=+(Math.random()*2+.3).toFixed(1);patch.duration=+(Math.random()*.9+.15).toFixed(2);if(!ssg())for(const op of patch.operators){op.mul=1+Math.floor(Math.random()*7);}patch.name='Variation '+String(Math.floor(Math.random()*999)).padStart(3,'0');renderControls();changed();};
 $('savePatch').onclick=()=>{saveBlob(new Blob([JSON.stringify(patch,null,2)],{type:'application/json'}),filename()+'.patch.json');$('dirty').textContent='SAVED';status('編集可能なパッチJSONを書き出しました。');};$('loadPatch').onclick=()=>$('patchFile').click();$('patchFile').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>65536)throw Error('パッチファイルが大きすぎます。');const data=JSON.parse(await file.text());const validated=await(await post('validate',data)).json();remember();stop();patch=validated;normalizeChip();renderControls();changed();status(`${file.name} を読み込みました。`);}catch(err){status('読込エラー：'+err.message,true);}finally{e.target.value='';}};
 $('exportWav').onclick=()=>exportFile('render','wav');$('exportVgm').onclick=()=>exportFile('vgm','vgm');$('exportJson').onclick=()=>exportFile('registers','registers.json');$('exportC').onclick=()=>exportFile('header','h');
 $('exportAi').onclick=()=>exportFile('bundle','ai.zip');$('exportText').onclick=()=>exportFile('handoff','handoff.md');$('copyAi').onclick=async()=>{try{const text=await(await post('handoff')).text();await navigator.clipboard.writeText(text);status('AI引き渡しテキストをコピーしました。');}catch(e){status('コピーできませんでした。「説明.md」でファイルを保存できます。',true);}};
 $('help').onclick=()=>$('helpDialog').showModal();$('closeHelp').onclick=()=>$('helpDialog').close();
 document.addEventListener('keydown',e=>{const typing=['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName);if(e.code==='Space'&&!typing&&e.target.role!=='slider'&&!$('helpDialog').open){e.preventDefault();if(playing)stop();else play();}if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'&&!typing){e.preventDefault();const from=e.shiftKey?future:history,to=e.shiftKey?history:future;if(from.length){stop();to.push(clone(patch));patch=from.pop();renderControls();changed();}}});
 window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(()=>{drawGraphs();drawScope(lastBuffer);},80);});
 }catch(e){status('起動エラー：'+e.message,true);}
}
init();
