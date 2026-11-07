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

## Feeling space C: ArtEmis-trained feeling space (2026-11-07)

**Question:** can people's emotional reactions to real paintings (ArtEmis) give a space where a visitor's words land on paintings that *feel* the same, without collapsing onto a few hubs?

**Setup** (`experiments/space/artemis_*.py`, run locally on an M4 Max, MPS, no GPU VM)
- **Data:** ArtEmis v0 (Achlioptas et al. 2021): 454,684 emotion labels and written explanations on 80,031 WikiArt paintings, 9 emotions. Images come from Hugging Face `Artificio/WikiArt` (103K rows), joined on artist and title: 48,534 paintings match. Only the 27 densest parquet row groups were fetched, giving 13,147 paintings and 74,768 explanations (~400 MB cache outside the repo).
- **Encoder:** `laion/CLIP-ViT-H-14-laion2B-s32B-b79K`, both towers, frozen. The image side is the IP-Adapter's encoder, so every pick stays usable as a style reference.
- **Library:** 800 paintings held out of all training. 5 random train/library splits; every number below is the mean ± sd over them.
- **Designs:**
  - **baseline:** today's method, "a painting that feels {text}" cosine vs. painting image embeds.
  - **A-emo:** two linear heads predict the 9-way ArtEmis emotion distribution, one from the image embed and one from an explanation's text embed. A painting scores by Σ p_text(e)·log(q_img(e) / library mean q(e)).
  - **A-emo8:** A-emo with the catch-all "something else" dropped on the text side.
  - **A-emo8-mlp:** A-emo8 with an MLP image head.
  - **A-emo+clip:** A-emo8 z-score + 0.5 × baseline z-score.
  - **A-emo-js:** Jensen–Shannon distance between the two distributions.
  - **A-human / A-human8:** the library painting's own ArtEmis votes in place of the image head.
  - **B-proj:** 1024→256 linear projections trained contrastively on (explanation, painting) pairs plus an emotion side-loss, library centred. **B-proj-emo3** gives the emotion loss a weight of 3.
  - **C-utt:** no image model; the visitor's words vs. the human explanations written for each library painting.
- **New metric, alongside the shared ones:** `emotion_hit_at3` is the share of top-3 picks whose majority ArtEmis emotion is one expected for the feeling (map in `artemis_02_space.py`). Chance is 0.29.

**Results** (40 feelings; library 800 per split; mean ± sd over 5 splits; `out/artemis_results.json`)

| candidate | library | top-1 unique /40 | top-1 max share | top-3 unique /120 | hubness k5 | paraphrase overlap@3 | paraphrase vs random | opposite vs random | emotion hit@3 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 800 | 25.6±3.1 | 0.14±0.04 | 67.0±2.6 | 7.1±1.9 | 0.25±0.05 | 0.79±0.03 | 1.04±0.02 | 0.41±0.04 |
| A-emo | 800 | 30.0±1.3 | 0.10±0.03 | 77.6±3.2 | 4.5±0.5 | 0.23±0.03 | 0.80±0.02 | 1.03±0.00 | 0.48±0.04 |
| A-emo8 | 800 | 30.2±1.8 | 0.10±0.02 | 81.2±2.6 | 3.9±0.2 | 0.27±0.02 | 0.75±0.04 | 1.03±0.00 | 0.50±0.05 |
| A-emo8-mlp | 800 | 32.2±1.9 | 0.09±0.01 | 86.2±3.7 | 3.4±0.2 | 0.25±0.04 | 0.78±0.05 | 1.02±0.01 | 0.48±0.02 |
| A-emo+clip | 800 | 30.2±1.3 | 0.10±0.02 | 75.8±2.2 | 4.2±0.5 | 0.23±0.04 | 0.83±0.04 | 1.02±0.01 | 0.54±0.04 |
| A-emo-js | 800 | 29.8±1.5 | 0.10±0.02 | 76.0±1.9 | 4.0±0.2 | 0.29±0.03 | 0.72±0.02 | 1.04±0.01 | 0.50±0.07 |
| A-human | 800 | 32.2±1.5 | 0.10±0.02 | 84.0±1.1 | 3.4±0.3 | 0.21±0.04 | 0.81±0.03 | 1.02±0.00 | 0.61±0.01 |
| A-human8 | 800 | 33.2±1.2 | 0.10±0.01 | 84.0±3.0 | 3.7±0.3 | 0.23±0.05 | 0.77±0.04 | 1.03±0.00 | 0.74±0.01 |
| B-proj | 800 | 36.8±0.7 | 0.05±0.00 | 100.0±5.0 | 2.9±0.2 | 0.09±0.06 | 0.92±0.04 | 1.00±0.01 | 0.33±0.06 |
| B-proj-emo3 | 800 | 36.0±0.9 | 0.05±0.00 | 99.6±2.4 | 2.7±0.2 | 0.10±0.02 | 0.91±0.02 | 1.01±0.01 | 0.36±0.02 |
| C-utt | 800 | 24.6±2.6 | 0.18±0.07 | 53.2±7.2 | 8.8±1.1 | 0.32±0.07 | 0.76±0.03 | 1.03±0.02 | 0.36±0.04 |

Every design answers one visitor query in under 10 ms on the Mac (CLIP text encode plus scoring 800 paintings), far under the 300 ms budget. Board: `experiments/space/out/artemis_board.png` (12 feelings, top 3, baseline vs. A-emo+clip vs. A-human8, split 0).

**What worked**
- **Routing through ArtEmis emotions cuts collapse.** Compared with the baseline, the A designs have about half the hubness (7.1 to 3.4–4.5), a lower top-1 max share (0.14 to 0.10) and 10–20 more distinct top-3 picks. They also land more often on paintings people felt the right way: emotion hit 0.48–0.54 vs. 0.41 (chance 0.29). Paraphrase consistency stays about the same.
- **Dropping "something else" on the text side helps a little.** A visitor always feels something: hubness 4.5 to 3.9, emotion hit 0.48 to 0.50.
- **Known human votes beat a predicted image emotion.** A-human8 reaches 0.74 emotion hit (partly circular, see caveats). If the library is drawn from ArtEmis's 80K annotated paintings, no image head is needed: the votes are a lookup table.
- **The image head is the weak link and still improving.** Its TV distance to held-out human votes is 0.474, 0.458 and 0.446 at 3K, 6K and 12K training paintings, vs. 0.526 for "always predict the average". All 48K joined paintings would likely help more.

**What didn't**
- **B (contrastive explanation→painting) spreads picks but loses feeling.** It has the best coverage, but paraphrase overlap is 0.09 and emotion hit 0.33, near chance. Explanations mostly describe *what is in* the painting ("the woman looks tired"), so the projection learns subject, not feeling. A stronger emotion loss didn't fix it.
- **C (match against human explanations) collapses as badly as the baseline.** Hubness is 8.8, though it has the best paraphrase overlap (0.32). Long, wordy explanation sets act as hubs.
- **The text head reads some feelings wrong.** ArtEmis rarely uses anger or disgust, so "rage" maps to excitement or fear and "anxious" to excitement or fear. "Wonder" maps to contentment, not awe, and "proud" to contentment or sadness. The 9 ArtEmis emotions are reactions to art, not a visitor's state, so grief vs. lonely or calm vs. grateful are indistinguishable by design.
- **On the board, A-emo+clip still picks by subject** for scene-like feelings (wonder gets snow, as in the baseline). A-human8 picks by feeling but looks noisier.

**Caveats**
- `emotion_hit_at3` uses the same human votes that A-human scores with (the majority label of each library painting). For A-human it measures text-head quality given perfect painting emotions; it is not an independent check. For the other designs it is independent: library paintings are never trained on.
- The feeling→emotion map is a judgment call (e.g. hope → contentment, awe or excitement).
- The library is a random WikiArt sample (Artificio subset), not the lab's 36 famous paintings. Not tested on that library.
- Collapse metrics from an 800-item library aren't directly comparable to the 36-item lab library: hubness skew grows with library size.
- The join between ArtEmis names and WikiArt titles is heuristic (artist slug plus title slug, trailing years stripped, ambiguous titles dropped); some mismatches are possible.
- Not tested: a blind human check on boards, more training data, fine-tuning CLIP, prompt templates on the text side, or a mix with thread A's recentring or thread D's color aura.

**Data and terms:** ArtEmis is distributed through a Google Form that accepts the ArtEmis Terms of Use (non-commercial research and education only; the authors give no warranty). The data was obtained that way by a team member. The ArtEmis CSV, images, embeddings and trained heads stay in a local cache (`~/.cache/living-canvas/artemis`) and are never committed. WikiArt images: `Artificio/WikiArt` on Hugging Face has no stated license, and WikiArt itself allows non-commercial research use only. ArtELingo (the Hugging Face copy) is unusable: its data files now return 404.

**Recommendation:** for the booth, use the emotion route, not a learned joint space:
- Build the painting library from ArtEmis-annotated WikiArt paintings and score with their human emotion votes (A-human8).
- Use A-emo+clip only for paintings outside ArtEmis.
- Keep Gemini (or a small keyword list) for anger, anxiety and pride, which the ArtEmis text head handles poorly.
- Confirm on blind boards before switching.
