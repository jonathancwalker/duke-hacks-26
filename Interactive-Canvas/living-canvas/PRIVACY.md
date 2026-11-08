# Privacy and consent

Three parts:

1. **The sign.** Print it and stand it next to the station.
2. **The on-screen notice.** The station shows it while it waits for a visitor.
3. **What the code does.** The facts behind every line, so the team can check the wording. Update this file whenever the code changes what is collected or sent.

---

## 1. The sign (print this)

> ### Living Canvas: what happens when you paint
>
> **Camera and microphone.** The camera follows your fingertip so you can draw in the air. The microphone hears your answer. We don't save any video or sound.
>
> **Your voice goes to Google.** Chrome sends your voice to Google to turn it into text. That's how Chrome's speech recognition works.
>
> **An AI reads your words.** Google's Gemini AI reads the text to pick the painters, the colors and a short mood label, like *"quiet hope after a hard week"*. The label never quotes you.
>
> **The computer that paints never hears you.** A rented graphics computer paints your picture. It gets only the color and painter choices. It never gets your words, your voice or your image.
>
> **What we keep tonight.** We keep the path your finger drew, your painting, the mood label and the painters' names. We don't keep your words.
>
> **Names are optional.** You never have to give one.
>
> **It's public.** The shared painting and the mood labels are on the big screen for everyone.
>
> *[Add this line when piece pages go live: "Your piece also gets its own web page. Anyone with the link can see it."]*
>
> **Rather not?** You can just watch. You can also walk away at any point. If you don't draw a path, nothing is saved. Want your entry removed tonight? Ask a team member. We'll delete your mood label and painting, but your strokes stay blended into the shared canvas.
>
> *Living Canvas · Duke Hackathon 2026*

---

## 2. The on-screen notice

This is the `consent` field in each `events/*.json`. It's a list of lines, so it can vary per event. `/api/event` returns it as one string, with the lines joined by `\n`.

```
The camera follows your fingertip and the mic hears your answer. We don't save video or sound.
Chrome sends your voice to Google to turn it into text, and Google's Gemini AI reads that text to pick your colors.
Your words aren't saved. We keep your path, your painting and a short mood label.
No name needed. The shared painting and mood labels are shown publicly.
Rather not? Just watch, or step away at any point: no path, nothing saved.
```

**Placing it on a screen.** `vibe/consent.js` renders the text. It brings its own styles and has no other dependencies.

```js
import { showConsent, hideConsent } from './consent.js';
showConsent(S.event.consent);             // default: small panel pinned top-left
showConsent(S.event.consent, myElement);  // inside your own layout; you position it
hideConsent();                            // while a visit runs
```

The station page (`vibe/flow.js`) shows it on the idle screen and hides it during a visit.

---

## 3. What the code does (station page `/vibe`)

| Data | Where it goes | Stored? |
|---|---|---|
| Camera video | Stays in the browser. MediaPipe finds the fingertip and wrists on the laptop (`vibe/hand.js`, `vibe/move.js`). Only the model files are downloaded from Google and jsDelivr; no frames are uploaded. | No frames are saved. The fingertip path (canvas x/y points) is saved as `strokes`. Wrist movement becomes one texture number and isn't saved. |
| Microphone audio | Chrome's Web Speech API (`vibe/audio.js`) streams it to Google for speech-to-text. Loudness is measured on the laptop. | Not saved by the booth. Google handles the audio under its own terms. |
| Spoken words (transcript) | Sent to the booth server as `feeling`, at most 200 characters, then to Gemini on Vertex AI (`brush_direct`). This only happens when `BOOTH_GCP_PROJECT` is set; otherwise local rules are used. | No. `visit_save` keeps only listed fields, and `booth/test_consent.py` checks that a saved visit never contains the words. |
| Mood label (`reading`) | Written by Gemini. It's told never to quote the visitor, and `safe_reading` filters it again. Shown on screen. | Yes. |
| Painters, energy, warmth, light, atmosphere | Sent to the GPU lab (a cloud VM) to paint the frame. The atmosphere phrase is written by Gemini, not the visitor. | Painter names are saved. |
| Painting and canvas images | Made on the GPU lab and on the page. | Yes, in `booth/visits/current/` (gitignored). Reset moves the folder aside; nothing is ever deleted automatically. |
| Name | The page doesn't ask for one yet. The server keeps up to 60 characters if a screen sends one. | Only if given. |

**Removing one visitor's entry.** Delete `booth/visits/current/NNNN.json`, `NNNN-mood.jpg` and `NNNN-canvas.jpg`. Later visits' canvas images still contain that visitor's strokes.

**Operator notes**

- Leave `BOOTH_LOG_WORDS` unset. It only affects the older `/` booth page (`booth.html`, `/api/visit`), which writes `booth/visits.jsonl`. When it's set to `1`, that log stores visitors' words. This sign covers `/vibe`.
- The Gemini line is shown even when Gemini is off and the rules director runs. It overstates what's sent, never understates it.

**Update this file and the `consent` lines when either of these lands:**

- **Presence embeddings (#7).** The transcript would go to the GPU lab, and a vector derived from the words may be saved as `presence`.
- **Piece pages (#26).** Add the public-page line to the sign and the on-screen notice.
