# Round 4b · the plain mix diluted strong visitors (a blend of paintings sits near the library center).
# Fixes: SHARPEN = push the mix away from the center; HYBRID = mix picks the paintings, axes add intensity.
# Run with: lab.py lab/r4b_sharpen.py --data lab/r4_readings.json
import torch

AX3 = ("energy", "temperature", "value")
K_SHARP, K_HYB_MIX, K_HYB_AXES = 1.75, 1.5, 0.6


def norm(v):
    return v / v.norm() * MEAN_NORM


def raw_mix(mix):
    return sum(w * ART_M[ART_NAMES.index(n)] for n, w in mix.items())[None]


def axes_offset(a):
    return sum(a[k] * ART_AXES[k] for k in AX3)


SCHEMES = {
    "axes": lambda r: norm(CENTER + axes_offset(r["axes"])),
    "mix": lambda r: norm(raw_mix(r["mix"])),
    f"mix sharpened x{K_SHARP}": lambda r: norm(CENTER + K_SHARP * (raw_mix(r["mix"]) - CENTER)),
    "hybrid (mix + axes)": lambda r: norm(CENTER + K_HYB_MIX * (raw_mix(r["mix"]) - CENTER) + K_HYB_AXES * axes_offset(r["axes"])),
}


def spread(vs):
    M = torch.cat(vs).float(); M = M / M.norm(dim=-1, keepdim=True); n = len(vs)
    return float((1 - M @ M.T).sum() / (n * (n - 1)))


def dist_from_center(vs):
    c = CENTER.float() / CENTER.norm()
    return sum(float(1 - (v.float() / v.norm()) @ c.T) for v in vs) / len(vs)


rows, labels = [], []
cond = {s: [] for s in SCHEMES}; outs = {s: [] for s in SCHEMES}
for r in DATA:
    row = []
    for s, fn in SCHEMES.items():
        v = fn(r); f = render2(ip=v, ip_scale=style_only(BOOTH_STYLE), **ART_CN)
        cond[s].append(v); outs[s].append(clip_image(f)); row.append(f)
    rows.append(row)
    top = ", ".join(f"{n.split(',')[0]} {w:.0%}" for n, w in list(r["mix"].items())[:2])
    labels.append(f"{r['key'].upper()} (voice {r['arousal']:.2f}) || mix {top}")

print(f"{'scheme':26s} input spread  distance from library center  output spread")
for s in SCHEMES:
    print(f"{s:26s} {spread(cond[s]):.3f}         {dist_from_center(cond[s]):.3f}                        {spread(outs[s]):.3f}")
show(board(rows, labels, list(SCHEMES), cell=(384, 216), left=200,
           title="R4b · axes vs mix vs sharpened mix vs hybrid"), "R4b_sharpen")
