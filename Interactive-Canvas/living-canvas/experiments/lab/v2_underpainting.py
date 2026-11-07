# Vibe paint round 2: calm pale underpainting, then three moods along three paths.
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
base = base_frame()
moods = [("grief", {"Tanner, The Banjo Lesson (1893)": 0.6, "Cassatt, The Child's Bath (1893)": 0.4}, 0.2, -0.3, -0.8),
         ("triumph", {"Delacroix, Liberty Leading the People (1830)": 0.45, "Kandinsky, Composition VII (1913)": 0.35, "Matisse, Woman with a Hat (1905)": 0.2}, 0.95, 0.8, 0.6),
         ("nervous", {"Kandinsky, Composition VII (1913)": 0.5, "Van Gogh, The Starry Night (1889)": 0.3, "Whistler, Nocturne in Black and Gold (1875)": 0.2}, 0.7, -0.4, -0.2)]
def path(seed):
    r = np.random.default_rng(seed); t = np.linspace(0, 1, 90); a, b, ph = r.uniform(1, 2.5), r.uniform(1, 2.5), r.uniform(0, 6)
    return [(W * (0.5 + 0.38 * np.sin(a * 6.28 * x + ph)), H * (0.5 + 0.36 * np.sin(b * 6.28 * x))) for x in t]
canvas = base.copy(); steps = [base]
for i, (n, w, e, wa, li) in enumerate(moods):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).line(path(i), fill=245, width=40, joint="curve")
    canvas = Image.composite(vibe_frame(w, e, wa, li), canvas, m.filter(ImageFilter.GaussianBlur(5))); steps.append(canvas.copy())
show(board([steps[:2], steps[2:]], ["start → after grief", "after triumph → after nervous"], ["", ""], cell=(640, 360), left=170,
           title="V2 · calm underpainting, three visitors' paths"), "V2_underpainting")
