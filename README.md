# Plush Octopus — Claude Opus version

Copied from the publicly shared artifact supplied by the user:
https://claude.ai/artifact/C86ZNoRcqpt8Q8AZxupTZn

`reference/original.html` is the original source, without Claude's frame wrapper.
`dist/index.html` is the runnable, self-contained version with mobile adaptations.
The original procedural shape, tetrahedral physics, fur, and interactions are preserved.

Changes: larger phone controls, responsive layout and safe areas, conservative
initial phone rendering quality, suspension while the tab is hidden, and a WebGL2
compatibility renderer for browsers without WebGPU. The compatibility renderer
uses the same deforming mesh and simulation, with simplified lighting and fur shading.

Phone-sized screens and touch devices now use a lighter surface mesh (15,498 vertices,
28,432 body triangles), 10 starting fur layers, and smaller shadow maps. Automatic
quality can reduce fur to 8 or 6 layers. The complete 2,608-node physics lattice stays
in use. Larger desktop screens retain the full surface mesh and quality ladder.
Append `?full` to compare the full rendering profile on a phone. A page reload selects
the surface profile; resizing alone does not rebuild it.

The experiment article and mass/volume/energy/holding readouts are removed, including
their dedicated calculations. The static 10 cm scale note remains. Mass and volume
constraints used by the soft-body simulation remain necessary for the toy's behavior.

The caption and controls header, plus the stuffing, pile, and damping sliders, are removed, together
with their slider listeners and styling. The toy uses its fixed simulation defaults.
The top label reads Volks Games; the old study number and duplicate branding are removed.

The **Performance checker** is hidden on every page load. Press **Shift+P** or click/tap
**Volks Games** five times quickly to reveal it. Repeat either gesture to hide it;
**Escape** also hides it and cancels an active check. Revealing it shows CPU breakdowns
and optional WebGPU timestamps. Hidden diagnostics do not update or issue GPU queries.
Its 16-second A/B check holds resolution and quality fixed, comparing full fur with
fur drawing off, both still and moving. It resets the toy and restores the controls.
GPU queries and diagnostic display updates run only while the checker is open or
testing. Phone toolbar height changes no longer cancel checks: rendering resolution
and layers stay fixed throughout the run. A width/orientation change or hidden tab
still cancels it. Results stay on the device. Desktop measurements do not predict phone FPS;
run the checker on the phone to identify its bottleneck.

Run `python adapt.py` to regenerate the runnable HTML after changing the adapter
or `webgl-fallback.js`, `optimize.py`, `instrument.py`, or `performance-check.js`. Serve `dist` over HTTP locally or HTTPS on a phone. Append
`?compat=1` to force WebGL2. `?q=0` through `?q=3` selects fixed rendering quality.

The original model comparison belongs to its creator; this working copy is for
the user's requested adaptation. No Claude runtime, sign-in, model calls, assets,
or external libraries are needed by the toy.
