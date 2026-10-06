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

The experiment article and mass/volume/energy/holding readouts are removed, including
their dedicated calculations. The static 10 cm scale note remains. Mass and volume
constraints used by the soft-body simulation remain necessary for the toy's behavior.

Expand **Performance checker** to see CPU breakdowns and optional WebGPU timestamps.
Its 16-second A/B check holds resolution and quality fixed, comparing full fur with
fur drawing off, both still and moving. It resets the toy and restores the controls.
GPU queries and diagnostic display updates run only while the checker is open or
testing. Results stay on the device. Desktop measurements do not predict phone FPS;
run the checker on the phone to identify its bottleneck.

Run `python adapt.py` to regenerate the runnable HTML after changing the adapter
or `webgl-fallback.js`, `instrument.py`, or `performance-check.js`. Serve `dist` over HTTP locally or HTTPS on a phone. Append
`?compat=1` to force WebGL2. `?q=0` through `?q=3` selects fixed rendering quality.

The original model comparison belongs to its creator; this working copy is for
the user's requested adaptation. No Claude runtime, sign-in, model calls, assets,
or external libraries are needed by the toy.
