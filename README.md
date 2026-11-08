# Momento

**One moment, painted by everyone.**

Momento is a shared painting that a room makes together. Each person steps up, says how they feel, and traces a path in the air with their hand. Their mood repaints the canvas only where their hand went. By the end of the night, everyone who was there is in the painting, and you can watch it come together, one person at a time.

*Built at the Duke Hackathon 2026.*

<!-- Add a screenshot or short GIF of the projector here: docs/momento.gif -->

---

## Why we built it

Most of the ways we remember an event are solitary. We each take our own photos and videos, on our own phones, and look at them alone. They capture what happened, but none of them show that we were there *together*.

We wanted to build a memory that a group makes together:

- **Everyone contributes.** Nobody watches from the side. Each person leaves one mark, and it stays in the piece.
- **It's about people, not the tech.** Your mark comes from you: your words, your voice, how you move, the path your hand draws. Two people who say the same words still leave different marks.
- **AI as a collaborator, not a replacement.** The AI doesn't make the art for you. It turns each person's presence into paint, then helps all those marks become one painting instead of a mess.
- **Something to look back on.** At the end of the night, a replay shows the painting coming together person by person, closing on one line about what everyone made. You can download the final piece and keep it.

Interactive art is usually built for one person at a time. Momento is built for a room: concerts, games, museums, graduations, any night that people share.

---

## How a visit works (about 30 seconds)

1. **Answer one question out loud.** For example, "How are you feeling right now?" You can whisper, shout, laugh or ramble.
2. **We pick your painters.** Your words, how loudly you said them and how much you moved choose 3 real paintings, out of about 2,600, that match how you feel. "First snow of the year on the walk here" finds a Sisley snow scene. "In love, first date" finds Toulouse-Lautrec's *The Kiss*.
3. **Paint in the air.** Trace a path with your finger for 6 seconds. Close your fist to lift the brush.
4. **Watch it land.** The whole scene is repainted in your mood, but it shows only along your path. Your voice sets how strongly it comes through, and your movement sets how rough the edges are.
5. **Leave your mark.** Your strokes glow for a moment. You can add your name, and you get one line about how your moment is now part of the night.

## What the night produces

- **A live projector view** of the shared painting, updating within a second of each visit.
- **An idle loop** that replays recent visits when nobody is at the station.
- **A closing replay** of every visit, stroke by stroke, ending on the final painting and one reflection written from the whole night's moods.
- **A downloadable final piece.**
- **Event setup:** an organizer describes the night in a few sentences. Momento drafts the question, the starting scene and the tone of its writing, and the organizer edits any of it.

---

## How it works

| Step | What happens | Built with |
|---|---|---|
| **See and hear** | Tracks your hand, fist and body movement; hears your words and how loudly you say them | MediaPipe (runs in the browser), Web Speech API, Web Audio |
| **Understand** | Reads the feeling in your words, steered by your voice and movement | CLIP ViT-H text embeddings + a small trained head, blended with Gemini |
| **Match to art** | Scores 2,656 WikiArt paintings by how people said each one made them feel (ArtEmis), plus subject match; keeps the top 3 | Our presence scorer ([`presence/`](Interactive-Canvas/living-canvas/presence/README.md)) |
| **Paint** | Blends the 3 paintings' image embeddings into one point in an art-history space and repaints the scene in that style, aligned pixel for pixel with the shared canvas | SDXL-Turbo + IP-Adapter + ControlNet on a cloud GPU (NVIDIA L4) |
| **Reveal** | Shows the new painting only under your path, with brush-like edges | HTML canvas |
| **Write** | Your one line, the closing reflection and the event setup drafts | Gemini on Vertex AI, with safety checks and fixed fallback lines |

**What we tested before building.** We compared several ways of matching feelings to paintings on a fixed set of test visitors. Plain CLIP sent most feelings to the same few paintings, 25 of 40 to *The Scream*. In a blind side-by-side test of rendered paintings, the approach trained on human emotion ratings came out ahead. We built on that one. The full story is in [`HYPOTHESES.md`](Interactive-Canvas/living-canvas/HYPOTHESES.md).

**Built to survive a live event.** Every visit is saved, so a reload rebuilds the night. If the GPU, Gemini or the scorer drops out, the booth falls back to cached frames, simple rules or a palette wash, and the visit still finishes.

---

## Run it yourself

**You'll need:** a Mac or Linux laptop, Chrome, a webcam and mic, Python 3, and a Google Cloud project with a GPU VM. Gemini is optional: without it, Momento uses simple rules.

```bash
git clone https://github.com/jonathancwalker/duke-hacks-26.git
cd duke-hacks-26/Interactive-Canvas/living-canvas
./start.sh            # starts the GPU, opens a tunnel, waits for the models, runs the booth
```

Then open these in Chrome and allow the camera and microphone:

| Page | Use it for |
|---|---|
| http://localhost:8790/setup | Set up tonight's event |
| http://localhost:8790/vibe | The station people step up to |
| http://localhost:8790/gallery | The projector |
| http://localhost:8790/montage | The closing replay |

No camera handy? Press **Simulate** on the station for a pretend visitor.

- `start.sh` points at our own Google Cloud project, so change `PROJECT` at its top to yours. Setting up the GPU VM is covered in [`experiments/gcp/README.md`](Interactive-Canvas/living-canvas/experiments/gcp/README.md).
- [`OPERATOR.md`](Interactive-Canvas/living-canvas/OPERATOR.md) is the full checklist for running a night.
- The presence scorer needs a library built once from the ArtEmis dataset. Without it, Gemini picks the painters ([`presence/README.md`](Interactive-Canvas/living-canvas/presence/README.md)).
- **Stop the GPU when you're done.** It bills by the hour: `./stop.sh`.

## What's in the repo

```
Interactive-Canvas/living-canvas/
  vibe/          the station, projector, replay and event setup pages
  booth/         the Python server that ties it together
  presence/      words + voice + movement -> 3 paintings
  experiments/   the GPU service, Google Cloud setup and our experiments
  events/        one file per event: question, scene, tone
  HYPOTHESES.md  what we tried and what we learned
Shared-Canvas/   an earlier version: paint with your hands in a famous painter's style
```

## Privacy

- Hand and body tracking runs in your browser. No video or audio recordings are saved.
- What you say is sent to Google (speech recognition and Gemini) to read its feeling.
- Each visit saves your strokes, the painting, a short reading of your mood, the painters chosen and your name if you gave one.

## Credits and licenses

- **Team:** Jonathan Walker ([@jonathancwalker](https://github.com/jonathancwalker)), Rachel ([@rachhel](https://github.com/rachhel)) <!-- full names, roles, anyone else -->
- **Paintings:** the GPU service uses public-domain paintings from Wikimedia Commons. The scorer's library refers to WikiArt paintings, and their images aren't in this repo.
- **ArtEmis** (Achlioptas et al., 2021) is licensed for non-commercial research and education only. Nothing built from it is in this repo.
- **Models:** SDXL-Turbo, ControlNet, IP-Adapter and CLIP, each under its own license. MediaPipe by Google. Gemini via Google Cloud Vertex AI.
