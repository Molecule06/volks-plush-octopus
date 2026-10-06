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
from optimize import optimize
html = optimize(html)
html = html.replace("setStatus(state.paused ? 'WEBGPU · PAUSED' : 'WEBGPU · LIVE',", "setStatus(renderer.backend + (state.paused ? ' · PAUSED' : ' · LIVE'),")
html = html.replace("setStatus('WEBGPU · LIVE', 'live');", "setStatus(renderer.backend + ' · LIVE', 'live');")
html = html.replace('    if (held && pendingFrames <= 0)', '    if (document.hidden) { last = now; acc = 0; return; }\n    if (held && pendingFrames <= 0)')
html = html.replace("<title>Plush Octopus</title>", "<title>Plush Octopus · Opus material study</title>")
html = html.replace('<div class="kicker">Material Studies / No. 012</div>', '<button class="kicker dev-trigger" id="devTrigger" type="button" aria-keyshortcuts="Shift+P">Volks Games</button>')
palette_start = html.index('const PALETTES = {')
palette_end = html.index('\n};', palette_start) + 3
html = html[:palette_start] + '''const PALETTES = {
  blue: {
    name: 'Blue',
    furRoot: lin('#285bc5'), furTip: lin('#97c7ff'), under: lin('#e4efff'), sucker: lin('#a4c7ff'), cheek: lin('#e6a1ce'),
    iris: lin('#253d62'), shadowTint: [0.48, 0.52, 0.62],
  },
  lagoon: {
    name: 'Lagoon',
    furRoot: lin('#1f7f86'), furTip: lin('#8fdfd6'), under: lin('#e3f6f1'), sucker: lin('#97ddd3'), cheek: lin('#f5878f'),
    iris: lin('#6a3a12'), shadowTint: [0.5, 0.56, 0.56],
  },
  orchid: {
    name: 'Orchid',
    furRoot: lin('#a756a0'), furTip: lin('#edb2e2'), under: lin('#fae5f3'), sucker: lin('#df9ed2'), cheek: lin('#ff9fc4'),
    iris: lin('#523454'), shadowTint: [0.60, 0.50, 0.59],
  },
};''' + html[palette_end:]
html = html.replace("let currentPalette = 'coral';", "let currentPalette = 'blue';")
html = html.replace("setPalette('coral');", "setPalette('blue');")
css = '''
/* Phone adaptations: preserve the original studio and type direction. */
body { min-height: 100dvh; }
.dev-trigger { display: block; pointer-events: auto; border: 0; padding: 16px 0; margin: -16px 0; background: transparent; text-align: left; text-transform: none; touch-action: manipulation; }
.dev-trigger:focus-visible { outline: 1px solid var(--ink); outline-offset: 4px; }
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
.swname, .check, .notes p { font-size: 14px; }
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
        description: 'Change the visible octopus fur to Blue, Lagoon, or Orchid (purple-pink).',
        inputSchema: { type: 'object', properties: { colour: { type: 'string', enum: ['blue', 'lagoon', 'orchid'] } }, required: ['colour'], additionalProperties: false },
        annotations: { readOnlyHint: false, untrustedContentHint: false },
        execute(input) {
          if (!input || !Object.hasOwn(PALETTES, input.colour) || Object.keys(input).length !== 1) throw new Error('Choose blue, lagoon, or orchid.');
          setPalette(input.colour); return { colour: input.colour };
        }
      }, { signal: lifecycle.signal })).catch(console.warn);
    } catch (error) { console.warn(error); }
  }
'''
html = html.replace('  // test mode: ?hold', webmcp+'\n  // test mode: ?hold')
from instrument import instrument
html = instrument(html)
import re
html = re.sub(r'\s*<p class="caption">[\s\S]*?</p>', '', html)
html = re.sub(r'^\s*\.caption[^\n]*\n', '', html, flags=re.MULTILINE)
html = html.replace('    <header><span class="label">The Specimen</span><span>fig. 12</span></header>\n', '')
html = html.replace('aria-label="Specimen controls"', 'aria-label="Octopus controls"')
slider_start = html.index('    <div class="group">\n      <div class="slider">')
slider_end = html.index('    <div class="group">\n      <div class="buttons">', slider_start)
html = html[:slider_start] + html[slider_end:]
sync_start = html.index("  const firm = $('#firmness')")
sync_end = html.index("  $('#shake').addEventListener", sync_start)
html = html[:sync_start] + html[sync_end:]
html = re.sub(r'^\s*(?:\.panel header|\.slider|input\[type=range\])[^\n]*\n', '', html, flags=re.MULTILINE)
html = html.replace(', input[type=range]:focus-visible', '')
html = re.sub(r'^const SCALE_CM = [^\n]*\n', '', html, flags=re.MULTILINE)
html = re.sub(r'\s*<details class="notes">[\s\S]*?</details>', '', html)
html = re.sub(r"\$\('#n(?:Particles|Tets|Shells)'\)\.textContent = [^;]+;", '', html)
html = re.sub(r'^\s*\.notes[^\n]*\n', '', html, flags=re.MULTILINE)
html = html.replace(', .notes,', ',').replace(' "notes notes"', '').replace(' "notes"', '')
html = html.replace('.check, .notes p', '.check')
html = re.sub(r'\s*<dl class="stats">[\s\S]*?</dl>', '', html)
html = re.sub(r'\s*<p class="footnote">[\s\S]*?</p>', '', html)
html = html.replace('aria-label="Live readouts"', 'aria-label="Tool instructions"')
html = re.sub(r'  const massOut = [\s\S]*?\n  }\n(?=\n  // expose)', '', html)
html = html.replace('updateReadouts();', '')
html = html.replace('readoutT = 0, ', '').replace('readoutT += dt; ', '')
html = re.sub(r'    if \(readoutT > 0\.15\) [^\n]*\n', '', html)
html = re.sub(r'  volumeRatio\(\) [^\n]*\n', '', html)
html = re.sub(r'^const DENSITY = [^\n]*\n', '', html, flags=re.MULTILINE)
html = re.sub(r'  let vol = 0, area = 0;[\s\S]*?(?=  const rest = new Float32Array\(pos\);)', '', html)
html = html.replace(', skinVol: vol, area', '')
html = re.sub(r'^\s*\.(?:stats|footnote)[^\n]*\n', '', html, flags=re.MULTILINE)
html = re.sub(r'(<section class="readouts"[\s\S]*?)(\s*</section>)', r'\1<p class="scale-note">Illustrative scale: 1 sim unit ≈ 10 cm (an octopus 38 cm from tip to tip).</p>\2', html, count=1)
html = html.replace('</head>', '<style>.scale-note{font-size:12px;line-height:1.5;color:var(--muted);max-width:400px;margin:9px 0 0}</style></head>', 1)
(root/'dist/index.html').write_text(html, encoding='utf-8')
print(f'Adapted the original Opus artifact: {len(html):,} characters.')
