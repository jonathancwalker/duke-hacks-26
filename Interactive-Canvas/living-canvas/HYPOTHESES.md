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
