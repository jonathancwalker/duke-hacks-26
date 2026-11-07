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

def vf3(w, ax, scale):
    v = mix_vector(w)
    for name, c in ax.items():
        v = v + (c if name != "energy" else (c - 0.5) * 2) * ART_AXES[name]
    v = v / v.norm() * MEAN_NORM
    return render2(ip=v, ip_scale=scale, seed=7, **ART_CN)
modes = [("style-only 1.4 (now)", style_only(1.4)), ("style 1.4 + layout 0.4", {"up": {"block_0": [0.0, 1.4, 0.0]}, "down": {"block_2": [0.0, 0.4]}}),
         ("full 0.7", 0.7), ("full 0.85", 0.85)]
ws = list(moods.values())
rows, labels = [], []
for mname, sc in modes:
    rows.append([vf3(ws[0][0], MOOD_AXES["grief"], sc), vf3(ws[1][0], MOOD_AXES["triumph"], sc), vf3(ws[2][0], MOOD_AXES["nervous"], sc)])
    labels.append(mname)
show(board([[base, None, None]] + rows, ["base"] + labels, ["grief (dark, cool)", "triumph (warm, bright)", "nervous"], cell=(400, 225), left=180,
           title="V1d · which injection carries mood tone, not just brushwork?"), "V1d_modes")
