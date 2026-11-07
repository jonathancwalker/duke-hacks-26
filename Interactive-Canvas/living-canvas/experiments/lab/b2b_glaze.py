# Brush round 2: does a light glaze lift human strokes or erase them? Synthetic strokes on a blank primed canvas.
import base64, io
import numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(4)
CW, CH = 1600, 900
base = np.full((CH, CW, 3), (236, 230, 216), np.uint8)
base = (base + rng.normal(0, 4, base.shape)).clip(0, 255).astype(np.uint8)           # primed linen grain
canvas = base.copy(); mask = np.zeros((CH, CW), np.uint8)
pal = [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in palette_of("Van Gogh, The Starry Night (1889)")[:4]]
for s in range(5):                                                                   # five curvy hand-like strokes
    t = np.linspace(0, 1, 120); a, b, ph = rng.uniform(1, 3), rng.uniform(1, 3), rng.uniform(0, 6)
    pts = np.stack([CW * (0.2 + 0.6 * (0.5 + 0.45 * np.sin(a * t * 6 + ph))), CH * (0.2 + 0.6 * (0.5 + 0.45 * np.sin(b * t * 6)))], 1).astype(np.int32)
    col = pal[s % len(pal)][::-1]
    for k in range(6):                                                               # bristles
        off = rng.normal(0, 6, 2).astype(np.int32)
        cv2.polylines(canvas, [pts + off], False, tuple(int(c) for c in col), int(rng.integers(4, 12)), cv2.LINE_AA)
    cv2.polylines(mask, [pts], False, 255, 40, cv2.LINE_AA)
canvas_rgb = Image.fromarray(canvas[:, :, ::-1].copy())
b = io.BytesIO(); canvas_rgb.save(b, "JPEG", quality=90); b64 = base64.b64encode(b.getvalue()).decode()
m = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(14))
weights = {"Van Gogh, The Starry Night (1889)": 0.6, "Monet, Water Lilies (1906)": 0.4}
rows, labels = [], []
for cn in (0.45, 0.7):
    row = [canvas_rgb]
    for s in (0.65, 0.8):
        img = canvas_rgb.resize((W, H))
        g = render2(cond=globals().get("_GLAZE_COND") or E(GLAZE_PROMPT), ip=mix_vector(weights), ip_scale=style_only(1.1), init=img,
                    strength=s, control=edges_of(img, 40, 120), cn_scale=cn, cn_end=1.0, seed=11).resize((CW, CH))
        row.append(Image.composite(g, canvas_rgb, m.point(lambda v: int(v * 0.75))))
    rows.append(row); labels.append(f"outline lock {cn}")
show(board(rows, labels, ["human strokes", "strength 0.65", "strength 0.8"], cell=(480, 270), left=160,
           title="B2b · stronger glaze, composited only where painted"), "B2b_glaze")
