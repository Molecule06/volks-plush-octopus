from pathlib import Path
root = Path(__file__).parent
original = (root/'reference/original.html').read_text(encoding='utf-8-sig')
html = original.replace('</style>', '</style></head><body>', 1)
fallback = (root/'webgl-fallback.js').read_text(encoding='utf-8')
html = html.replace('// ===== main.js =====', fallback+'\n\n// ===== main.js =====')
html = html.replace("const canvas = $('#gl');", "let canvas = $('#gl');")
start = html.index('  try {\n    if (!navigator.gpu)', html.index('async function main()'))
end = html.index('  let recoveries = 0;', start)
html = html[:start]+'''  try {
    if (new URLSearchParams(location.search).has('compat')) throw new Error('compatibility-mode');
    renderer = await Renderer.create(canvas, renderMesh, sim.edges, sim.n);
    renderer.backend = 'WEBGPU';
  } catch (err) {
    console.info('Using mobile compatibility renderer:', err.message);
    // A canvas cannot change context types once WebGPU has claimed it.
    const freshCanvas = canvas.cloneNode(false);
    canvas.replaceWith(freshCanvas); canvas = freshCanvas;
    try { renderer = new WebGLRenderer(canvas, renderMesh, sim.edges, sim.n); }
    catch (fallbackError) {
      showFallback('3D graphics could not start.', fallbackError.message);
      return;
    }
  }
  renderer.setFinger(fmesh);
'''+html[end:]
html = html.replace("if (info.reason === 'destroyed') return;", "if (info.reason === 'destroyed') return;\n      if (r.backend === 'WEBGL') { showFallback('Graphics were interrupted.', 'Reload the page to pick up the octopus again.'); return; }")
html = html.replace("renderer = fresh; dyn = fresh.dyn;", "fresh.backend = 'WEBGPU'; renderer = fresh; dyn = fresh.dyn;")
html = html.replace('let quality = 0;', "let quality = matchMedia('(pointer: coarse)').matches ? 2 : 0;")
html = html.replace("setStatus(state.paused ? 'WEBGPU · PAUSED' : 'WEBGPU · LIVE',", "setStatus(renderer.backend + (state.paused ? ' · PAUSED' : ' · LIVE'),")
html = html.replace("setStatus('WEBGPU · LIVE', 'live');", "setStatus(renderer.backend + ' · LIVE', 'live');")
html = html.replace('    if (held && pendingFrames <= 0)', '    if (document.hidden) { last = now; acc = 0; return; }\n    if (held && pendingFrames <= 0)')
html = html.replace("<title>Plush Octopus</title>", "<title>Plush Octopus · Opus material study</title>")
css = '''
/* Phone adaptations: preserve the original studio and type direction. */
body { min-height: 100dvh; }
.panel { max-height: calc(100dvh - 100px); overflow-y: auto; }
.tool, .btn, .swatch { touch-action: manipulation; }
@media (max-width: 860px), (max-height: 560px) and (max-width: 1000px) {
  body { grid-template-columns: minmax(0, 1fr); grid-template-areas: "head" "stage" "panel" "read" "notes"; padding-bottom: max(var(--gutter), env(safe-area-inset-bottom)); }
  .masthead { padding-top: max(var(--gutter), env(safe-area-inset-top)); padding-right: var(--gutter); }
  .masthead .kicker { font-size: 12px; letter-spacing: .12em; }
  .masthead h1 { font-size: clamp(48px, 13vw, 76px); }
  .caption { font-size: 16px; }
  .status { position: absolute; top: 0; right: 0; font-size: 12px; margin-top: max(var(--gutter), env(safe-area-inset-top)); }
  .stage { height: clamp(280px, 43svh, 520px); }
  .panel { max-height: none; overflow: visible; padding: 18px; }
  .label, .kicker { font-size: 12px; }
  .swname, .slider output, .check, .notes p { font-size: 14px; }
  input[type=range] { height: 40px; }
  input[type=range]::-webkit-slider-thumb { width: 22px; height: 22px; margin-top: -10px; }
  input[type=range]::-moz-range-thumb { width: 20px; height: 20px; }
  .slider .ends { font-size: 12px; }
  .check { min-height: 44px; }
  .check .box { width: 16px; height: 16px; }
  .hint { font-size: 16px; max-width: none; }
  .hint b { font-size: 12px; }
  .footnote { font-size: 12px; }
  .notes summary { min-height: 44px; }
}
@media (max-width: 440px) {
  .masthead { padding-top: calc(max(var(--gutter), env(safe-area-inset-top)) + 30px); }
  .status { left: var(--gutter); right: auto; padding: 5px 8px; }
  .masthead h1 { margin-top: 14px; }
  .stats > div { padding-right: 3px; }
  .stats > div + div { padding-left: 8px; }
  .stats dt { letter-spacing: .05em; font-size: 12px; }
  .stats dd { font-size: 17px; }
  .checks { gap: 10px; }
}
'''
html = html.replace('</head>', '<style>'+css+'</style></head>', 1)
webmcp = '''
  const context = document.modelContext;
  if (context?.registerTool) {
    const lifecycle = new AbortController();
    window.addEventListener('pagehide', () => lifecycle.abort(), { once: true });
    try {
      Promise.resolve(context.registerTool({
        name: 'set_octopus_material', title: 'Set octopus fur colour',
        description: 'Change the visible octopus fur to Coral, Lilac, or Lagoon.',
        inputSchema: { type: 'object', properties: { colour: { type: 'string', enum: ['coral', 'lilac', 'lagoon'] } }, required: ['colour'], additionalProperties: false },
        annotations: { readOnlyHint: false, untrustedContentHint: false },
        execute(input) {
          if (!input || !Object.hasOwn(PALETTES, input.colour) || Object.keys(input).length !== 1) throw new Error('Choose coral, lilac, or lagoon.');
          setPalette(input.colour); return { colour: input.colour };
        }
      }, { signal: lifecycle.signal })).catch(console.warn);
    } catch (error) { console.warn(error); }
  }
'''
html = html.replace('  // test mode: ?hold', webmcp+'\n  // test mode: ?hold')
(root/'dist/index.html').write_text(html, encoding='utf-8')
print(f'Adapted the original Opus artifact: {len(html):,} characters.')
