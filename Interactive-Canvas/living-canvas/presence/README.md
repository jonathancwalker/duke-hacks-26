# Presence scorer

`POST /api/presence` turns what a visitor says, how loud they say it and how much they move into 3 painting weights.
It is "C5", the scorer that won the blind feeling-space eval: **feeling** from human emotion votes plus **subject**
from a trained text-to-painting space, over about 2,600 WikiArt paintings.

```
POST /api/presence  {"feeling": "First snow of the year on the walk here.", "loudness": 0.3, "movement": 0.2}
-> {"artists": [{"name", "weight", "label", "title", "votes", "emotion_z", "subject_z"}, ...3],
    "vectors": {name: [1024 floats]},          # CLIP ViT-H image vectors: /api/vibe/render takes them as "vectors"
    "read": {"source": "head" | "head+gemini", "emotions", "head", "gemini", "clarity", "arousal"},
    "library": 2656, "ms": 9.0}
```

`loudness` falls back to `arousal` (what `listen()` sends); both are 0..1. `wait_s` (up to 3) waits for Gemini.
503 when the scorer is not loaded; the vibe page then uses the director's painters.

## How it scores

1. **Emotion read** over ArtEmis's 9 emotions: a linear head on the CLIP text embedding, answered at once. The first
   call for a sentence also asks Gemini (temperature 0, same 9 emotions) in the background; later calls for the same
   words blend 50/50 once it is back. "something else" is dropped and the rest renormalised.
2. **Voice and movement steer**: arousal = (loudness + movement) / 2 multiplies excitement, anger and fear by
   exp(steer × (arousal − 0.5) × clarity), and contentment and sadness by its inverse. Clarity = 1 − normalised
   entropy of the read, so a vague read is steered less.
3. **Emotion score** = steered read · PMI of each painting's human vote distribution, smoothed toward the corpus prior
   with `prior_votes` pseudo-votes.
4. **Subject score** = cosine in the trained contrastive space (text tower with an arousal input vs image tower,
   library centred), so "first snow" reaches snow paintings.
5. **score** = z(emotion) + λ · z(subject) over the whole library; top 3; weights = softmax of their z-scores.

The vibe page calls it once when the visitor stops talking (starts the Gemini read) and again after the director
answers (usually with Gemini's read by then), and renders with those paintings. The director still sets energy,
warmth, light, atmosphere, the reading and the trail palette.

## Settings (`config.json`, re-read when it changes; no restart, no code change)

| key | default | what it does |
|---|---|---|
| `lambda` | 1.0 | weight of the subject score against the emotion score |
| `votes.min` | 6 | only paintings with at least this many ArtEmis votes (6 → 2,656 paintings; 10 → 282) |
| `votes.soft_k` | 0 | soft count weighting: a painting's emotion score × n / (n + soft_k), so thin-vote paintings lean neutral (0 = off) |
| `prior_votes` | 10 | pseudo-votes that pull each painting's vote profile toward the corpus prior |
| `steer` | 2.0 | strength of the voice/movement steer |
| `gemini_weight` | 0.5 | share of Gemini's read in the blend |
| `top_k` | 3 | paintings returned |
| `library_dir` | `~/.cache/living-canvas/presence` | the built library (or `PRESENCE_DIR`) |

`PRESENCE_CONFIG` points the booth at another config file.

## Build the library (once per machine)

Needs the ArtEmis cache (`ARTEMIS_CACHE`, from `experiments/space/artemis_01_build.py`) and the eval board's
restatements (`c4_restatements.json` and `c4_restatements_emb.pt`). Training takes about 20 s on a laptop.

```bash
uv run --no-project --with torch,transformers,pandas,pyarrow,numpy,pillow python -I presence/build.py --restatements <dir>
```

The booth needs `torch` and `transformers` in its environment (the CLIP ViT-H text tower runs locally, on the Apple GPU
when there is one, about 10 ms per sentence).

## Tests

```bash
uv run --no-project --with pytest,torch,transformers,numpy python -I -m pytest presence booth -q -s
PRESENCE_EVAL_OUT=<eval board out/> ... # adds the regression: the 9 board cases pick what the board's C5b picked
```

## Data terms

ArtEmis is licensed for **non-commercial research and education only**. Everything built from it (the library,
the vote profiles, the restatements, any renders) stays outside git and must not be shared beyond the project.
The paintings' images and metadata come from WikiArt.
