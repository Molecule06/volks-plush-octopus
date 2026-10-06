"""Mobile rendering changes, kept separate from the preserved reference source."""

def optimize(html):
    def replace_once(before, after):
        nonlocal html
        if html.count(before) != 1:
            raise ValueError('Mobile adapter anchor changed: '+before[:80])
        html=html.replace(before, after, 1)

    replace_once('const NET_STEP = 0.028;', '''// Surface detail scales with the phone's small canvas. Physics retains its full lattice.
const MOBILE_RENDER = !new URLSearchParams(location.search).has('full') &&
  (matchMedia('(pointer: coarse)').matches || matchMedia('(max-width: 860px)').matches);
const NET_STEP = MOBILE_RENDER ? 0.042 : 0.028;''')
    replace_once('this.shadowSize = 2048; this.topSize = 1024;',
                 'this.shadowSize = MOBILE_RENDER ? 1024 : 2048; this.topSize = MOBILE_RENDER ? 512 : 1024;')
    replace_once('const QUALITY = [[1.6, 36], [1.3, 30], [1.0, 24], [0.8, 18]];', '''const QUALITY = MOBILE_RENDER
    ? [[1.25, 12], [1.0, 10], [0.85, 8], [0.75, 6]]
    : [[1.6, 36], [1.3, 30], [1.0, 24], [0.8, 18]];
  let performanceCheckActive = false;''')
    replace_once('let quality = 0;', 'let quality = MOBILE_RENDER ? 1 : 0;')
    replace_once('''  function resize() {
    const r = canvas.getBoundingClientRect();''', '''  function resize() {
    // A phone toolbar may emit resize events during a test. Keep its buffer/layers fixed.
    if (performanceCheckActive) return;
    const r = canvas.getBoundingClientRect();''')
    replace_once('if (dt > 1 / 38) slowT += dt;', 'if (dt > 1 / (MOBILE_RENDER ? 52 : 38)) slowT += dt;')
    replace_once('if (slowT > 1.5)', 'if (slowT > (MOBILE_RENDER ? 1.0 : 1.5))')
    # Buffer uploads do not require a fresh fur vector while paused and unchanged.
    replace_once('''  function skin() {
    const aw''', '''  function skin() {
    if (state.paused && !dirty) return false;
    const aw''')
    replace_once('let furPrimed = false, furCalm = 0;', 'let furPrimed = false, furCalm = 0, combDirty = true;')
    replace_once('''  function updateFur(dt, moved) {
    if (!furPrimed)''', '''  function updateFur(dt, moved) {
    if (furPrimed && dt === 0 && !moved && !combDirty) return false;
    combDirty = false;
    if (!furPrimed)''')
    replace_once('function smoothFur() { comb.set(combDefault); }',
                 'function smoothFur() { comb.set(combDefault); combDirty = true; }')
    # Brushing is another writer of comb directions; preserve it even while paused.
    replace_once('''    return touched;
  }''', '''    if (touched) combDirty = true;
    return touched;
  }''')
    return html
