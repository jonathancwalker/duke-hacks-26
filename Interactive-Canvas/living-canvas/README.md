# Living Canvas

Step up, talk and move for 10 seconds, and a shared painting changes with you.

**How:** webcam + mic → Gemini reads how you are → a point among 18 real paintings → a GPU repaints the chapel.

## Run it

1. Start the GPU:
   ```bash
   gcloud compute instances start living-canvas-gpu --zone us-central1-b --project hackathon-514014
   ```
2. Open the tunnel (leave it running):
   ```bash
   gcloud compute ssh living-canvas-gpu --zone us-central1-b --project hackathon-514014 -- -N -L 8765:localhost:8765
   ```
3. Start the booth (first time: `python3 -m venv .venv && .venv/bin/pip install google-genai`):
   ```bash
   cd booth && BOOTH_GCP_PROJECT=hackathon-514014 .venv/bin/python booth_server.py
   ```
4. Open http://localhost:8790 in Chrome and press **Step up**.

By default each visitor becomes a mix of real paintings plus intensity (`BOOTH_PLACEMENT=hybrid`). Add `BOOTH_PLACEMENT=axes` to go back to energy / warmth / light only.

**Brush experiment:** open http://localhost:8790/brush instead. You paint with your hands, in the hand of the painters Gemini picks from what you say (36 paintings), with a light AI glaze over your strokes afterward. Built on `Shared-Canvas`.

**Vibe paint:** open http://localhost:8790/vibe. Say how you feel, trace a path in the air with a finger, and the painting is repainted in your mood only along that path. **Simulate** runs a pretend visitor. Pick what the night starts from at the top: the chapel, a blank canvas the chapel emerges from, or a blank canvas for abstract mood paint.

**Events:** each event is one JSON file in `events/` (`name`, `kind`, `question`, `scene`, `closing`). The vibe page asks the event's question, paints its scene, and ends each visit with its closing line. Pick the event with `BOOTH_EVENT=concert` (default `museum`), or per page with http://localhost:8790/vibe?event=concert. Add an event by adding a file; no code changes.

Stop the GPU when you're done (`gcloud compute instances stop ...`, same flags). You also need `experiments/.lab.json` with the lab URL and token; it's kept out of git, so ask the team for it.

## Folders

- `booth/`: the booth page and server
- `brush/`: the brush experiment page
- `vibe/`: the vibe paint page
- `experiments/`: the GPU lab, experiments, and Google Cloud setup
- `prototype/`, `artifact/`: early prototypes and explainer pages
- `HYPOTHESES.md`: what we tried and what we learned

## Code layout (vibe page)

`vibe/vibe.html` is markup only; it loads `vibe.css` and one module entry, `flow.js`. The booth server serves `/vibe/*.js` and `/vibe/*.css`.

- `flow.js`: the visit state machine (speak → brush → trace → reveal → commit), start modes, Simulate, buttons
- `hand.js`: camera + MediaPipe HandLandmarker, mirrored fingertip positions (`startCamera`, `readTips`)
- `audio.js`: mic loudness and Web Speech → `{ feeling, arousal }` (`listen`)
- `render.js`: canvas layout, linen start, glowing trails while tracing, bristle-masked reveal
- `api.js`: calls to `/api/brush`, `/api/vibe/base`, `/api/vibe/render`
- `state.js`: shared state (`S`: canvas size, painting, start mode), DOM handles, small helpers
