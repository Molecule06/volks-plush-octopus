// Small, local-only diagnostic. CPU timings and optional GPU timestamps are separate.
// A fixed-resolution A/B test isolates fur rendering from the soft-body workload.
class OctopusPerformanceCheck {
  constructor(hooks) {
    this.hooks=hooks;this.samples=[];this.phaseSamples=[];this.running=false;this.lastPublish=0;
    const panel=document.createElement('details');panel.className='perf-check';panel.id='performance';
    panel.innerHTML=`<summary>Performance checker</summary>
      <dl class="perf-live"><div><dt>FPS</dt><dd id="perfFPS">—</dd></div><div><dt>Frame</dt><dd id="perfFrame">—</dd></div><div><dt>Physics CPU</dt><dd id="perfPhysics">—</dd></div><div><dt>Skin + fur CPU</dt><dd id="perfSkin">—</dd></div><div><dt>Draw submit CPU</dt><dd id="perfSubmit">—</dd></div><div><dt>GPU execution</dt><dd id="perfGPU">—</dd></div><div><dt>Fur layers</dt><dd id="perfLayers">—</dd></div></dl>
      <p class="perf-note" id="perfGeometry"></p><button type="button" class="btn" id="perfRun">Check bottleneck · 16s</button>
      <p class="perf-note">Compares full fur with fur drawing off, first still, then moving. CPU timings exclude GPU execution. GPU timing is shown when supported. Resets the toy and restores your controls.</p>
      <p id="perfResult" class="perf-result" role="status">Ready to check.</p><div id="perfTable"></div>`;
    document.querySelector('.panel').appendChild(panel);this.panel=panel;
    this.button=panel.querySelector('#perfRun');this.result=panel.querySelector('#perfResult');
    const hud=document.createElement('div');hud.className='perf-hud';hud.hidden=true;hud.setAttribute('role','status');document.querySelector('#stage').appendChild(hud);this.hud=hud;
    this.button.addEventListener('click',()=>this.running?this.finish(true):this.start());
    panel.addEventListener('toggle',()=>{this.samples=[];this.hooks.active(panel.open||this.running);});
    document.addEventListener('visibilitychange',()=>{if(document.hidden){this.samples=[];if(this.running)this.finish(true);}});
    // Safari's toolbar changes height while scrolling. Only a width/orientation
    // change invalidates the comparison; the renderer freezes its buffer during it.
    window.addEventListener('resize',()=>{if(this.running){if(window.innerWidth!==this.viewportWidth)this.finish(true);}else this.samples=[];});
  }
  average(samples,key){return samples.reduce((s,v)=>s+v[key],0)/Math.max(1,samples.length);}
  stats(samples){const intervals=samples.map(s=>s.interval).sort((a,b)=>a-b);return {
    frames:samples.length,fps:1000/this.average(samples,'interval'),frameMs:this.average(samples,'interval'),p95Ms:intervals[Math.min(intervals.length-1,Math.floor(intervals.length*.95))]||0,
    physicsMs:this.average(samples,'physics'),skinFurMs:this.average(samples,'skin'),submitMs:this.average(samples,'submit'),cpuMs:this.average(samples,'cpu'),gpuMs:samples.some(s=>Number.isFinite(s.gpu))?this.average(samples.filter(s=>Number.isFinite(s.gpu)),'gpu'):null};}
  start(){
    if(!document.body.classList.contains('ready'))return;
    this.saved=this.hooks.save();this.full=this.saved.shells;this.rows=[];this.running=true;this.phase=-1;this.hooks.active(true);
    this.disabledControls=[...document.querySelectorAll('.panel button,.panel input')].filter(el=>el!==this.button).map(el=>[el,el.disabled]);
    for(const [el] of this.disabledControls)el.disabled=true;
    this.canvas=document.querySelector('#gl');this.pointerStyle=this.canvas.style.pointerEvents;this.canvas.style.pointerEvents='none';
    this.phases=[{name:'Still · full fur',paused:true,layers:this.full},{name:'Still · no fur drawing',paused:true,layers:0},{name:'Moving · full fur',paused:false,layers:this.full},{name:'Moving · no fur drawing',paused:false,layers:0}];
    this.width=this.hooks.info().width;this.height=this.hooks.info().height;this.viewportWidth=window.innerWidth;
    this.button.textContent='Cancel check';this.hud.hidden=false;this.result.textContent='Checking on this device…';this.panel.querySelector('#perfTable').replaceChildren();
    document.querySelector('#stage').scrollIntoView({block:'center',behavior:'instant'});this.next(performance.now());
  }
  next(now){this.phase++;if(this.phase===this.phases.length){this.finish(false);return;}
    this.phaseSamples=[];this.phaseStart=now;this.nextNudge=now+1000;this.hooks.apply(this.phases[this.phase]);}
  sample(v){
    if(!this.running&&!this.panel.open)return;
    if(!Number.isFinite(v.interval)||v.interval<=0)return;
    this.samples.push(v);if(this.samples.length>120)this.samples.shift();
    if(this.running){const elapsed=v.now-this.phaseStart,p=this.phases[this.phase];
      if(elapsed>=800)this.phaseSamples.push(v);
      if(!p.paused&&v.now>=this.nextNudge){this.hooks.nudge();this.nextNudge=v.now+1000;}
      if(elapsed>=4000){this.rows.push({name:p.name,layers:p.layers,...this.stats(this.phaseSamples)});this.next(v.now);}
    }
    if(v.now-this.lastPublish<500)return;this.lastPublish=v.now;
    const s=this.stats(this.samples),i=this.hooks.info();
    const put=(id,value)=>this.panel.querySelector('#'+id).textContent=value;
    put('perfFPS',s.fps.toFixed(1));put('perfFrame',s.frameMs.toFixed(1)+' ms');put('perfPhysics',s.physicsMs.toFixed(2)+' ms');put('perfSkin',s.skinFurMs.toFixed(2)+' ms');put('perfSubmit',s.submitMs.toFixed(2)+' ms');put('perfGPU',s.gpuMs===null?'Unavailable':s.gpuMs.toFixed(2)+' ms');put('perfLayers',String(i.layers));
    this.panel.querySelector('#perfGeometry').textContent=`${i.backend} · ${i.width} × ${i.height} pixels · ${i.vertices.toLocaleString()} vertices · ${i.triangles.toLocaleString()} body triangles · ${i.nodes.toLocaleString()} physics nodes · ${i.tets.toLocaleString()} tetrahedra`;
    if(this.running)this.hud.textContent=`${this.phases[this.phase].name} · ${s.fps.toFixed(0)} FPS · ${Math.min(16,Math.floor(this.phase*4+(v.now-this.phaseStart)/1000))}/16s`;
  }
  finish(cancelled){if(!this.running)return;this.running=false;this.hooks.restore(this.saved);this.hooks.active(this.panel.open);for(const [el,disabled]of this.disabledControls)el.disabled=disabled;this.canvas.style.pointerEvents=this.pointerStyle;this.button.textContent='Check bottleneck · 16s';this.hud.hidden=true;this.samples=[];
    if(cancelled){this.result.textContent='Check cancelled. Keep the tab visible and avoid rotating the phone or changing screen width while testing.';return;}
    const [stillFull,stillOff,movingFull,movingOff]=this.rows;
    const gain=(a,b)=>{const value=(b.fps/a.fps-1)*100;return Math.abs(value)<.05?0:value;};
    const renderGain=gain(stillFull,stillOff),movingGain=gain(movingFull,movingOff);
    const cpuShare=movingFull.cpuMs/movingFull.frameMs;
    let finding=renderGain>20?'Fur drawing is a major bottleneck on this device.':cpuShare>.6?'JavaScript simulation and deformation use most of the frame budget.': 'Fur drawing did not dominate this check. Shadows, GPU limits, or the browser may contribute.';
    if(stillFull.fps>55&&stillOff.fps>55)finding='Both still tests ran smoothly; the frame-rate cap may hide spare GPU capacity.';
    if(stillFull.gpuMs!==null&&stillOff.gpuMs!==null&&stillFull.gpuMs>0){const furShare=Math.max(0,1-stillOff.gpuMs/stillFull.gpuMs);finding=`Fur drawing accounted for about ${(furShare*100).toFixed(0)}% of GPU execution in the still-toy comparison.`;}
    this.result.textContent=`${finding} Turning off fur drawing changed still FPS by ${renderGain.toFixed(0)}% and moving FPS by ${movingGain.toFixed(0)}%.`;
    const table=document.createElement('table');table.innerHTML='<thead><tr><th>Test</th><th>FPS</th><th>CPU</th><th>GPU</th></tr></thead><tbody>'+this.rows.map(r=>`<tr><td>${r.name}</td><td>${r.fps.toFixed(1)}</td><td>${r.cpuMs.toFixed(1)} ms</td><td>${r.gpuMs===null?'—':r.gpuMs.toFixed(1)+' ms'}</td></tr>`).join('')+'</tbody>';
    this.panel.querySelector('#perfTable').appendChild(table);
    this.panel.dataset.report=JSON.stringify({width:this.width,height:this.height,renderer:this.hooks.info().backend,rows:this.rows,renderGain,movingGain});
    this.panel.open=true;
  }
}
