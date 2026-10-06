# Plush Octopus — Claude Opus version

Copied from the publicly shared artifact supplied by the user:
https://claude.ai/artifact/C86ZNoRcqpt8Q8AZxupTZn

`reference/original.html` is the original source, without Claude's frame wrapper.
`dist/index.html` is the runnable, self-contained version with mobile adaptations.
The original procedural geometry, tetrahedral physics, fur, and interactions are preserved.

Changes: larger phone controls, responsive layout and safe areas, conservative
initial phone rendering quality, suspension while the tab is hidden, and a WebGL2
compatibility renderer for browsers without WebGPU. The compatibility renderer
uses the same deforming mesh and simulation, with simplified lighting and fur shading.

Run `python adapt.py` to regenerate the runnable HTML after changing the adapter
or `webgl-fallback.js`. Serve `dist` over HTTP locally or HTTPS on a phone. Append
`?compat=1` to force WebGL2. `?q=0` through `?q=3` selects fixed rendering quality.

The original model comparison belongs to its creator; this working copy is for
the user's requested adaptation. No Claude runtime, sign-in, model calls, assets,
or external libraries are needed by the toy.
