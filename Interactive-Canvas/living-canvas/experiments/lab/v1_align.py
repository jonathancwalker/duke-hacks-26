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
rows, labels = [], []
canvas = base.copy()
for i, (name, (w, e)) in enumerate(moods.items()):
    vf = vibe_frame(w, e)
    m = path_mask(i)
    canvas = Image.composite(vf, canvas, m)                 # changes accumulate, visitor after visitor
    rows.append([vf, m.convert("RGB"), canvas.copy()]); labels.append(f"visitor {i + 1}: {name}")
show(board([[base, None, base]] + rows, ["starting painting"] + labels, ["vibe frame (full)", "hand-path mask", "painting after"],
           cell=(448, 252), left=240, title="V1 · vibe paint: the painting changes only along each visitor's path"), "V1_align")
