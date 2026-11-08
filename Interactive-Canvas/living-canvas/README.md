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
3. Start the booth (first time: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`; `./start.sh` does steps 1–3 and this for you):
   ```bash
   cd booth && BOOTH_GCP_PROJECT=hackathon-514014 .venv/bin/python booth_server.py
   ```
4. Open http://localhost:8790 in Chrome: it opens the station (`/vibe`). The first booth page is still at `/booth`.

By default each visitor becomes a mix of real paintings plus intensity (`BOOTH_PLACEMENT=hybrid`). Add `BOOTH_PLACEMENT=axes` to go back to energy / warmth / light only.

**Brush experiment:** open http://localhost:8790/brush instead. You paint with your hands, in the hand of the painters Gemini picks from what you say (36 paintings), with a light AI glaze over your strokes afterward. Built on `Shared-Canvas`.

**Vibe paint:** open http://localhost:8790/vibe. Say how you feel, trace a path in the air with a finger, and the painting is repainted in your mood only along that path. The painters come from the presence scorer (`presence/`): your words, voice loudness and movement pick 3 of about 2,600 WikiArt paintings. It needs the packages in `booth/requirements.txt` and a one-time library build (see `presence/README.md`); without the library the Gemini director picks from the 36 lab paintings. **Simulate** runs a pretend visitor. Pick what the night starts from at the top: the chapel, a blank canvas the chapel emerges from, or a blank canvas for abstract mood paint.

**Gallery:** open http://localhost:8790/gallery fullscreen on the projector. It shows tonight's shared canvas, crossfades to each new visit within about a second, and shows the visitor count and event name. It has no controls and no camera. A reload brings back the current canvas.

**Events:** each event is one JSON file in `events/` (`name`, `kind`, `question`, `scene`, `closing`, and optionally `context`, `voice` and `date`). The vibe page asks the event's question, paints its scene, and ends each visit with its closing line; `context` and `voice` guide the booth's writing.

**Event setup:** open http://localhost:8790/setup before the night. Enter the event's name, kind, date and a few sentences about what tonight is about, then **Draft with Gemini** to get the question, the base scene, a writing voice and a closing line (with Gemini off you get a simple draft by kind). Edit anything, **Preview scene** to see the base painting from the GPU, then **Save and go live**. It writes `events/<name>.json`, makes it the active event at once and opens the station (`/vibe`) on it; if the event changed and tonight already has visits, it first offers to start a fresh night on the new scene. A station open elsewhere picks the event up on its next Reset or reload. **Start a fresh night** moves tonight's visits aside, like the station's Reset. The active event survives a restart (`events/.active`, not in git); `BOOTH_EVENT=concert` overrides it at startup, and a page can ask for another with http://localhost:8790/vibe?event=concert.

Stop the GPU when you're done (`gcloud compute instances stop ...`, same flags). You also need `experiments/.lab.json` with the lab URL and token; it's kept out of git, so ask the team for it.

## Folders

- `booth/`: the booth page and server
- `brush/`: the brush experiment page
- `vibe/`: the vibe paint page
- `presence/`: words + voice + movement → 3 paintings (`/api/presence`). Built from ArtEmis, which is licensed for non-commercial research and education only: the built library stays outside git.
- `experiments/`: the GPU lab, experiments, and Google Cloud setup
- `prototype/`, `artifact/`: early prototypes and explainer pages
- `HYPOTHESES.md`: what we tried and what we learned

## Code layout (vibe page)

`vibe/vibe.html` is markup only; it loads `vibe.css` and one module entry, `flow.js`. The booth server serves `/vibe/*.js` and `/vibe/*.css`.

- `flow.js`: the visit state machine (speak → brush → trace → reveal → commit), start modes, Simulate, buttons
- `hand.js`: camera + MediaPipe HandLandmarker, mirrored fingertip positions (`startCamera`, `readTips`)
- `audio.js`: mic loudness and Web Speech → `{ feeling, arousal }` (`listen`)
- `render.js`: canvas layout, linen start, glowing trails while tracing, bristle-masked reveal
- `api.js`: calls to `/api/brush`, `/api/presence`, `/api/vibe/base`, `/api/vibe/render`
- `state.js`: shared state (`S`: canvas size, painting, start mode), DOM handles, small helpers
