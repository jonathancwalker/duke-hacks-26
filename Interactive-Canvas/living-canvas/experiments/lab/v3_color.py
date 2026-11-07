# Vibe paint round 3: why do moods look alike, and what makes them distinct? Plus two blank-canvas starts.
import cv2
from PIL import ImageDraw, ImageFilter
ensure_library()
def pick(*ps):
    out = {}
    for p, w in ps:
        n = next((n for n in ART_NAMES if n.startswith(p)), None)
        if n: out[n] = w
    return out
MOODS = [  # name, painters, energy, warmth, light, color words (what Gemini would add)
    ("grief",   pick(("Tanner", .6), ("Cassatt", .4)), .2, -.3, -.8, "deep indigo, slate grey and muted umber"),
    ("triumph", pick(("Delacroix, Liberty", .45), ("Kandinsky", .35), ("Matisse", .2)), .95, .8, .6, "blazing gold, vermilion red and bright cobalt"),
    ("nervous", pick(("Kandinsky", .5), ("Van Gogh, The Starry", .3), ("Whistler", .2)), .7, -.4, -.2, "acid green, electric blue and sickly yellow"),
    ("calm",    pick(("Monet, Water", .6), ("Hiroshige", .4)), .1, 0, .4, "soft lavender, sage green and pearl white"),
    ("fury",    pick(("Goya", .5), ("Munch", .3), ("Gericault", .2)), .95, .6, -.7, "blood red, black and burnt orange"),
    ("love",    pick(("Renoir", .5), ("Klimt", .3), ("Cassatt", .2)), .5, .7, .5, "rose pink, warm peach and gold leaf"),
]
def cond(extra, scene=True):
    base = STYLE if scene else "an abstract expressive painting, gestural brushstrokes and loose color fields, no objects"
    return E(f"{base}, painted in {extra}") if extra else (S_PE, S_PP) if scene else E(base)
def lab_of(img):
    return cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2LAB).astype(np.float32)
def palette_match(img, weights, amount=0.8):
    """Per-channel histogram match in LAB toward the chosen paintings' own pixels (weighted)."""
    src = lab_of(img); tgt = []
    for n, w in weights.items():
        px = lab_of(ART[n].resize((96, 96))).reshape(-1, 3); tgt.append(px[np.random.default_rng(0).choice(len(px), int(4000 * w))])
    tgt = np.concatenate(tgt); out = src.copy()
    for c in range(3):
        s = src[..., c].ravel(); order = np.argsort(s); q = np.empty_like(s)
        q[order] = np.quantile(tgt[:, c], np.linspace(0, 1, len(s)))
        out[..., c] = q.reshape(src.shape[:2])
    out = src + amount * (out - src)
    return Image.fromarray(cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB))
def frame(w, e, wa, li, words=None, scene=True):
    v = mix_vector(w)
    v = v + (e - .5) * 2 * ART_AXES["energy"] + wa * ART_AXES["temperature"] + li * ART_AXES["value"]
    v = v / v.norm() * MEAN_NORM
    kw = ART_CN if scene else dict(cn_scale=0.0, cn_end=1.0)
    return render2(cond=cond(words, scene), ip=v, ip_scale=style_only(1.4), seed=7, **kw)
rows, labels, F = [], [], {}
for n, w, e, wa, li, words in MOODS:
    a = frame(w, e, wa, li); b = frame(w, e, wa, li, words); c = palette_match(a, w); d = palette_match(b, w, .6)
    ab = frame(w, e, wa, li, words, scene=False)
    F[n] = (d, palette_match(ab, w, .6))
    rows.append([a, b, c, d, F[n][1]]); labels.append(f"{n}: " + ", ".join(k.split(",")[0] for k in w))
show(board(rows, labels, ["now", "+ color words", "+ palette match", "words + match .6", "abstract (no chapel)"],
           cell=(384, 216), left=230, title="V3 · making moods distinct"), "V3_color")
# Blank canvas: six visitors' paths on primed linen, scene mode and abstract mode
def path(seed):
    r = np.random.default_rng(seed); t = np.linspace(0, 1, 90); a, b, ph = r.uniform(.6, 1.6), r.uniform(.6, 1.6), r.uniform(0, 6)
    cx, cy = r.uniform(.3, .7), r.uniform(.3, .7)
    return [(W * (cx + .3 * np.sin(a * 6.28 * x + ph)), H * (cy + .3 * np.sin(b * 6.28 * x))) for x in t]
LINEN = Image.new("RGB", (W, H), (233, 226, 211))
for mode in (0, 1):
    canvas = LINEN.copy(); steps = []
    for i, (n, *_r) in enumerate(MOODS):
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).line(path(i + 3), fill=235, width=46, joint="curve")
        canvas = Image.composite(F[n][mode], canvas, m.filter(ImageFilter.GaussianBlur(4)))
        if i in (0, 2, 5): steps.append(canvas.copy())
    show(board([steps], ["after 1 → 3 → 6 visitors"], ["", "", ""], cell=(512, 288), left=170,
               title=f"V3 · blank canvas, {'chapel revealed' if mode == 0 else 'abstract'}"), f"V3_blank_{['scene', 'abstract'][mode]}")
