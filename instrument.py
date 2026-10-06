from pathlib import Path

def instrument(html):
    root=Path(__file__).parent
    code=(root/'performance-check.js').read_text(encoding='utf-8')
    html=html.replace('// ===== main.js =====',code+'\n// ===== main.js =====')
    html=html.replace('const device = await adapter.requestDevice();', "const device = await adapter.requestDevice({requiredFeatures:adapter.features.has('timestamp-query')?['timestamp-query']:[]});")
    html=html.replace('    this.shells = 40;', '''    this.shells = 40;
    if(device.features.has('timestamp-query'))this.gpuProbe={
      querySet:device.createQuerySet({type:'timestamp',count:2}),
      resolve:device.createBuffer({size:16,usage:GPUBufferUsage.QUERY_RESOLVE|GPUBufferUsage.COPY_SRC}),
      read:device.createBuffer({size:16,usage:GPUBufferUsage.COPY_DST|GPUBufferUsage.MAP_READ}),
      pending:false,frames:0,ms:null
    };''')
    html=html.replace('    const enc = d.createCommandEncoder();', '''    const enc = d.createCommandEncoder();
    const measureGPU=this.measureGPU&&this.gpuProbe&&!this.gpuProbe.pending&&++this.gpuProbe.frames%12===0;''',1)
    html=html.replace('colorAttachments: [], depthStencilAttachment: { view: this.shadowTex.createView()', "timestampWrites:measureGPU?{querySet:this.gpuProbe.querySet,beginningOfPassWriteIndex:0}:undefined,colorAttachments: [], depthStencilAttachment: { view: this.shadowTex.createView()",1)
    html=html.replace('colorAttachments: [{ view: out.createView()', "timestampWrites:measureGPU?{querySet:this.gpuProbe.querySet,endOfPassWriteIndex:1}:undefined,colorAttachments: [{ view: out.createView()",1)
    # The WebGPU property is endOfPassWriteIndex (not endingOfPassWriteIndex).
    html=html.replace('    d.queue.submit([enc.finish()]);', '''    if(measureGPU){const g=this.gpuProbe;enc.resolveQuerySet(g.querySet,0,2,g.resolve,0);enc.copyBufferToBuffer(g.resolve,0,g.read,0,16);g.pending=true;}
    d.queue.submit([enc.finish()]);
    if(measureGPU){const g=this.gpuProbe;g.read.mapAsync(GPUMapMode.READ).then(()=>{const t=new BigUint64Array(g.read.getMappedRange());g.ms=Number(t[1]-t[0])/1e6;g.read.unmap();}).catch(()=>{g.ms=null;}).finally(()=>{g.pending=false;});}''',1)
    css='''<style>
    .perf-check{border-top:1px solid var(--line);margin-top:8px;padding-top:8px;font-size:14px;}
    .perf-check[hidden]{display:none;}
    .perf-check summary{cursor:pointer;min-height:36px;display:flex;align-items:center;}
    .perf-live{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0 12px;}
    .perf-live dt{font-size:12px;color:var(--muted);}.perf-live dd{margin:3px 0 0;font:14px var(--mono);}
    .perf-note{font-size:12px;line-height:1.5;color:var(--muted);}.perf-result{font-size:14px;line-height:1.5;}
    #perfRun{width:100%;min-height:44px;}#perfTable{overflow-x:auto;}#perfTable table{font-size:12px;width:100%;border-collapse:collapse;}
    #perfTable th,#perfTable td{text-align:left;padding:7px 4px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums;}
    .perf-hud{position:absolute;bottom:12px;left:12px;right:12px;width:max-content;max-width:calc(100% - 24px);padding:8px 12px;background:rgba(226,223,218,.94);border:1px solid var(--line);font:12px/1.4 var(--mono);pointer-events:none;}
    .perf-hud[hidden]{display:none;}
    </style>'''
    html=html.replace('</head>',css+'</head>',1)
    marker='  // ── loop ──'
    hook='''  const checker = new OctopusPerformanceCheck({
    active(enabled) { renderer.measureGPU=enabled; if(!enabled&&renderer.gpuProbe)renderer.gpuProbe.ms=null; },
    save() { const saved = { paused:state.paused, slow:state.slow, showMesh:state.showMesh, lock:lockQ, shells:renderer.shells }; performanceCheckActive=true; lockQ=true; state.slow=false; state.showMesh=false; return saved; },
    apply(phase) { state.paused=phase.paused; renderer.shells=phase.layers; resetAll(); sim.reset(phase.paused?0:0.3); dirty=true; acc=0; },
    nudge() { sim.nudge(0.65); },
    restore(saved) { state.paused=saved.paused; state.slow=saved.slow; state.showMesh=saved.showMesh; lockQ=saved.lock; performanceCheckActive=false; resize(); renderer.shells=saved.shells; resetAll(); },
    info() { return { backend:renderer.backend, width:renderer.w, height:renderer.h, layers:renderer.shells, vertices:nV, triangles:renderMesh.body.count/3, nodes:sim.n, tets:sim.nT }; }
  });
'''
    html=html.replace(marker,hook+'\n'+marker)
    html=html.replace('    const dt = held ?', '    const cpuStart=performance.now();\n    let physicsEnd=cpuStart;\n    const frameInterval=now-last;\n    const dt = held ?')
    html=html.replace('    const moved = skin();', '    physicsEnd=performance.now();\n    const moved = skin();',1)
    html=html.replace('    followScene(dt);','    const furEnd=performance.now();\n    followScene(dt);',1)
    html=html.replace('    renderer.uploadGeometry(sim.x,', '    const submitStart=performance.now();\n    renderer.uploadGeometry(sim.x,',1)
    html=html.replace('    renderer.draw(state.showMesh);', '''    renderer.draw(state.showMesh);
    const cpuEnd=performance.now();
    if (!first && !held) checker.sample({now,interval:frameInterval,physics:physicsEnd-cpuStart,skin:furEnd-physicsEnd,submit:cpuEnd-submitStart,cpu:cpuEnd-cpuStart,gpu:renderer.gpuProbe?.ms??null});''',1)
    html=html.replace('if (!first && !held) adaptQuality(dt);', 'if (!first && !held && !checker.running) adaptQuality(dt);')
    return html
