# Feeling space experiments

Goal: a space where what a visitor says lands near art (or colors) that *feel* the same, without collapsing onto a few hubs. Today's CLIP text-to-painting matching sends most moods to Munch and Van Gogh.

Every candidate is scored the same way with `metrics.py` on `feelings.json` (40 statements: 20 feelings, each with a paraphrase, plus 12 opposite pairs):

| Metric | Good | What it catches |
|---|---|---|
| `coverage_top1/top3` (unique, entropy, max_share) | many items, entropy near 1, low max_share | a few paintings winning everything |
| `hubness_k5` | near 0 | hub paintings |
| `paraphrase_overlap_at3` | high | same feeling, different words, different picks |
| `paraphrase_vs_random` | well below 1 | paraphrases not landing together |
| `opposite_vs_random` | above 1 | opposites landing together |

Numbers are a screen, not a verdict: the final call is a blind human check on boards.

Candidates (one folder or script each, results added to `HYPOTHESES.md`):
- **A · Repaired CLIP** (`clip_*`): recentering, whitening, text-image gap correction, prompt templates, and a larger painting library.
- **C · ArtEmis** (`artemis_*`): a small head on CLIP trained on people's emotional reactions to WikiArt paintings.
- **D · Color aura** (`aura_*`): feeling to palette, no paintings.

Run the self-test: `python -I metrics.py`
