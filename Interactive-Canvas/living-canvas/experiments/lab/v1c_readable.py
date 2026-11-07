# Vibe paint round 1: do vibe frames line up with the base, and does a path-masked change read as a painted gesture?
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
ensure_library()
base = base_frame()
moods = {
    "grief (Tanner + Cassatt)": ({"Tanner, The Banjo Lesson (1893)": 0.6, "Cassatt, The Child's Bath (1893)": 0.4}, 0.2),
    "triumph (Delacroix + Kandinsky + Matisse)": ({"Delacroix, Liberty Leading the People (1830)": 0.45, "Kandinsky, Composition VII (1913)": 0.35,
                                                   "Matisse, Woman with a Hat (1905)": 0.2}, 0.95),
    "nervous (Kandinsky + Van Gogh + Whistler)": ({"Kandinsky, Composition VII (1913)": 0.5, "Van Gogh, The Starry Night (1889)": 0.3,
                                                    "Whistler, Nocturne in Black and Gold (1875)": 0.2}, 0.7),
}

MOOD_AXES = {"grief": dict(energy=0.2, temperature=-0.3, value=-0.8), "triumph": dict(energy=0.95, temperature=0.8, value=0.6),
             "nervous": dict(energy=0.7, temperature=-0.4, value=-0.2)}
def vf2(w, ax, style=1.4, k=1.0):
    v = mix_vector(w)
    for name, c in ax.items():
        v = v + k * (c if name != "energy" else (c - 0.5) * 2) * ART_AXES[name]
    v = v / v.norm() * MEAN_NORM
    return render2(ip=v, ip_scale=style_only(style), seed=7, **ART_CN)
def path_pts(seed):
    r = np.random.default_rng(seed); t = np.linspace(0, 1, 90); a, b, ph = r.uniform(1, 2.5), r.uniform(1, 2.5), r.uniform(0, 6)
    return [(W * (0.5 + 0.38 * np.sin(a * 6.28 * x + ph)), H * (0.5 + 0.36 * np.sin(b * 6.28 * x))) for x in t]
def stroke_mask(pts, width, blur):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).line(pts, fill=245, width=width, joint="curve")
    return m.filter(ImageFilter.GaussianBlur(blur))
def rim(pts, width):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.line(pts, fill=255, width=width + 6, joint="curve"); d.line(pts, fill=0, width=width - 2, joint="curve")
    return m.filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.35))
variants = [("soft mask, mix only (before)", False, 46, 9, False), ("mix + warmth/light/energy axes, soft mask", True, 46, 9, False),
            ("axes + firmer stroke + wet rim", True, 38, 3, True)]
rows, labels = [], []
names = list(MOOD_AXES)
for vname, use_axes, width, blur, use_rim in variants:
    canvas = base.copy()
    for i, (mname, (w, e)) in enumerate(moods.items()):
        frame = vf2(w, MOOD_AXES[names[i]]) if use_axes else vibe_frame(w, e)
        pts = path_pts(i)
        canvas = Image.composite(frame, canvas, stroke_mask(pts, width, blur))
        if use_rim:
            dark = Image.blend(canvas, Image.new("RGB", (W, H), (30, 24, 20)), 0.55)
            canvas = Image.composite(dark, canvas, rim(pts, width))
    rows.append([canvas]); labels.append(vname)
show(board(rows, labels, ["painting after 3 visitors: grief, triumph, nervous"], cell=(896, 504), left=200,
           title="V1c · making each visitor's path readable"), "V1c_readable")
