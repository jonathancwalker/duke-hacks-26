"""Candidate A: can CLIP text->painting matching be repaired so it stops collapsing onto hub paintings?

Scores the current method (lab/00_lib.py art_weights) and each fix on the 40 shared feelings with metrics.report_scores.
Writes out/clip_results.json and out/clip_results.md. Run: uv run --no-project --with torch,transformers,pillow,numpy python -I clip_run.py
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I drops the script dir
import io, json, math, os
import numpy as np
from PIL import Image
from clip_common import (CACHE, OUT, REF_SENTENCES, REF_WORDS, TEMPLATES, cached_image_embeds, embed_texts, load_small_library)
from metrics import load_feelings, report_scores

ENSEMBLE = ["baseline", "evokes", "mood", "emotion", "atmosphere"]


def unit(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)


def cos(a, b):
    return unit(a) @ unit(b).T


# ---------------- text side ----------------
def text_embeds(feelings):
    """{template: (T (40,d), R_words, R_sentences)}, unit length, cached."""
    p = os.path.join(CACHE, "txt.npz")
    texts = [f["text"] for f in feelings]
    key = json.dumps([texts, REF_WORDS, REF_SENTENCES, TEMPLATES])
    if os.path.exists(p):
        z = np.load(p, allow_pickle=True)
        if str(z["key"]) == key:
            return {t: (z[f"T_{t}"], z[f"Rw_{t}"], z[f"Rs_{t}"]) for t in TEMPLATES}
    out = {t: tuple(embed_texts([tpl.format(x) for x in xs]) for xs in (texts, REF_WORDS, REF_SENTENCES))
           for t, tpl in TEMPLATES.items()}
    np.savez(p, key=key, **{f"{k}_{t}": v[j] for t, v in out.items() for j, k in enumerate(("T", "Rw", "Rs"))})
    return out


def ensemble(tx, names):
    return tuple(unit(np.mean([tx[n][j] for n in names], 0)) for j in range(3))


def text_sets(tx):
    """(T, R) pairs scored below. R (reference bank) only matters for the fixes, never for plain cosine."""
    ens = ensemble(tx, ENSEMBLE)
    s = {t: (tx[t][0], tx[t][1]) for t in TEMPLATES}
    s["ensemble"] = (ens[0], ens[1])
    s["baseline/Rsent"] = (tx["baseline"][0], tx["baseline"][2])
    s["ensemble/Rsent"] = (ens[0], ens[2])
    h = len(tx["baseline"][2]) // 2           # robustness: each half of the sentence bank on its own
    s["baseline/Rsent-A"] = (tx["baseline"][0], tx["baseline"][2][:h])
    s["baseline/Rsent-B"] = (tx["baseline"][0], tx["baseline"][2][h:])
    return s


# ---------------- fixes: each maps (T, R, I) -> scores (n_feelings, n_paintings) ----------------
def m_base(T, R, I):
    return cos(T, I)


def m_center_img(T, R, I):
    I = unit(I); return cos(T, I - I.mean(0))


def m_center_both(T, R, I):
    I = unit(I); return cos(T - R.mean(0), I - I.mean(0))


def m_center_both_query(T, R, I):
    """Transductive: text mean from the 40 test statements themselves (a deployed system would need a running mean)."""
    I = unit(I); return cos(T - T.mean(0), I - I.mean(0))


def m_gap(T, R, I):
    """Close the modality gap: move the text cloud's centre onto the image cloud's centre."""
    I = unit(I); return cos(T - R.mean(0) + I.mean(0), I)


def whiten(k, alpha=0.1):
    def f(T, R, I):
        I = unit(I); mu = I.mean(0); Ic = I - mu
        _, s, vt = np.linalg.svd(Ic, full_matrices=False)
        k_ = min(k, len(s) - 1)
        lam = s[:k_] ** 2 / (len(I) - 1)
        W = vt[:k_].T / np.sqrt(lam + alpha * lam.mean())    # shrunk whitening on the library's top-k PCs
        return cos((T - R.mean(0)) @ W, Ic @ W)
    f.__name__ = f"whiten{k}"
    return f


def csls(k=10):
    """Cross-domain similarity local scaling: penalise paintings that are close to every text (hubs)."""
    def f(T, R, I, inner=m_base):
        C, CR = inner(T, R, I), inner(R, R, I)
        r = np.sort(CR, 0)[-k:].mean(0)
        return 2 * C - r[None]
    return f


def zcol(inner):
    """Per-painting z-score of the similarity against the reference emotion bank: a painting must beat its own
    typical similarity to win, so 'similar to everything' stops helping."""
    def f(T, R, I):
        C, CR = inner(T, R, I), inner(R, R, I)
        return (C - CR.mean(0)) / (CR.std(0) + 1e-9)
    return f


def csls_on(inner, k=10):
    def f(T, R, I):
        C, CR = inner(T, R, I), inner(R, R, I)
        return 2 * C - np.sort(CR, 0)[-k:].mean(0)[None]
    return f


# ---------------- extra metrics (kept alongside metrics.py, which is shared and unchanged) ----------------
def extra(scores, names, feelings, k=3, seed=0):
    top1 = np.argsort(-scores, 1)[:, 0]
    counts = np.bincount(top1, minlength=scores.shape[1])
    p = counts[counts > 0] / counts.sum()
    # entropy normalised by the most it could be with 40 picks, so small and large libraries compare
    ent_picks = float(-(p * np.log(p)).sum() / math.log(min(len(feelings), scores.shape[1])))
    # paraphrase lift: paraphrase top-k overlap minus overlap of random non-paraphrase pairs. When everything lands on
    # the same hubs, paraphrases "agree" for free; the lift only counts agreement beyond that.
    top = np.argsort(-scores, 1)[:, :k]
    rng = np.random.default_rng(seed)
    pairs = [tuple(rng.choice(len(feelings), 2, replace=False)) for _ in range(600)]
    pairs = [(a, b) for a, b in pairs if feelings[a]["para"] != feelings[b]["para"]]
    rand_ov = float(np.mean([len(set(top[a]) & set(top[b])) / k for a, b in pairs]))
    hub = names[int(counts.argmax())]
    return {"top1_entropy_vs_picks": round(ent_picks, 3), "rand_overlap_at3": round(rand_ov, 3),
            "top_hub": f"{hub.split(',')[0]} ({int(counts.max())}/40)"}


def rescale(S, ref_row_std):
    """Global rescale (ranking unchanged) so every method's mean within-row spread matches the baseline's.
    metrics.topk_dist uses a fixed temperature, so without this the pair metrics would reward score scale, not picks."""
    return S * (ref_row_std / S.std(1).mean())


def score_one(tag, tname, mname, S, names, feelings, opposites, ref_std):
    S = rescale(S, ref_std)
    r = report_scores(f"{tag} · {tname} · {mname}", S, feelings, opposites)
    r.update(extra(S, names, feelings)); r.update(library=tag, text=tname, method=mname)
    r["para_lift_at3"] = round(r["paraphrase_overlap_at3"] - r["rand_overlap_at3"], 3)
    return r


def score_all(tag, methods, tx_sets, I, names, feelings, opposites, ref_std):
    return [score_one(tag, tname, mname, f(T, R, I), names, feelings, opposites, ref_std)
            for tname, (T, R) in tx_sets.items() for mname, f in methods.items()]


def flat(r):
    c1, c3 = r["coverage_top1"], r["coverage_top3"]
    return (f"| {r['library']} | {r['text']} | {r['method']} | {c1['unique']}/{c1['of']} | {c1['entropy']:.2f} | "
            f"{r['top1_entropy_vs_picks']:.2f} | {c1['max_share']:.2f} | {c3['unique']} | {r['hubness_k5']:.2f} | "
            f"{r['paraphrase_overlap_at3']:.2f} | {r['para_lift_at3']:.2f} | {r['paraphrase_vs_random']:.2f} | "
            f"{r['opposite_vs_random']:.2f} | {r['top_hub']} |")


HEADER = ("| library | text | method | top1 unique | top1 entropy | top1 ent/picks | max share | top3 unique | hubness k5 | "
          "para overlap@3 | para lift@3 | para/rand | opp/rand | biggest hub |\n|" + "---|" * 14)


def large_library(small_names, small_I):
    p = os.path.join(CACHE, "wikiart_subset.json")
    if not os.path.exists(p):
        return None
    sub = json.load(open(p))
    names = [f"{s['artist'].replace('-', ' ').title()}, WikiArt #{s['idx']} ({s['style'].replace('_', ' ')})" for s in sub]
    imgs = []
    for s in sub:
        im = Image.open(s["path"]).convert("RGB"); im.thumbnail((1024, 1024)); imgs.append(im)
    E = cached_image_embeds("wikiart", names, imgs)
    return small_names + names, np.concatenate([small_I, E])


FIXES = {"center_img": m_center_img, "center_both": m_center_both, "center_both_query*": m_center_both_query,
         "gap_shift": m_gap, "whiten8": whiten(8), "whiten16": whiten(16), "whiten32": whiten(32),
         "csls": csls_on(m_base), "zscore": zcol(m_base),
         "center_both+csls": csls_on(m_center_both), "center_both+zscore": zcol(m_center_both),
         "whiten16+zscore": zcol(whiten(16))}
BIG_FIXES = {"cosine": m_base, "center_both": m_center_both, "whiten16": whiten(16), "whiten64": whiten(64),
             "csls": csls_on(m_base), "zscore": zcol(m_base), "center_both+csls": csls_on(m_center_both),
             "center_both+zscore": zcol(m_center_both), "whiten64+zscore": zcol(whiten(64))}
FIX_TEXTS = ("baseline", "ensemble", "baseline/Rsent", "ensemble/Rsent")
ROBUST = {"center_both": m_center_both, "zscore": zcol(m_base), "center_both+zscore": zcol(m_center_both)}
ROBUST_TEXTS = ("baseline/Rsent-A", "baseline/Rsent-B")


def main():
    feelings, opposites = load_feelings()
    names, imgs = load_small_library()
    I = cached_image_embeds("small", names, imgs)
    print(f"{len(names)} paintings embedded, dim {I.shape[1]}")
    tx = text_embeds(feelings)
    sets = text_sets(tx)
    ref_std = cos(tx["baseline"][0], I).std(1).mean()
    rng = np.random.default_rng(0)

    # 0) reference: random scores (what "no collapse, no meaning" looks like)
    rows = [score_one("36", "-", "random (reference)", rng.normal(size=(len(feelings), len(names))), names,
                      feelings, opposites, ref_std)]
    # 1) baseline + prompt templates with the current cosine
    rows += score_all("36", {"cosine": m_base}, {k: v for k, v in sets.items() if "/" not in k}, I, names,
                      feelings, opposites, ref_std)
    # 2) geometric fixes, with each prompt set and each reference bank
    rows += score_all("36", FIXES, {k: sets[k] for k in FIX_TEXTS}, I, names, feelings, opposites, ref_std)
    rows += score_all("36", ROBUST, {k: sets[k] for k in ROBUST_TEXTS}, I, names, feelings, opposites, ref_std)

    # 3) larger library
    big = large_library(names, I)
    if big:
        bn, bI = big
        print(f"large library: {len(bn)} paintings")
        rows.append(score_one(str(len(bn)), "-", "random (reference)", rng.normal(size=(len(feelings), len(bn))),
                              bn, feelings, opposites, ref_std))
        rows += score_all(str(len(bn)), BIG_FIXES, {k: sets[k] for k in FIX_TEXTS}, bI, bn, feelings, opposites,
                          ref_std)
        rows += score_all(str(len(bn)), ROBUST, {k: sets[k] for k in ROBUST_TEXTS}, bI, bn, feelings, opposites,
                          ref_std)

    os.makedirs(OUT, exist_ok=True)
    json.dump(rows, open(os.path.join(OUT, "clip_results.json"), "w"), indent=1)
    md = HEADER + "\n" + "\n".join(flat(r) for r in rows)
    open(os.path.join(OUT, "clip_results.md"), "w").write(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
