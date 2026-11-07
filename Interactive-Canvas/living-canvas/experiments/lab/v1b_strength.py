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
rng = np.random.default_rng(2)
def path_mask(seed):
    r = np.random.default_rng(seed); m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    t = np.linspace(0, 1, 90); a, b, ph = r.uniform(1, 2.5), r.uniform(1, 2.5), r.uniform(0, 6)
    pts = [(W * (0.5 + 0.38 * np.sin(a * 6.28 * x + ph)), H * (0.5 + 0.36 * np.sin(b * 6.28 * x))) for x in t]
    d.line(pts, fill=200, width=46, joint="curve")
    return m.filter(ImageFilter.GaussianBlur(9))

def vf(w, e, style, energy_k):
    v = mix_vector(w); v = v + (float(e) - 0.5) * energy_k * ART_AXES["energy"]; v = v / v.norm() * MEAN_NORM
    return render2(ip=v, ip_scale=style_only(style) if style < 5 else style - 5, seed=7, **ART_CN)
settings = [("style-only 1.2, energy 0.8 (now)", 1.2, 0.8), ("style-only 1.7, energy 1.4", 1.7, 1.4), ("style-only 2.2, energy 1.8", 2.2, 1.8)]
rows, labels = [], []
for sname, st, ek in settings:
    canvas = base.copy(); row = []
    for i, (name, (w, e)) in enumerate(moods.items()):
        canvas = Image.composite(vf(w, e, st, ek), canvas, path_mask(i).point(lambda v: min(255, int(v * 1.25))))
    rows.append([canvas]); labels.append(sname)
show(board(rows, labels, ["painting after 3 visitors (grief, triumph, nervous paths)"], cell=(896, 504), left=200,
           title="V1b · how strongly should a visitor's mood show inside their path?"), "V1b_strength")
