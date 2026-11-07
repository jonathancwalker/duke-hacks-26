# Living Canvas: how a person's presence becomes part of the painting

**The goal:** a person's expression is encoded, added to a running representation of everyone who came before, and the change shows up in the art in a way that means something, not just as a random shift.

**What we learned so far:** turning people into scene descriptions only changes *what is depicted* (night, a moon, snow). Real art carries feeling through *form*: brushwork, palette, edges, density, abstraction. A person's presence has three channels:

| Channel | What it is | Kind of sign |
|---|---|---|
| **Trace** | The physical mark of you being here: your gesture, your rhythm | Index (caused by you, like a footprint) |
| **Temperament** | How you were: energy, warmth, tension, softness | Form |
| **Meaning** | What you said | Symbol (use sparingly) |

## Hypotheses

### H1 · Art-history embedding space
- **Encode:** your temperament becomes a point in CLIP's shared text-and-image space, located by its nearest real artworks (Rembrandt, Turner, Hokusai, Monet, Van Gogh, Munch, Klimt, Kandinsky and others).
- **Aggregate:** the crowd is a weighted blend of artworks, and its center moves through art history.
- **Shows up:** an IP-Adapter conditions the painting on that blend, so style and form change while the subject stays put.
- **Interesting because:** the space is made of real art, the math happens on real embeddings, and each person gets "your moment was closest to Turner's *Rain, Steam and Speed*."

### H2 · Trace underpainting
- **Encode:** your actual gesture path (webcam) and rhythm (voice) are rendered as brush strokes, in your temperament.
- **Aggregate:** everyone's strokes stack as layers, re-rendered from saved inputs so they never degrade.
- **Shows up:** a diffusion model paints a finish over the stacked underpainting, so your marks literally stay in the painting.
- **Interesting because:** it's a hybrid of a procedural renderer and diffusion. It's the only hypothesis where the presence is an index, physically caused by you.

### H3 · Form directions (art-theory axes)
- **Encode:** you become coefficients on five art-theory axes: energy, color temperature, edges, density and abstraction. Each axis is a direction in the model's conditioning space, averaged over several paraphrased prompt pairs, so it changes form, not subject.
- **Aggregate:** the crowd's mean coefficients, which can be read and explained.
- **Shows up:** conditioning arithmetic plus guidance push.
- **Interesting because:** these are training-free "concept slider" directions that are separate from each other and easy to explain.

### H4 · The crowd as a distribution, not just an average
- **Encode:** any of H1–H3.
- **Aggregate:** the mean sets temperament, the spread sets tension. A united crowd looks harmonious; a divided crowd shows clashing color and fractured forms. Two crowds with the same average can look different.
- **Interesting because:** the painting shows how a room agrees or disagrees, not only its average mood.

## How we test each one

| Test | Pass if |
|---|---|
| **Same sentence, two temperaments** | Calm vs agitated delivery of the same words gives clearly different paintings in form |
| **Blind match** | Classmates match three people to their three paintings above chance |
| **Marks survive** (H2) | Each person's gesture is still findable after the diffusion finish |
| **Same mean, different spread** (H4) | A united crowd and a divided crowd look different |
| **Pretty** | It reads as a painting, never as mush or a poster |
| **Speed** | Under about 3 s per frame on the booth GPU |

## Round 1 experiments (`experiments/lab/`)
- `e1_art_space.py`: H1. The four personas' top artworks, plus full and style-only IP-Adapter conditioning.
- `e2_trace.py`: H2. Four people's gestures stacked, then diffusion-finished at three strengths.
- `e3_form_axes.py`: H3. Each axis swept −1 / 0 / +1, then the four personas mapped onto the axes.
- `e4_crowd_stats.py`: H4. A united and a divided crowd with the same mean, with and without the tension term.

The personas use synthetic voice, movement and gesture values until the webcam and mic are wired up.

## Round 1 results (2026-11-07, T4 GPU, about 1.5 s per frame)

| | Result | What we learned |
|---|---|---|
| **H1 art space** | ✅ works, after one fix | Retrieval makes sense (grief → Whistler's *Nocturne*, resolve → Monet's *Impression, Sunrise*). A Canny lock held for every step flattens style; **locking layout only for the first 50% of steps (0.35)** keeps the chapel and lets the style through. Walking from grief to joy is smooth. Flaw: CLIP retrieval mapped joy and anxiety to the same Kandinsky blend, ignoring valence. |
| **H2 trace** | ⚠️ partial | Raw traces read as scribbles. A diffusion finish at 0.5 erases the gesture's shape but keeps its color as scene elements (joy's orange becomes an autumn tree). Next: put the traces into the control image so they become structure. |
| **H3 form axes (text)** | ❌ | Text directions such as "agitated vs calm brushwork" barely move SDXL-Turbo, even with push 3. |
| **H3 form axes (art space)** | ✅ **strong** | Axes defined as directions between groups of paintings in the IP-Adapter's CLIP image space: energy (calm Monet/Whistler → bold Van Gogh/Turner), temperature (cool moonlit → golden), discord (harmonious → fractured). All four personas, joy and anxiety included, are clearly different. |
| **H4 crowd spread** | ✅ in art space | United and divided crowds with the same mean look identical without the spread term. Adding discord in proportion to spread makes the divided crowd visibly turbulent. |

**Core recipe so far:** a person becomes coefficients on art-space axes. The crowd is the mean of those, plus discord from their spread, giving a point in the CLIP image space of real paintings. An IP-Adapter at 0.85 with a Canny lock (0.35, first 50% of steps) on SDXL-Turbo renders it: no guidance, 4 steps, about 1.5 s per frame on a T4.

## Round 2 results: a whole night (16 visitors, about 1.3 s per frame on a T4)

- **Individual presence: ✅ visible.** All 16 "your moment" frames are distinct and read as their visitor: anger is a stormy *Starry Night*, missing grandma is a moonlit nocturne with lit windows, "quiet, peaceful, home" is soft and still.
- **Crowd painting: ✅ follows the night, but subtly.** Calm, then moonlit and stormy after stress and grief, then bright, then stormy after anger, then calm. Averaging a mixed crowd keeps it near the center of the art space, so frame-to-frame changes are gentle. It can be tuned by amplifying the crowd's distance from the center.
- **Discord calibration:** v1 (1.6 × spread) saturated by visitor 3, because any varied night has a spread around 0.7. The fix responds only to unusual division (`(spread − 0.45) × 1.6`, capped at 0.7) and leaves discord out of the personal moment frames.
- **Mapping flaw:** temperature equals positivity, so "first snow" renders warm. Claude as art director, reading meaning, should set temperature.
- **Readout flaw:** the library's center is closest to Munch and Van Gogh, so "crowd nearest" often says *The Scream* even when the painting looks calm. Recenter the space, or describe the crowd's position by its axes instead.
- **Film:** each visitor eases into their moment, holds, then settles into the crowd. The fixed seed keeps the composition still, so the transitions are smooth.

## Round 3 results: real inputs (2026-11-07)

- **Claude as art director beats the hand-set rule on meaning.** Grandma goes properly dark (one lit window); first snow goes cool and hushed instead of warm. Tested with Claude writing the coefficients in-session; the booth calls the API.
- **The art space only reaches where its paintings live.** "Hot, dark, violent" anger rendered bright yellow until Goya, Delacroix (×2) and Géricault joined the library (now 18 paintings). The axes were already nearly independent (cosine 0.06), so orthogonalizing and rebalancing changed nothing. Coverage was the fix.
- **Figure-heavy paintings leak content.** At full IP-Adapter strength, anger and joy brought crowds of figures into the scene, anger as a brawl. **Style-only injection at 1.2** keeps palette and drama without figures and still separates calm cases. That's the booth default.
- **Booth works end to end (simulated visitors):** capture page → local booth server → director → Colab GPU → "your moment" then "crowd after". About 2.5 s of GPU time per visit; the director adds Claude latency.
- **Not yet verified:** real webcam, mic and speech capture (the browser pane blocks devices), the Laban and prosody calibration on real people, and the live Claude director (needs the `anthropic` package and credentials on the booth laptop).

## Round 4 results: a mix of paintings instead of three axes (2026-11-07)

**Question:** does placing a visitor as a weighted blend of real paintings, which Gemini picks (2–4 of the 18), encode them better than the three hand-built axes (energy, warmth, light)?

**Setup:** 9 test visitors, including the same neutral sentence whispered-and-still and loud-and-animated. Gemini 3.8 Flash gave both readings for each. Rendered on the L4 with identical settings (style-only 1.2, early outline lock, fixed seed). "Output spread" = mean pairwise cosine distance between the CLIP embeddings of the rendered frames (higher = visitors look more different).

| Scheme | Input spread | Output spread |
|---|---|---|
| axes (current booth) | 0.397 | 0.162 |
| mix | 0.287 | 0.168 |
| mix pushed ×1.75 from the library center | 0.556 | 0.222 |
| **hybrid: mix ×1.5 + 0.6 × axes** | **0.623** | **0.220** |

- **Gemini's picks are art-historically sensible.** Grief → Turner's *Temeraire* + Whistler; stress → Munch + Van Gogh; snow → Friedrich + Monet; anger → Goya + Delacroix. With identical words, the body alone flips the mix from Seurat (still) to Kandinsky (animated).
- **A plain mix dilutes.** A blend of paintings sits between them, near the library center, so grief, stress and anger came out muted. Axes can reach past any single painting (darker than any of them).
- **Pushing the mix outward restores distinctness but not darkness.** Anger stays grey and stress stays bright yellow.
- **The hybrid is best by eye and ties for best on output spread (+36% over the current axes).** The mix supplies character (Friedrich's mist, Kandinsky's florals, Munch's sky); the axes supply intensity (anger's dark amber).
- **Cost:** the mix call took 4–6 s versus 3–5 s for axes. The booth would need one combined Gemini call returning both.
- **Caveats:** 9 visitors, one seed, one Gemini call each; output spread is a proxy, not a human judgment. "Nearest painting of each output" was dropped as a metric because every frame shows a pond, so it measured subject, not style.

## Vibe paint: mood only along the hand path (2026-11-07)

- **Same seed + outline lock = pixel-aligned mood frames.** Each visitor's frame repaints the whole chapel in their mood, and it lines up with the current painting, so the page can show it only along their path with no seams.
- **Style-only injection at 1.4, plus the energy, warmth and light axes, carries tone as well as brushwork.** Grief goes dark and misty, triumph bright and flat, nerves swirl. Full injection (0.7 and 0.85) brings figures back.
- **Start calm and pale.** On a bold starting painting, bright moods disappeared into it. A pale underpainting lets every path read, and the visits stack.
- **Overlaps read stronger.** Each piece of a path adds 70% of the mood, so crossings come through fully.
- **Not yet verified:** real camera and mic in the vibe page (the browser pane blocks devices). Only tested with Simulate.

## Vibe paint round 3: why moods looked alike (2026-11-07)

- **Gemini isn't the bottleneck.** Across 12 feelings it chose 17 different painters.
- **The scene prompt is.** "Chapel above a garden pond" pulls every mood toward the same greens: calm and bored, grief and homesick came out nearly identical.
- **What didn't help:** color words in the prompt, letting the lead painter dominate the blend, palette matching to the paintings' pixels, and starting from the chapel recolored in the painters' palettes (the model repaints it green, and the moods converge further).
- **What helped:** letting the mood set the scene's **light and weather** (Gemini writes it: "at night, one candle-lit window", "in full spring bloom, turquoise sky"). Spring turns turquoise, exam nerves get rain streaks, homesick gets snow and a moon.
- **Most distinct: no scene at all.** Abstract frames (same painters and axes, no chapel) differ in color *and* form: grief grey slashes, triumph Kandinsky shapes, love Klimt mosaic.
- **Blank canvas, two ways:** paths reveal the chapel in each visitor's mood (it emerges over the night), or lay down abstract mood paint. Brush-like ragged mask edges keep paths from looking like cut-out tubes on linen.

## Feeling space A: repair CLIP matching (2026-11-07)

**Question:** can CLIP text→painting matching stop collapsing onto a few hub paintings without an LLM picking painters?

**Setup** (`experiments/space/clip_*.py`, run on a Mac with MPS, no GPU VM):
- Both towers of `laion/CLIP-ViT-H-14-laion2B-s32B-b79K`. The image tower is the IP-Adapter's encoder family, and the embeds are the same projected `image_embeds` the lab's `clip_image` returns.
- Libraries: the lab's 36 paintings from Wikimedia Commons, and the same 36 plus 269 WikiArt paintings, for 305 in all. The WikiArt subset is stratified by style from `huggan/wikiart` via the datasets-server rows API, with only the kept images downloaded (148 MB).
- Test set: the shared 40 statements in `feelings.json`, scored with `metrics.report_scores` (unchanged).
- Every score matrix is globally rescaled to the baseline's spread before scoring, which leaves rankings unchanged. `topk_dist` uses a fixed temperature, so without this the pair metrics would reward a method's score scale rather than its picks.
- New metrics, kept in `clip_run.py`:
  - **para lift@3:** paraphrase top-3 overlap minus the overlap of random non-paraphrase pairs. Agreement that comes free from everyone landing on the same hub doesn't count.
  - **top1 ent/picks:** top-1 entropy normalised by log(min(40, N)), so the 36- and 305-painting libraries compare.
- Fixes need a reference text bank. Two hand-written banks, both separate from the test statements:
  - **Rwords:** 78 emotion words.
  - **Rsent:** 50 visitor-style sentences on mixed and neutral topics, standing in for a log of past visitors.
- Full table: `experiments/space/out/clip_results.md`. Board: `experiments/space/out/clip_board.png`.

| library | prompt / ref bank | method | top1 unique | top1 ent/picks | max share | hubness k5 | para overlap@3 | para lift@3 | para/rand | opp/rand | biggest hub |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 36 | – | random scores (reference) | 23 | 0.82 | 0.10 | 0.74 | 0.12 | 0.03 | 1.02 | 0.95 | – |
| 36 | "a painting that feels …" | **cosine (today)** | 9 | 0.44 | 0.55 | 1.84 | 0.53 | 0.24 | 0.67 | 0.91 | Friedrich 22/40 |
| 36 | "the mood of this artwork is like: …" | cosine | 14 | 0.59 | 0.35 | 1.59 | 0.43 | 0.13 | 0.73 | 0.97 | Friedrich 14/40 |
| 36 | "an artwork expressing this emotion: …" | cosine | 10 | 0.39 | 0.62 | 2.16 | 0.53 | 0.21 | 0.73 | 0.97 | Munch 25/40 |
| 36 | 5-prompt ensemble | cosine | 10 | 0.52 | 0.30 | 1.88 | 0.55 | 0.23 | 0.73 | 0.96 | Friedrich 12/40 |
| 36 | today's prompt | center images only | 9 | 0.41 | 0.60 | 1.89 | 0.52 | 0.20 | 0.76 | 0.94 | Friedrich 24/40 |
| 36 | today's / Rsent | modality-gap shift | 10 | 0.57 | 0.23 | 1.72 | 0.50 | 0.19 | 0.72 | 1.03 | Munch 9/40 |
| 36 | today's / Rsent | whiten (16 PCs of library) | 19 | 0.77 | 0.15 | 0.63 | 0.27 | 0.15 | 0.77 | 0.94 | Goya 6/40 |
| 36 | today's / Rsent | CSLS hub penalty | 19 | 0.77 | 0.12 | 1.46 | 0.37 | 0.20 | 0.70 | 1.00 | Friedrich 5/40 |
| 36 | today's / Rsent | per-painting z-score | 18 | 0.77 | 0.10 | 0.69 | 0.42 | 0.30 | 0.75 | 1.00 | Bruegel 4/40 |
| 36 | today's / Rwords | center both | 17 | 0.73 | 0.15 | 1.25 | 0.35 | 0.17 | 0.74 | 0.91 | Renoir 6/40 |
| 36 | today's / **Rsent** | **center both** | 24 | 0.85 | 0.10 | 0.39 | 0.33 | 0.24 | 0.76 | 0.97 | Tanner 4/40 |
| 36 | today's / Rsent half A · half B | center both | 21 · 24 | 0.80 · 0.85 | 0.12 · 0.10 | 1.09 · 0.23 | 0.37 · 0.32 | 0.26 · 0.22 | 0.72 · 0.74 | 1.03 · 0.97 | – |
| 36 | today's / Rsent | center both + z-score | 21 | 0.81 | 0.10 | 0.84 | 0.38 | 0.28 | 0.71 | 1.00 | Monet 4/40 |
| 36 | today's / Rsent half A · half B | center both + z-score | 19 · 17 | 0.80 · 0.74 | 0.10 · 0.15 | 0.84 · 0.85 | 0.33 · 0.32 | 0.21 · 0.21 | 0.72 · 0.74 | 1.01 · 1.02 | – |
| 36 | today's / the 40 test statements* | center both | 24 | 0.85 | 0.10 | 0.22 | 0.32 | 0.24 | 0.76 | 1.01 | Tanner 4/40 |
| 305 | – | random scores (reference) | 37 | 0.97 | 0.05 | 1.08 | 0.00 | -0.01 | 1.01 | 1.00 | – |
| 305 | today's prompt | cosine | 17 | 0.65 | 0.28 | 6.26 | 0.37 | 0.20 | 0.72 | 1.04 | Friedrich 11/40 |
| 305 | today's / **Rsent** | **center both** | 35 | 0.95 | 0.05 | 1.56 | 0.18 | 0.16 | 0.84 | 0.99 | Rembrandt 2/40 |
| 305 | today's / Rsent | center both + z-score | 35 | 0.95 | 0.05 | 1.61 | 0.17 | 0.15 | 0.86 | 1.01 | Munch 2/40 |

\* Transductive: centred on the test statements themselves. It's only an upper bound; a booth would use a running mean of the night's visitors.

**What worked**
- **Centring both clouds is the repair.** Subtract the library's mean image embedding from each painting, and the mean of a bank of visitor-style sentences from each text, before cosine.
  - On 36 paintings: top-1 picks go from 9 to 24 distinct paintings, the biggest hub from 22/40 to 4/40, and hubness from 1.84 to 0.39 (random scores give 0.74).
  - Paraphrase lift holds at 0.24, the same as today. The fix removes collapse without losing the agreement that wasn't coming from hubs.
- **The reference bank matters more than the method.** The same centring with emotion *words* only reaches 17 distinct picks. With visitor *sentences* it matches the transductive upper bound. This held on each half of the sentence bank (25 sentences each).
- **Simplest is best.** Per-painting z-scores, CSLS and whitening reach similar spread. Stacking z-score on centring didn't hold up on the split halves (lift 0.21 on both halves vs 0.28 on the full bank).

**What didn't**
- **Prompt templates and ensembles only move the hub.** "Emotion" wording sends 25/40 to The Scream, and "mood" wording sends 14/40 to Friedrich.
- **Image-only centring and the modality-gap shift barely help.** Neither removes the direction all visitor sentences share, and centring the text side is what made the difference.
- **Nothing separates opposites.** opp/rand stays 0.91–1.04 for every method, so grief and triumph pick paintings no farther apart than random pairs. CLIP's text side encodes topic more than valence. This is the case for a trained feeling space (C) or an LLM step.
- **A bigger library alone doesn't fix collapse.** On 305 paintings plain cosine still sends 11/40 to Friedrich and hubness rises to 6.26. With centring it spreads well (35 distinct, max 2/40).
  - Exact top-3 paraphrase overlap drops (lift 0.16), partly because more near-equivalent paintings compete.
  - The board shows WikiArt's black-and-white Doré engravings and sketches winning rage, fear and anxious. They're bad style sources for the IP-Adapter, so a larger library needs curation (colour paintings only).

**Caveats**
- **Numbers are a screen.** 40 statements and 20 paraphrase pairs, so differences under ~0.05 in lift are noise. The human check on `out/clip_board.png` comes next.
- **Subject still beats feeling.** "Alone even in this crowd" picks crowd scenes, and "first snow" picks snow scenes.
- **The sentence bank was written by hand** while the test set was visible. A real visitor log is the honest version.
- **The WikiArt slice is narrow.** The datasets-server only indexes the first 11,320 rows, which are sorted by artist: 23 named artists plus "Unknown", 15 styles, heavy on Impressionism and Realism.
- **Encoder equivalence not checked.** I didn't confirm that the IP-Adapter's own encoder weights (`h94/IP-Adapter` `models/image_encoder`) produce identical embeds to the LAION image tower; both are OpenCLIP ViT-H-14.
- **Input differs from production.** Today's production text is Gemini's temperament line, not the raw visitor sentence scored here.

Reproduce (from `experiments/space/`): `uv run --no-project --with numpy python -I clip_wikiart.py`, then `uv run --no-project --with torch,transformers,pillow,numpy python -I clip_run.py` and the same for `clip_board.py`.
