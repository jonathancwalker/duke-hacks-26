# Brush experiment (lab side): a bigger artist library, each artist's palette + brush style, and a light masked glaze.
# Runs inside the lab after 00-02. Heavy work is cached in globals, so re-running per request is cheap.
import base64, io, time, urllib.parse, urllib.request
import numpy as np
import torch
from PIL import Image

# ---- 18 more public-domain paintings (Commons filenames found by search, not guessed) ----
EXTRA_ART = {
    "Bruegel, The Hunters in the Snow (1565)": "Pieter Bruegel the Elder - Hunters in the Snow (Winter) - Google Art Project.jpg",
    "Caravaggio, The Calling of Saint Matthew (1600)": "Caravaggio — The Calling of Saint Matthew.jpg",
    "Vermeer, The Milkmaid (1658)": "Johannes Vermeer - Het melkmeisje - Google Art Project.jpg",
    "Renoir, Dance at Le Moulin de la Galette (1876)": "Auguste Renoir - Dance at Le Moulin de la Galette - Google Art Project.jpg",
    "Sargent, Carnation, Lily, Lily, Rose (1886)": "John Singer Sargent - Carnation, Lily, Lily, Rose - Google Art Project.jpg",
    "Tanner, The Banjo Lesson (1893)": "Henry Ossawa Tanner - The Banjo Lesson.jpg",
    "Cassatt, The Child's Bath (1893)": "Mary Cassatt - The Child's Bath - Google Art Project.jpg",
    "Gauguin, Vision after the Sermon (1888)": "Paul Gauguin - Vision of the Sermon (Jacob Wrestling with the Angel) - NG 1643 - National Galleries of Scotland.jpg",
    "Matisse, Woman with a Hat (1905)": "Matisse-Woman-with-a-Hat.jpg",
    "Marc, The Large Blue Horses (1911)": "Franz Marc - Die großen blauen Pferde 1911.jpg",
    "Klee, Senecio (1922)": "Paul Klee, 1922, Senecio, oil on gauze, 40.3 × 37.4 cm, Kunstmuseum Basel.jpg",
    "Homer, The Gulf Stream (1899)": "Winslow Homer - The Gulf Stream - Metropolitan Museum of Art.jpg",
    "Caillebotte, Paris Street; Rainy Day (1877)": "Gustave Caillebotte - Paris Street; Rainy Day - Google Art Project.jpg",
    "Hiroshige, Sudden Shower over Shin-Ohashi (1857)": "Hiroshige, Sudden shower over Shin-Ōhashi bridge and Atake, 1857.jpg",
    "Fan Kuan, Travelers Among Mountains and Streams (c.1000)": "Fan Kuan - Travelers Among Mountains and Streams - Google Art Project.jpg",
    "Monet, Rouen Cathedral in Sunlight (1894)": "Claude Monet - Rouen Cathedral, West Façade, Sunlight - Google Art Project.jpg",
    "Turner, Snow Storm (1842)": "Joseph Mallord William Turner - Snow Storm - Steam-Boat off a Harbour's Mouth - WGA23178.jpg",
    "Mondrian, Composition II in Red, Blue and Yellow (1930)": "Piet Mondriaan, 1930 - Mondrian Composition II in Red, Blue, and Yellow.jpg",
}


def ensure_library():
    """Download any missing EXTRA_ART into ART / ART_V and rebuild the library matrices. Idempotent."""
    global ART_NAMES, ART_M, ART_MN
    added = 0
    for name, f in EXTRA_ART.items():
        if name in ART_V:
            continue
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(f) + "?width=1024"
        data = None
        for attempt in range(4):
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read(); break
            except Exception as e:
                print(f"  retry {name}: {e}"); time.sleep(6 * (attempt + 1))
        if data is None:
            print("SKIPPED", name); continue
        img = Image.open(io.BytesIO(data)).convert("RGB"); img.thumbnail((1024, 1024))
        ART[name], ART_V[name] = img, clip_image(img); added += 1
        time.sleep(2.5)
    if added or len(ART_NAMES) != len(ART_V):
        ART_NAMES = list(ART_V)
        ART_M = torch.cat([ART_V[n] for n in ART_NAMES]); ART_MN = ART_M / ART_M.norm(dim=-1, keepdim=True)
    return added


# ---- brush style per artist (what a stroke "in their manner" looks like on the booth canvas) ----
BRUSH_BY_PREFIX = [
    ("Van Gogh", "impasto"), ("Delacroix", "impasto"),
    ("Monet", "dab"), ("Renoir", "dab"), ("Sargent", "dab"), ("Cassatt", "dab"), ("Bruegel", "dab"),
    ("Whistler", "wash"), ("Turner", "wash"), ("Friedrich", "wash"), ("Munch", "wash"), ("Homer", "wash"), ("Caillebotte", "wash"),
    ("Hokusai", "ink"), ("Hiroshige", "ink"), ("Fan Kuan", "ink"), ("Kandinsky", "ink"),
    ("Seurat", "stipple"),
    ("Gauguin", "flat"), ("Matisse", "flat"), ("Marc", "flat"), ("Klee", "flat"), ("Mondrian", "flat"),
    ("Rembrandt", "glaze"), ("Caravaggio", "glaze"), ("Vermeer", "glaze"), ("Goya", "glaze"), ("Gericault", "glaze"), ("Tanner", "glaze"),
    ("Klimt", "gold"),
]


def brush_for(name):
    return next((b for p, b in BRUSH_BY_PREFIX if name.startswith(p)), "dab")


_PALETTES = globals().setdefault("_PALETTES", {})


def palette_of(name, k=6):
    """The painting's own colors: k-means over its pixels, most common first (hex)."""
    if name not in _PALETTES:
        px = np.asarray(ART[name].resize((96, 96))).reshape(-1, 3).astype(np.float32)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
        _, labels, centers = cv2.kmeans(px, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
        counts = np.bincount(labels.flatten(), minlength=k)
        order = np.argsort(-counts)
        _PALETTES[name] = ["#%02x%02x%02x" % tuple(int(c) for c in centers[i]) for i in order]
    return _PALETTES[name]


def artist_catalog():
    return [{"name": n, "brush": brush_for(n), "palette": palette_of(n)} for n in ART_NAMES]


# ---- light glaze: restyle the visitor's strokes in their artists' manner, keeping the strokes' shapes ----
GLAZE_PROMPT = "expressive oil paint brushstrokes on a primed linen canvas, visible paint texture"


def mix_vector(weights):
    v = sum(float(w) * ART_M[ART_NAMES.index(n)] for n, w in weights.items() if n in ART_NAMES)
    v = v[None] if v.dim() == 1 else v
    return v / v.norm() * MEAN_NORM


def glaze(canvas_jpg_b64, weights, strength=0.42, style=1.1, seed=11):
    """Returns the AI-restyled canvas (768x432). The booth composites it back only where this visitor painted."""
    img = Image.open(io.BytesIO(base64.b64decode(canvas_jpg_b64))).convert("RGB").resize((W, H))
    if "_GLAZE_COND" not in globals():
        globals()["_GLAZE_COND"] = E(GLAZE_PROMPT)
    return render2(cond=_GLAZE_COND, ip=mix_vector(weights), ip_scale=style_only(style), init=img, strength=strength,
                   control=edges_of(img, 40, 120), cn_scale=0.6, cn_end=1.0, seed=seed)
