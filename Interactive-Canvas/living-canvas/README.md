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

**Brush experiment:** open http://localhost:8790/brush instead. You paint with your hands, in the hand of the painters Gemini picks from what you say (36 paintings), with a light AI glaze over your strokes afterward. Built on `Shared-Canvas`.

Stop the GPU when you're done (`gcloud compute instances stop ...`, same flags). You also need `experiments/.lab.json` with the lab URL and token; it's kept out of git, so ask the team for it.

## Folders

- `booth/`: the booth page and server
- `brush/`: the brush experiment page
- `experiments/`: the GPU lab, experiments, and Google Cloud setup
- `prototype/`, `artifact/`: early prototypes and explainer pages
- `HYPOTHESES.md`: what we tried and what we learned
