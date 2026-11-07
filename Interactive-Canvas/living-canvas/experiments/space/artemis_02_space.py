"""ArtEmis thread · step 2: train small feeling spaces on ArtEmis, score them against the baseline on a held-out library.

Designs (all on frozen CLIP ViT-H embeddings from artemis_01_build.py):
  baseline   "a painting that feels {text}" cosine vs painting image embeds (art_weights in experiments/lab/00_lib.py)
  A-emo      text head and image head both predict the 9-way ArtEmis emotion distribution; a painting scores by
             sum_e p_text(e) * log(q_img(e) / mean_library q(e))  (how much more than average it carries that emotion)
  A-emo+clip A-emo z-score plus 0.5 * baseline z-score, so the emotion picks the region and CLIP breaks ties
  B-proj     linear projections (1024 -> 256) for text and image, trained contrastively on (explanation, painting)
             pairs with an emotion side-loss; cosine in the projected space, library centred
  C-utt      no image model at query time: the visitor's words vs. the human explanations written for each library
             painting (text-to-text); a painting scores by the mean of its top-2 explanation similarities
Library = paintings held out of all training (their ArtEmis labels are used only for scoring emotion_hit_at3).
Run: uv run --no-project --with torch --with transformers --with pandas --with pyarrow --with numpy python -I artemis_02_space.py
"""
import json, os, sys, time
import numpy as np, pandas as pd, torch, torch.nn as nn, torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import artemis_clip as C
import metrics

CACHE = os.environ.get("ARTEMIS_CACHE", os.path.expanduser("~/.cache/living-canvas/artemis"))
N_LIB = int(os.environ.get("N_LIB", 800))
EMO = ["amusement", "awe", "contentment", "excitement", "anger", "disgust", "fear", "sadness", "something else"]
# Expected ArtEmis emotions per feeling, for the emotion_hit_at3 sanity metric (added alongside the shared metrics).
EXPECT = {"grief": {"sadness"}, "triumph": {"excitement", "awe"}, "calm": {"contentment"}, "rage": {"anger"},
          "anxious": {"fear"}, "love": {"contentment", "excitement"}, "lonely": {"sadness"},
          "hope": {"contentment", "awe", "excitement"}, "homesick": {"sadness", "contentment"}, "wonder": {"awe"},
          "exhausted": {"sadness"}, "excited": {"excitement", "amusement"}, "grateful": {"contentment", "awe"},
          "fear": {"fear"}, "nostalgia": {"contentment", "sadness"}, "playful": {"amusement", "excitement"},
          "neutral": {"something else", "contentment"}, "spring": {"contentment", "excitement"},
          "betrayed": {"anger", "sadness", "disgust"}, "proud": {"excitement", "awe", "contentment"}}
torch.manual_seed(0)


def load():
    P = pd.read_parquet(os.path.join(CACHE, "paintings.parquet"))
    U = pd.read_parquet(os.path.join(CACHE, "utts.parquet"))
    IE = torch.load(os.path.join(CACHE, "img_emb.pt")).float()
    UE = torch.load(os.path.join(CACHE, "utt_emb.pt")).float()
    U["e"] = U.emotion.map({e: i for i, e in enumerate(EMO)})
    D = np.zeros((len(P), len(EMO)), np.float32)
    np.add.at(D, (U.p.values, U.e.values), 1)
    D /= D.sum(1, keepdims=True)
    return P, U, IE, UE, torch.tensor(D)


def train_a(IE, UE, U, D, tr, mlp=False):
    """Two heads onto the 9 ArtEmis emotions (image head linear, or a one-hidden-layer MLP)."""
    gi = nn.Sequential(nn.Linear(1024, 512), nn.GELU(), nn.Dropout(0.3), nn.Linear(512, 9)) if mlp else nn.Linear(1024, 9)
    ht = nn.Linear(1024, 9)
    tri = torch.tensor(tr)
    um = torch.tensor(np.isin(U.p.values, tr))
    X, Y = UE[um], torch.tensor(U.e.values)[um]
    opt = torch.optim.AdamW(list(gi.parameters()) + list(ht.parameters()), lr=3e-3, weight_decay=1e-4)
    for ep in range(300):
        li = -(D[tri] * F.log_softmax(gi(IE[tri] * 20), -1)).sum(-1).mean()  # x20 ~ undo unit-norm scale
        b = torch.randint(0, len(X), (4096,))
        lt = F.cross_entropy(ht(X[b] * 20), Y[b])
        opt.zero_grad(); (li + lt).backward(); opt.step()
    gi.eval()
    return lambda v: F.softmax(gi(v * 20), -1), lambda t: F.softmax(ht(t * 20), -1)


def train_b(IE, UE, U, tr, dim=256, steps=1500, w_emo=0.5):
    """Contrastive linear projections on (explanation, painting) pairs, plus an emotion side-loss on the text side."""
    Wt, Wi, emo = nn.Linear(1024, dim, bias=False), nn.Linear(1024, dim, bias=False), nn.Linear(dim, 9)
    logit_scale = nn.Parameter(torch.tensor(np.log(1 / 0.07), dtype=torch.float32))
    um = np.isin(U.p.values, tr)
    X, Pidx, Y = UE[torch.tensor(um)], torch.tensor(U.p.values[um]), torch.tensor(U.e.values[um])
    params = list(Wt.parameters()) + list(Wi.parameters()) + list(emo.parameters()) + [logit_scale]
    opt = torch.optim.AdamW(params, lr=1e-3, weight_decay=1e-2)
    for s in range(steps):
        b = torch.randint(0, len(X), (1024,))
        pid = Pidx[b]
        uniq, inv = torch.unique(pid, return_inverse=True)
        t = F.normalize(Wt(X[b]), dim=-1); v = F.normalize(Wi(IE[uniq]), dim=-1)
        logits = logit_scale.exp().clamp(max=100) * t @ v.T          # text -> its painting among the batch's paintings
        loss = F.cross_entropy(logits, inv) + w_emo * F.cross_entropy(emo(t * 10), Y[b])
        opt.zero_grad(); loss.backward(); opt.step()
    return lambda t: F.normalize(Wt(t), dim=-1), lambda v: F.normalize(Wi(v), dim=-1)


def emotion_hit(scores, D_lib, feelings, k=3):
    top = np.argsort(-scores, axis=1)[:, :k]
    major = [EMO[i] for i in D_lib.argmax(1)]
    return round(float(np.mean([np.mean([major[j] in EXPECT[f["para"]] for j in top[i]]) for i, f in enumerate(feelings)])), 3)


def z(x):
    return (x - x.mean(1, keepdims=True)) / (x.std(1, keepdims=True) + 1e-9)


def run(P, U, IE, UE, D, seed, feelings, opposites, T_raw, T_base, verbose=False):
    """Train every design on one train/library split and score it. Returns rows, scores and extras."""
    torch.manual_seed(seed)
    perm = np.random.default_rng(seed).permutation(len(P))
    lib, tr = np.sort(perm[:N_LIB]), np.sort(perm[N_LIB:])
    L = IE[lib]
    gi, ht = train_a(IE, UE, U, D, tr)
    gm, _ = train_a(IE, UE, U, D, tr, mlp=True)
    pt, pi = train_b(IE, UE, U, tr)
    pt2, pi2 = train_b(IE, UE, U, tr, w_emo=3.0)
    ex = {}
    if verbose:  # learning curve for the image head (TV distance to held-out human distributions; lower is better)
        ex["image_head_curve"] = {}
        for frac in (0.25, 0.5, 1.0):
            g_, _ = train_a(IE, UE, U, D, tr[: int(len(tr) * frac)])
            with torch.no_grad():
                ex["image_head_curve"][int(len(tr) * frac)] = round(float(0.5 * (g_(IE[lib]) - D[lib]).abs().sum(1).mean()), 3)

    with torch.no_grad():
        S = {}
        S["baseline"] = (T_base @ L.T).numpy()
        q = gi(L); p = ht(T_raw); qm = gm(L)
        ex["tv_linear"] = float(0.5 * (q - D[lib]).abs().sum(1).mean())
        ex["tv_mlp"] = float(0.5 * (qm - D[lib]).abs().sum(1).mean())
        ex["tv_prior"] = float(0.5 * (D[tr].mean(0) - D[lib]).abs().sum(1).mean())
        pmi = lambda dist: (dist.log() - dist.mean(0, keepdim=True).log()).T
        S["A-emo"] = (p @ pmi(q)).numpy()
        # a visitor always feels something: drop ArtEmis's catch-all class on the text side and renormalise
        p8 = p.clone(); p8[:, EMO.index("something else")] = 0; p8 = p8 / p8.sum(1, keepdim=True)
        S["A-emo8"] = (p8 @ pmi(q)).numpy()
        S["A-emo8-mlp"] = (p8 @ pmi(qm)).numpy()
        S["A-emo+clip"] = z(S["A-emo8"]) + 0.5 * z(S["baseline"])
        S["A-emo-js"] = -np.array([[0.5 * (F.kl_div(((pp + qq) / 2).log(), pp, reduction="sum") + F.kl_div(((pp + qq) / 2).log(), qq, reduction="sum")).item()
                                    for qq in q] for pp in p8])
        # upper bound for the emotion route: the library's own human votes instead of the image head
        H = (D[lib] * 6 + 0.5) / (6 + 4.5)                              # light smoothing (~6 votes per painting)
        S["A-human"] = (p @ pmi(H)).numpy()
        S["A-human8"] = (p8 @ pmi(H)).numpy()
        ex["text_head_argmax"] = {f["id"]: EMO[i] for f, i in zip(feelings, p8.argmax(1).tolist())}
        Lp = pi(L); Lp = F.normalize(Lp - Lp.mean(0, keepdim=True), dim=-1)
        S["B-proj"] = (pt(T_raw) @ Lp.T).numpy()
        Lp2 = pi2(L); Lp2 = F.normalize(Lp2 - Lp2.mean(0, keepdim=True), dim=-1)
        S["B-proj-emo3"] = (pt2(T_raw) @ Lp2.T).numpy()
        # C: text-to-text against the library paintings' own explanations
        um = np.isin(U.p.values, lib)
        Ul, ULE = U[um].reset_index(drop=True), UE[torch.tensor(um)]
        col = Ul.p.map({p_: i for i, p_ in enumerate(lib)}).values
        sim = (T_raw @ ULE.T).numpy()
        Sc = np.full((len(feelings), len(lib)), -1.0)
        for j in range(len(lib)):
            Sc[:, j] = np.sort(sim[:, col == j], axis=1)[:, -2:].mean(1)
        S["C-utt"] = Sc

        if verbose:  # latency of one visitor query on this Mac (text encode + head + library scoring), median of 20
            def lat(fn):
                ts = []
                for _ in range(20):
                    t0 = time.time(); fn(); ts.append(time.time() - t0)
                return round(1000 * float(np.median(ts)), 1)
            Lq, s_ = pmi(q), "I am so angry I could scream."
            ex["latency_ms"] = {"baseline": lat(lambda: C.text([f"a painting that feels {s_}"]) @ L.T),
                                "A-emo": lat(lambda: ht(C.text([s_])) @ Lq),
                                "B-proj": lat(lambda: pt(C.text([s_])) @ Lp.T),
                                "C-utt": lat(lambda: C.text([s_]) @ ULE.T)}

    D_lib = D[lib].numpy()
    rows = []
    for name, sc in S.items():
        r = metrics.report_scores(name, sc, feelings, opposites)
        r["library"] = len(lib)
        r["emotion_hit_at3"] = emotion_hit(sc, D_lib, feelings)
        rows.append(r)
    ex["emotion_hit_chance"] = float(np.mean([np.mean([EMO[i] in EXPECT[f["para"]] for i in D_lib.argmax(1)]) for f in feelings]))
    ex["picks"] = {name: {f["id"]: [P.painting[lib[j]] for j in np.argsort(-sc[i])[:3]] for i, f in enumerate(feelings)}
                   for name, sc in S.items()}
    return rows, ex


FLAT = {"top1_unique": lambda r: r["coverage_top1"]["unique"], "top1_max_share": lambda r: r["coverage_top1"]["max_share"],
        "top3_unique": lambda r: r["coverage_top3"]["unique"], "top3_entropy": lambda r: r["coverage_top3"]["entropy"],
        "hubness_k5": lambda r: r["hubness_k5"], "paraphrase_overlap_at3": lambda r: r["paraphrase_overlap_at3"],
        "paraphrase_vs_random": lambda r: r["paraphrase_vs_random"], "opposite_vs_random": lambda r: r["opposite_vs_random"],
        "emotion_hit_at3": lambda r: r["emotion_hit_at3"]}


def main():
    P, U, IE, UE, D = load()
    feelings, opposites = metrics.load_feelings()
    texts = [f["text"] for f in feelings]
    T_raw = C.text(texts)
    T_base = C.text([f"a painting that feels {t}" for t in texts])
    seeds = range(int(os.environ.get("N_SEEDS", 5)))
    print(f"{len(P)} paintings ({len(P) - N_LIB} train, {N_LIB} library per split), {len(U)} explanations, {len(seeds)} splits")
    all_rows, ex0, chance = {}, None, []
    for sd in seeds:
        rows, ex = run(P, U, IE, UE, D, sd, feelings, opposites, T_raw, T_base, verbose=(sd == 0))
        ex0 = ex0 or ex
        chance.append(ex["emotion_hit_chance"])
        for r in rows:
            all_rows.setdefault(r["candidate"], []).append(r)
        print(f"split {sd} done", flush=True)
    summary = {name: {k: [round(float(np.mean([f(r) for r in rs])), 3), round(float(np.std([f(r) for r in rs])), 3)] for k, f in FLAT.items()}
               for name, rs in all_rows.items()}
    out = {"summary_mean_sd": summary, "rows_by_split": all_rows, "emotion_hit_chance": round(float(np.mean(chance)), 3),
           "n_paintings": len(P), "n_library": N_LIB, "n_train": len(P) - N_LIB, "n_explanations": len(U), "n_splits": len(seeds),
           **{k: v for k, v in ex0.items() if k != "picks"}, "picks_split0": ex0["picks"]}
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with open(os.path.join(HERE, "out", "artemis_results.json"), "w") as f:
        json.dump(out, f, indent=1)
    m = lambda name, k, d=2: f"{summary[name][k][0]:.{d}f}±{summary[name][k][1]:.{d}f}"
    print(f"\nmean±sd over {len(seeds)} splits; library {N_LIB} paintings each, held out of training")
    print("| candidate | library | top-1 unique /40 | top-1 max share | top-3 unique /120 | hubness k5 | paraphrase overlap@3 | paraphrase vs random | opposite vs random | emotion hit@3 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for name in summary:
        print(f"| {name} | {N_LIB} | {m(name, 'top1_unique', 1)} | {m(name, 'top1_max_share')} | {m(name, 'top3_unique', 1)} | {m(name, 'hubness_k5', 1)} | "
              f"{m(name, 'paraphrase_overlap_at3')} | {m(name, 'paraphrase_vs_random')} | {m(name, 'opposite_vs_random')} | {m(name, 'emotion_hit_at3')} |")
    print("emotion_hit chance", out["emotion_hit_chance"], "| latency ms", ex0["latency_ms"], "| image head curve", ex0["image_head_curve"],
          "| TV linear/mlp/prior", round(ex0["tv_linear"], 3), round(ex0["tv_mlp"], 3), round(ex0["tv_prior"], 3))
    print("text head (8-way) argmax:", ex0["text_head_argmax"])


if __name__ == "__main__":
    main()
