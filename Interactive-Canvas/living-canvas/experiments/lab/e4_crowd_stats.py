CN = dict(cn_scale=0.35, cn_end=0.5)   # early-only structure lock (from D2/D3)
# H4 · Crowd as a distribution. Two crowds with the SAME mean on the form axes:
#   united  = 6 people near the mean;  divided = 3 calm/cool + 3 agitated/warm.
# Mean-only rendering looks identical by construction; adding tension = spread should separate them.
import numpy as np
rng = np.random.default_rng(3)
mean = {"energy": 0.0, "temperature": 0.1, "edges": 0.0, "density": 0.1, "abstraction": 0.0}
united = [{k: v + rng.normal(0, 0.08) for k, v in mean.items()} for _ in range(6)]
divided = ([{**mean, "energy": -0.9, "temperature": -0.8} for _ in range(3)] +
           [{**mean, "energy": 0.9, "temperature": 1.0} for _ in range(3)])

def stats(crowd):
    m = {k: float(np.mean([c[k] for c in crowd])) for k in mean}
    spread = float(np.mean([np.std([c[k] for c in crowd]) for k in mean]))
    return m, spread

rows, labels = [], []
for name, crowd in (("UNITED", united), ("DIVIDED", divided)):
    m, s = stats(crowd)
    tension = float(np.clip(s * 2.5, 0, 1.5))
    rows.append([render2(cond=form_cond(m), push=3.0, **CN),
                 render2(cond=form_cond({**m, "tension": tension}), push=3.0, **CN)])
    labels.append(f"{name}: mean {fmt_coefs(m)} | spread {s:.2f} -> tension {tension:.2f}")
    print(labels[-1])
show(board(rows, labels, ["mean only", "mean + tension from spread"],
           title="E4 · H4 same mean, different spread"), "E4_crowd_stats")
