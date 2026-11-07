# Living Canvas — validation brief

**One-liner:** Step up to the screen, answer one question, and your face and hands paint a 15-second stroke into a shared artwork that everyone at the event builds together. You leave with a snapshot of the piece with your part highlighted.

## Why it's more than a filter (the AI/ML story)

Three layers, each one a real model doing real work:

| Layer | What it does | Model | Where it runs |
|---|---|---|---|
| **1. Perception** | Reads hands (21 landmarks each, 2 hands) and face (478 landmarks + 52 expression blendshapes) at ~30fps | MediaPipe Hand Landmarker + Face Landmarker | On-device, in the browser (WASM/GPU) |
| **2. Expression → brush mapping** | Turns signals into a brush "signature": smile → warmth/brightness, jaw open → burst of paint, brow raise → longer flowing strokes, pinch → brush width, hand speed → spread | Hand-designed feature mapping (v0) → learned mapping (v1, see below) | Browser |
| **3. Synthesis** *(v1)* | Turns the crowd's raw strokes into one coherent painting, using the strokes as structure | img2img / ControlNet (scribble) on SDXL-Turbo or Flux via hosted API | Server / API |

The v1 upgrade for layer 2 is the "solid ML" talking point: instead of hand-written rules, embed each contributor's 52-dim blendshape trace + motion features and cluster them, so the canvas groups similar "energies" together. That's also what makes the final piece compose instead of turning to mud.

## Riskiest assumptions (what v0 tests)

1. **Feel:** does body input make marks that feel good in under 15 seconds? *(If people's strokes look like a toddler's mouse scribble, the concept dies.)*
2. **Composition:** do 10+ contributors add up to something beautiful, or to brown mud? → the **Simulate crowd** button tests this in seconds.
3. **Booth reality:** one laptop + webcam, bad lighting, people walking behind. Does tracking hold?
4. **Is the ML visible?** Judges need to *see* the model working → live signal bars + landmark overlay.

## v0 prototype (this folder)

`prototype/index.html`, a single file with no build step.

- Webcam → MediaPipe hands + face → flow-field particle brush
- Mood question with 4 answers → palette
- 15s turns, per-contributor layers, "your moment" highlight PNG
- Replay (layer-by-layer build), save full piece
- Mouse fallback + **Simulate crowd** (synthetic contributors) for testing without people

Run it: `python3 -m http.server 5173 --directory Interactive-Canvas/prototype`, then open http://localhost:5173. The webcam needs localhost or https.

## Not in v0

- Multi-device / phone contribution (shared state over websockets)
- AI synthesis render (layer 3)
- QR-code share of your moment
- Partnerships, payments, famous co-creator: these are go-to-market ideas, not things to validate tonight
