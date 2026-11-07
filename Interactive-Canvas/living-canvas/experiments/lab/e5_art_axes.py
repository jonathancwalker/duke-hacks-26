# H3 + H4 rebuilt inside the art space. Axes are directions between groups of real paintings in the
# IP-Adapter's CLIP image space (text directions were too weak in E3/E4).
import numpy as np
CN = dict(cn_scale=0.35, cn_end=0.5)
def A(*names):
    idx = [i for i, n in enumerate(ART_NAMES) if any(n.startswith(x) for x in names)]
    return ART_M[idx].mean(0, keepdim=True)
ART_AXES = {
    "energy":      A("Van Gogh, The Starry", "Turner, Rain", "Hokusai", "Munch", "Kandinsky") - A("Whistler", "Monet, Water", "Friedrich", "Monet, Impression"),
    "temperature": A("Klimt", "Turner, The Fighting", "Van Gogh, Wheatfield", "Seurat") - A("Whistler", "Hokusai", "Monet, Water", "Van Gogh, The Starry"),
    "discord":     A("Munch", "Kandinsky", "Van Gogh, Wheatfield", "Turner, Rain") - A("Monet, Water", "Seurat", "Whistler", "Klimt"),
}
CENTER = ART_M.mean(0, keepdim=True)
def art_point(coefs, k=1.0):
    v = CENTER.clone()
    for name, c in coefs.items(): v = v + k * c * ART_AXES[name]
    return v
IP = 0.85
rows, labels = [], []
for name in ART_AXES:
    rows.append([render2(ip=art_point({name: c}), ip_scale=IP, **CN) for c in (-1, 0, 1)]); labels.append(f"art axis: {name}")
show(board(rows, labels, ["-1", "0", "+1"], title="E5a · H3 in art space: axes = directions between groups of paintings"), "E5a_art_axes")

rows, labels = [], []
for k in ORDER:
    c = persona_coefs(PERSONAS[k]); cc = {"energy": c["energy"], "temperature": c["temperature"]}
    rows.append([render2(ip=art_point(cc), ip_scale=IP, **CN)]); labels.append(f"{k.upper()}: energy {cc['energy']:+.1f}, temperature {cc['temperature']:+.1f}")
united = [{"energy": e, "temperature": t} for e, t in np.random.default_rng(3).normal(0, 0.08, (6, 2))]
divided = [{"energy": -0.9, "temperature": -0.8}] * 3 + [{"energy": 0.9, "temperature": 1.0}] * 3
for name, crowd in (("UNITED crowd", united), ("DIVIDED crowd", divided)):
    m = {a: float(np.mean([p[a] for p in crowd])) for a in ("energy", "temperature")}
    spread = float(np.mean([np.std([p[a] for p in crowd]) for a in ("energy", "temperature")]))
    rows.append([render2(ip=art_point(m), ip_scale=IP, **CN), render2(ip=art_point({**m, "discord": min(1.2, spread * 1.5)}), ip_scale=IP, **CN)])
    labels.append(f"{name}: mean e {m['energy']:+.2f} t {m['temperature']:+.2f} | spread {spread:.2f} -> discord {min(1.2, spread * 1.5):.2f}")
show(board(rows, labels, ["persona / crowd mean only", "crowd mean + discord from spread"],
           title="E5b · personas and crowds on art-space axes"), "E5b_personas_crowds")
