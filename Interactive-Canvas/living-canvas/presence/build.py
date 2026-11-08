"""Build the presence library (offline, once): the curated ArtEmis paintings plus the two trained heads.

    uv run --no-project --with torch,transformers,pandas,pyarrow,numpy,pillow python -I presence/build.py \
        --restatements <dir with c4_restatements.json and c4_restatements_emb.pt>

Inputs (all outside git, ArtEmis is non-commercial research only):
  ARTEMIS_CACHE   paintings.parquet, utts.parquet, img_emb.pt, utt_emb.pt, thumbs/ (experiments/space/artemis_01_build.py)
  --restatements  Gemini's visitor-voice restatements of ArtEmis explanations and their CLIP embeddings (the eval
                  board's feeling_lab.py `gemini` step writes both)
  --colorfulness  optional cached colorfulness per painting (.npy); computed from the thumbs otherwise
Writes <library_dir>/presence_library.npz (config.json `library_dir`, or PRESENCE_DIR) and build.json.

Training is the eval board's, step for step and with the same seeds, so the library reproduces its C5/C5b picks:
  - text head: a linear head from the CLIP text embedding onto the 9 emotions (cross-entropy on every ArtEmis
    explanation's label), trained next to a linear image head, as in space C's train_a;
  - feeling space (C4): contrastive explanation <-> painting projections (1024 -> 256), a shared emotion head on both
    towers (w_emo 30, soft labels from the vote distributions), the restatements as extra positives, and an arousal
    input on the text tower.
Library = every cached painting except sketches, illustrations, designs, posters, caricatures, ads and near-monochrome
images (colorfulness under 15). The vote floor and smoothing are applied at query time, from config.json.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from presence.scorer import EMO, LIBRARY_FILE, load_config  # noqa: E402

CACHE = os.environ.get("ARTEMIS_CACHE", os.path.expanduser("~/.cache/living-canvas/artemis"))
DROP_GENRES = {"sketch and study", "illustration", "design", "poster", "caricature", "advertisement", "None"}
COLOR_MIN, K_PRIOR, W_EMO = 15.0, 10.0, 30.0
AROUSAL = {"amusement": .7, "awe": .6, "contentment": .25, "excitement": .85, "anger": .85, "disgust": .6, "fear": .8,
           "sadness": .25, "something else": .5}
torch.set_num_threads(8)                                           # as the eval board ran: same float order


def load():
    P = pd.read_parquet(os.path.join(CACHE, "paintings.parquet"))
    U = pd.read_parquet(os.path.join(CACHE, "utts.parquet"))
    IE = torch.load(os.path.join(CACHE, "img_emb.pt")).float()
    UE = torch.load(os.path.join(CACHE, "utt_emb.pt")).float()
    U["e"] = U.emotion.map({e: i for i, e in enumerate(EMO)})
    D = np.zeros((len(P), len(EMO)), np.float32)
    np.add.at(D, (U.p.values, U.e.values), 1)
    D /= D.sum(1, keepdims=True)
    n = torch.tensor(np.bincount(U.p.values, minlength=len(P)), dtype=torch.float32)[:, None]
    return P, U, IE, UE, torch.tensor(D), n


def colorfulness(path):
    """Hasler & Suesstrunk (2003) colorfulness; under ~15 is close to monochrome."""
    from PIL import Image
    x = np.asarray(Image.open(path).convert("RGB"), float)
    rg, yb = x[..., 0] - x[..., 1], 0.5 * (x[..., 0] + x[..., 1]) - x[..., 2]
    return float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))


def train_text_head(IE, UE, U, D, tr):
    """Space C's train_a: image head (soft labels) and text head (explanation labels), trained together."""
    gi, ht = nn.Linear(1024, 9), nn.Linear(1024, 9)
    tri = torch.tensor(tr)
    um = torch.tensor(np.isin(U.p.values, tr))
    X, Y = UE[um], torch.tensor(U.e.values)[um]
    opt = torch.optim.AdamW(list(gi.parameters()) + list(ht.parameters()), lr=3e-3, weight_decay=1e-4)
    for _ in range(300):
        li = -(D[tri] * F.log_softmax(gi(IE[tri] * 20), -1)).sum(-1).mean()
        b = torch.randint(0, len(X), (4096,))
        lt = F.cross_entropy(ht(X[b] * 20), Y[b])
        opt.zero_grad(); (li + lt).backward(); opt.step()
    return ht


class Space(nn.Module):
    def __init__(self, d=256):
        super().__init__()
        self.t, self.i, self.g = nn.Linear(1024, d), nn.Linear(1024, d), nn.Linear(1024, d)
        nn.init.zeros_(self.g.weight); nn.init.zeros_(self.g.bias)
        self.emo = nn.Linear(d, len(EMO))
        self.ls = nn.Parameter(torch.tensor(math.log(1 / 0.07)))

    def text(self, x, a=None):
        a = torch.full((len(x),), 0.5) if a is None else torch.as_tensor(a, dtype=torch.float32).reshape(-1)
        return F.normalize(self.t(x) + (a[:, None] - 0.5) * self.g(x), dim=-1)

    def img(self, v):
        return F.normalize(self.i(v), dim=-1)


def synth_arousal(labels, rng):
    a = torch.tensor([AROUSAL[EMO[int(k)]] for k in labels]) + torch.tensor(rng.normal(0, .12, len(labels)), dtype=torch.float32)
    a = a.clamp(0, 1)
    a[torch.tensor(rng.random(len(labels)) < 0.5)] = 0.5         # half the time no voice signal: text alone must work
    return a


def train_space(D, n, U, UE, IE, tr, restate, w_emo=W_EMO, steps=2000, seed=0):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    prior = D[tr].mean(0, keepdim=True)
    H = (D * n + K_PRIOR * prior) / (n + K_PRIOR)
    um = np.isin(U.p.values, tr)
    X, Pi, Y = UE[torch.tensor(um)], torch.tensor(U.p.values[um]), torch.tensor(U.e.values[um])
    RE, rp, ry = restate
    keep = torch.tensor(np.isin(rp.numpy(), tr))
    RE, rp, ry = RE[keep], rp[keep], ry[keep]
    m = Space()
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-2)
    for _ in range(steps):
        b = torch.randint(0, len(X), (1024,))
        x, pid, y = X[b], Pi[b], Y[b]
        if len(RE):
            rb = torch.randint(0, len(RE), (256,))
            x, pid, y = torch.cat([x, RE[rb]]), torch.cat([pid, rp[rb]]), torch.cat([y, ry[rb]])
        a = synth_arousal(y, rng)
        uniq, inv = torch.unique(pid, return_inverse=True)
        t, v = m.text(x, a), m.img(IE[uniq])
        nce = F.cross_entropy(m.ls.exp().clamp(max=100) * t @ v.T, inv)
        ce = F.cross_entropy(m.emo(t * 10), y)
        soft = -(H[uniq] * F.log_softmax(m.emo(v * 10), -1)).sum(-1).mean()
        loss = nce + w_emo * (ce + soft)
        opt.zero_grad(); loss.backward(); opt.step()
    return m.eval()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--restatements", required=True)
    ap.add_argument("--colorfulness")
    ap.add_argument("--out", help="library dir (default: config.json library_dir or PRESENCE_DIR)")
    a = ap.parse_args()
    out = a.out or load_config()["library_dir"]
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    P, U, IE, UE, D, n = load()
    cpath = a.colorfulness or os.path.join(out, "colorfulness.npy")
    if os.path.exists(cpath):
        col = np.load(cpath)
    else:
        col = np.array([colorfulness(os.path.join(CACHE, "thumbs", f"{p}.jpg")) for p in P.painting])
        np.save(cpath, col)
    cur = np.where(~P.genre.isin(DROP_GENRES).values & (col >= COLOR_MIN))[0]
    rows = json.load(open(os.path.join(a.restatements, "c4_restatements.json")))
    RE = torch.load(os.path.join(a.restatements, "c4_restatements_emb.pt"))
    assert len(RE) == len(rows), "restatement embeddings do not match the restatements"
    restate = (RE, torch.tensor([r["p"] for r in rows]), torch.tensor([r["e"] for r in rows]))
    allp = np.arange(len(P))
    torch.manual_seed(0)
    ht = train_text_head(IE, UE, U, D, allp)
    print(f"text head trained ({time.time() - t0:.0f}s)", flush=True)
    m = train_space(D, n, U, UE, IE, allp, restate)
    print(f"feeling space trained ({time.time() - t0:.0f}s)", flush=True)
    with torch.no_grad():
        proj = m.img(IE[cur]).numpy().astype(np.float32)
    lab = lambda s: str(s).replace("-", " ").title() if s is not None else ""
    np.savez(os.path.join(out, LIBRARY_FILE),
             names=np.array([str(x) for x in P.painting[cur]]), artist=np.array([lab(x) for x in P.artist[cur]]),
             title=np.array([str(x) for x in P.title[cur]]), genre=np.array([str(x) for x in P.genre[cur]]),
             n=n[cur, 0].numpy().astype(np.int32), D=D[cur].numpy(), prior=D.mean(0).numpy(),
             img_emb=IE[cur].numpy().astype(np.float32), img_proj=proj,
             head_W=ht.weight.detach().numpy(), head_b=ht.bias.detach().numpy(),
             c4_t_W=m.t.weight.detach().numpy(), c4_t_b=m.t.bias.detach().numpy(),
             c4_g_W=m.g.weight.detach().numpy(), c4_g_b=m.g.bias.detach().numpy())
    json.dump({"built": time.strftime("%Y-%m-%dT%H:%M:%S"), "paintings": int(len(cur)), "corpus": int(len(P)),
               "restatements": len(rows), "w_emo": W_EMO, "k_prior_training": K_PRIOR, "color_min": COLOR_MIN,
               "license": "derived from ArtEmis (non-commercial research and education only); do not commit or share"},
              open(os.path.join(out, "build.json"), "w"), indent=1)
    print(f"wrote {out}/{LIBRARY_FILE}: {len(cur)} paintings ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
