# Round 4 · painting mix vs axes. DATA = readings from mix_readings.py (run with: lab.py lab/r4_mix.py --data lab/r4_readings.json)
# Same render settings for both (style-only 1.2, early outline lock, fixed seed). Measures how distinct visitors come out.
import torch

AX3 = ("energy", "temperature", "value")


def mix_vec(mix):
    v = sum(w * ART_M[ART_NAMES.index(n)] for n, w in mix.items())[None]
    return v / v.norm() * MEAN_NORM


def axes_vec(a):
    return art_point({k: a[k] for k in AX3})


def unit(vs):
    M = torch.cat(vs).float()
    return M / M.norm(dim=-1, keepdim=True)


def spread(vs):
    """Mean pairwise cosine distance: 0 = all identical, higher = visitors more distinct."""
    M = unit(vs); n = len(vs)
    return float((1 - M @ M.T).sum() / (n * (n - 1)))


def pair_dist(vs, i, j):
    M = unit(vs)
    return float(1 - M[i] @ M[j])


rows, labels = [], []
cond, out_emb, out_near = {"axes": [], "mix": []}, {"axes": [], "mix": []}, {"axes": [], "mix": []}
for r in DATA:
    va, vm = axes_vec(r["axes"]), mix_vec(r["mix"])
    fa = render2(ip=va, ip_scale=style_only(BOOTH_STYLE), **ART_CN)
    fm = render2(ip=vm, ip_scale=style_only(BOOTH_STYLE), **ART_CN)
    for k, v, f in (("axes", va, fa), ("mix", vm, fm)):
        cond[k].append(v); e = clip_image(f); out_emb[k].append(e)
        out_near[k].append(nearest_art(e, 1)[0])
    rows.append([fa, fm])
    mix_txt = ", ".join(f"{n.split(',')[0]} {n.split(', ')[1].split(' (')[0]} {w:.0%}" for n, w in r["mix"].items())
    labels.append(f"{r['key'].upper()}: \"{r['words']}\" (voice {r['arousal']:.2f}) || axes e{r['axes']['energy']:+.1f} "
                  f"t{r['axes']['temperature']:+.1f} v{r['axes']['value']:+.1f} || mix: {mix_txt}")

n = len(DATA)
keys = [r["key"] for r in DATA]
i_still, i_anim = keys.index("neutral, still"), keys.index("neutral, animated")
print("metric                                   axes    mix")
print(f"conditioning spread (input points)      {spread(cond['axes']):.3f}  {spread(cond['mix']):.3f}")
print(f"output spread (CLIP of rendered frames)  {spread(out_emb['axes']):.3f}  {spread(out_emb['mix']):.3f}")
print(f"same words, still vs animated (output)   {pair_dist(out_emb['axes'], i_still, i_anim):.3f}  {pair_dist(out_emb['mix'], i_still, i_anim):.3f}")
print(f"distinct nearest paintings of outputs    {len(set(out_near['axes']))}/{n}     {len(set(out_near['mix']))}/{n}")
print("nearest painting of each output (axes | mix):")
for k, a, m in zip(keys, out_near["axes"], out_near["mix"]):
    print(f"  {k:18s} {a.split(' (')[0]:38s} | {m.split(' (')[0]}")
show(board(rows, labels, ["AXES (energy, warmth, light)", "MIX (weighted blend of chosen paintings)"], cell=(512, 288), left=260,
           title="R4 · same visitor, two ways of placing them in art space"), "R4_mix_vs_axes")
