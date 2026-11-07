# Vibe paint round 3c: start from the chapel recolored in the painters' own palette (gradient map), then paint over it.
# With 4 steps, the starting colors mostly survive, so each painter mix keeps its own colors.
ensure_library()
def pick(*ps):
    return {n: w for p, w in ps for n in [next((n for n in ART_NAMES if n.startswith(p)), None)] if n}
CASES = [
    ("grandmother passed", pick(("Tanner", .5), ("Turner", .3), ("Whistler", .2)), .2, -.3, -.8),
    ("won the championship", pick(("Klimt", .5), ("Delacroix", .3), ("Renoir", .2)), .95, .8, .6),
    ("nervous presentation", pick(("Munch", .6), ("Seurat", .4)), .7, -.4, -.2),
    ("calm sunday", pick(("Seurat", .6), ("Monet", .4)), .1, .2, .5),
    ("bored in line", pick(("Caillebotte", .6), ("Seurat", .4)), .15, -.2, 0),
    ("spring break", pick(("Renoir", .6), ("Matisse", .4)), .85, .7, .7),
    ("homesick", pick(("Tanner", .6), ("Caillebotte", .4)), .2, -.1, -.4),
    ("anxious exams", pick(("Munch", .6), ("Van Gogh", .4)), .75, -.3, -.4),
]
def lut(weights):
    """A 256-step gradient through the painters' own colors, dark to light, each painter in proportion to its weight."""
    cols = []
    for n, w in weights.items():
        for h in palette_of(n): cols += [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))] * max(1, round(w * 6))
    cols.sort(key=lambda c: .3 * c[0] + .59 * c[1] + .11 * c[2])
    xs = np.linspace(0, 1, len(cols)); t = np.linspace(0, 1, 256)
    return np.stack([np.interp(t, xs, [c[i] for c in cols]) for i in range(3)], 1).astype(np.uint8)
def gradient_map(img, weights):
    g = np.asarray(img.convert("L"))
    g = ((g - np.percentile(g, 2)) / (np.percentile(g, 98) - np.percentile(g, 2) + 1e-6) * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(lut(weights)[g])
def blobs(weights, seed=3):
    """For the abstract canvas: big soft blobs of the painters' colors."""
    r = np.random.default_rng(seed); L = lut(weights)
    f = sum(np.sin(r.uniform(1, 5) * np.linspace(0, 6.28, W)[None] + r.uniform(0, 6)) * np.cos(r.uniform(1, 4) * np.linspace(0, 6.28, H)[:, None] + r.uniform(0, 6)) for _ in range(5))
    f = ((f - f.min()) / (f.max() - f.min()) * 255).astype(np.uint8)
    return Image.fromarray(L[f])
def point(w, e, wa, li, k=1.0):
    v = mix_vector(w) + k * ((e - .5) * 2 * ART_AXES["energy"] + wa * ART_AXES["temperature"] + li * ART_AXES["value"])
    return v / v.norm() * MEAN_NORM
SCENE = globals().get("_V3C_SCENE") or render2(seed=7, **ART_CN); globals()["_V3C_SCENE"] = SCENE
ABS = E("an abstract expressive painting, gestural brushstrokes and loose color fields, no objects")
rows, labels = [], []
for n, w, *ax in CASES:
    init = gradient_map(SCENE, w)
    rows.append([render2(ip=point(w, *ax), ip_scale=style_only(1.4), seed=7, **ART_CN),
                 init,
                 render2(ip=point(w, *ax, .5), ip_scale=style_only(1.4), init=init, strength=.6, seed=7, cn_scale=.5, cn_end=.8),
                 render2(ip=point(w, *ax, .5), ip_scale=style_only(1.4), init=init, strength=.75, seed=7, cn_scale=.5, cn_end=.8),
                 render2(cond=ABS, ip=point(w, *ax, .5), ip_scale=style_only(1.4), init=blobs(w), strength=.8, seed=7, cn_scale=0.0, cn_end=1.0)])
    labels.append(f"{n}: " + ", ".join(k.split(",")[0] for k in w))
show(board(rows, labels, ["now", "palette start (gradient map)", "painted over, .6", "painted over, .75", "abstract from palette blobs"],
           cell=(384, 216), left=230, title="V3c · start from the painters' own palette"), "V3c_palette_init")
