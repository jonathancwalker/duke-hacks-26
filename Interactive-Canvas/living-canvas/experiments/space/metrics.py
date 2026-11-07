"""Collapse metrics for a feeling space, shared by every candidate (repaired CLIP, ArtEmis, color aura).

A candidate supplies one of:
  - scores: (n_feelings, n_items) similarity of each feeling to each library item (painting, style...), or
  - outputs + distance: one output per feeling (vector, palette...) and a distance function between outputs.
Run `python -I metrics.py` for a self-test on random data.
"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load_feelings():
    with open(os.path.join(HERE, "feelings.json")) as f:
        d = json.load(f)
    return d["feelings"], d["opposites"]


def _pairs(feelings, opposites):
    idx = {f["id"]: i for i, f in enumerate(feelings)}
    groups = {}
    for i, f in enumerate(feelings):
        groups.setdefault(f["para"], []).append(i)
    para = [(g[a], g[b]) for g in groups.values() for a in range(len(g)) for b in range(a + 1, len(g))]
    opp = [(idx[a], idx[b]) for a, b in opposites]
    return para, opp


def coverage(scores, k=1):
    """How spread the picks are. unique: distinct items in anyone's top-k; entropy: 0 (one item wins everything) .. 1 (even)."""
    top = np.argsort(-scores, axis=1)[:, :k].ravel()
    counts = np.bincount(top, minlength=scores.shape[1])
    p = counts[counts > 0] / counts.sum()
    ent = float(-(p * np.log(p)).sum() / math.log(scores.shape[1]))
    return {"unique": int((counts > 0).sum()), "of": int(scores.shape[1]), "entropy": round(ent, 3),
            "max_share": round(float(counts.max() / counts.sum()), 3)}


def hubness(scores, k=5):
    """Skewness of how often each item appears in someone's top-k. ~0 is healthy; large positive = a few hubs."""
    top = np.argsort(-scores, axis=1)[:, :k].ravel()
    c = np.bincount(top, minlength=scores.shape[1]).astype(float)
    sd = c.std()
    return round(float(((c - c.mean()) ** 3).mean() / sd ** 3) if sd > 0 else 0.0, 3)


def topk_dist(scores, temp=0.05, k=5):
    """Each feeling as a soft distribution over its top-k items, for comparing feelings."""
    out = np.zeros_like(scores, dtype=float)
    for i, row in enumerate(scores):
        t = np.argsort(-row)[:k]
        w = np.exp((row[t] - row[t].max()) / temp)
        out[i, t] = w / w.sum()
    return out


def pair_metrics(outputs, distance, feelings, opposites, seed=0):
    """Separation and consistency on any outputs. Reports distances relative to random pairs (1.0 = random)."""
    para, opp = _pairs(feelings, opposites)
    n = len(outputs)
    rng = np.random.default_rng(seed)
    rand = [tuple(rng.choice(n, 2, replace=False)) for _ in range(400)]
    d = lambda ps: float(np.mean([distance(outputs[a], outputs[b]) for a, b in ps]))
    base = d(rand) or 1e-9
    return {"paraphrase_vs_random": round(d(para) / base, 3),   # lower is better (paraphrases together)
            "opposite_vs_random": round(d(opp) / base, 3)}      # higher is better (opposites apart)


def overlap_at_k(scores, feelings, k=3):
    """Share of top-k items paraphrase pairs have in common (1 = identical picks)."""
    para, _ = _pairs(feelings, [])
    top = np.argsort(-scores, axis=1)[:, :k]
    return round(float(np.mean([len(set(top[a]) & set(top[b])) / k for a, b in para])), 3)


def report_scores(name, scores, feelings=None, opposites=None):
    """Full report for a candidate that scores feelings against a library."""
    if feelings is None:
        feelings, opposites = load_feelings()
    dist = topk_dist(scores)
    js = lambda p, q: float(0.5 * (np.abs(p - q)).sum())  # total variation distance between pick distributions
    r = {"candidate": name, "coverage_top1": coverage(scores, 1), "coverage_top3": coverage(scores, 3),
         "hubness_k5": hubness(scores, 5), "paraphrase_overlap_at3": overlap_at_k(scores, feelings, 3)}
    r.update(pair_metrics(dist, js, feelings, opposites))
    return r


def report_outputs(name, outputs, distance, feelings=None, opposites=None):
    """Report for a candidate whose output is not a pick from a library (e.g. a color palette)."""
    if feelings is None:
        feelings, opposites = load_feelings()
    r = {"candidate": name}
    r.update(pair_metrics(outputs, distance, feelings, opposites))
    return r


if __name__ == "__main__":
    fs, opp = load_feelings()
    rng = np.random.default_rng(1)
    rand = rng.normal(size=(len(fs), 36))
    hub = rand.copy(); hub[:, 0] += 3  # one painting wins everything
    print(json.dumps(report_scores("random", rand, fs, opp)))
    print(json.dumps(report_scores("collapsed", hub, fs, opp)))
    pal = [rng.uniform(size=(5, 3)) for _ in fs]
    print(json.dumps(report_outputs("random palettes", pal, lambda a, b: float(np.abs(a - b).mean()), fs, opp)))
