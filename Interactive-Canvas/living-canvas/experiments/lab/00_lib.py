# Shared by every experiment. Runs inside the lab server, where render(), E(), clip_text(), ART_*, board(), show() exist.
import colorsys
import numpy as np
import torch
from PIL import Image

# ---------- personas: stand-ins for real mic + webcam + Claude until those are wired ----------
# laban: weight (-1 light .. +1 strong), time (-1 sustained .. +1 sudden),
#        space (-1 indirect .. +1 direct), flow (-1 bound .. +1 free)
# temperament: what Claude-as-art-director would write. Formal language, never scene content.
PERSONAS = {
    "grief": dict(words="Missing my grandma tonight.", voice="whisper",
                  temperament="hushed, slow, inward, soft dissolving edges, cool muted blue-grey, sparse and quiet",
                  arousal=0.15, valence=-0.6, laban=dict(weight=-0.7, time=-0.8, space=-0.6, flow=0.6)),
    "joy": dict(words="Everyone I love is in this room right now!", voice="laughing",
                temperament="bright, buoyant, warm saturated color, quick broken dabs, open airy light",
                arousal=0.8, valence=0.9, laban=dict(weight=-0.6, time=0.7, space=-0.5, flow=0.8)),
    "anxiety": dict(words="I am so stressed about the job market.", voice="tight, fast",
                    temperament="agitated, jagged, heavy impasto, harsh contrast, clashing hot and cold color, tense diagonals",
                    arousal=0.9, valence=-0.7, laban=dict(weight=0.8, time=0.9, space=0.7, flow=-0.8)),
    "resolve": dict(words="I want to build something that matters.", voice="steady, low",
                    temperament="steady, luminous, deliberate long strokes, deep warm and cool harmony, monumental calm",
                    arousal=0.5, valence=0.5, laban=dict(weight=0.7, time=-0.6, space=0.8, flow=-0.2)),
}
ORDER = ["grief", "joy", "anxiety", "resolve"]

# ---------- H1: art-history space ----------
def art_weights(text, k=3, temp=0.02):
    """Nearest artworks to a temperament in CLIP space, with softmax weights over the top k."""
    t = clip_text([f"a painting that feels {text}"])
    sims = (ART_MN @ t.T).squeeze(1)
    top = torch.topk(sims, min(k, len(ART_NAMES)))
    w = torch.softmax(top.values / temp, 0)
    return [(ART_NAMES[i], float(s), float(wi)) for i, s, wi in zip(top.indices.tolist(), top.values.tolist(), w.tolist())]

def art_vec(weights):
    """Blend artworks' IP-Adapter embeddings by weight: a point that stays inside the space of real art."""
    v = sum(wi * ART_M[ART_NAMES.index(n)] for n, _, wi in weights)
    return v[None]

def fmt_weights(ws):
    return "; ".join(f"{n.split(',')[0]} {n.split('(')[-1].rstrip(')')} {w:.0%}" for n, _, w in ws)

# ---------- H2: gesture traces ----------
def gesture(p, seed=0, n=260):
    """Synthetic hand path (canvas px) shaped by Laban effort. Stand-in for webcam fingertip tracking."""
    L = p["laban"]; rng = np.random.default_rng(seed)
    x, y, ang = W * rng.uniform(.25, .75), H * rng.uniform(.3, .65), rng.uniform(0, 2 * np.pi)
    speed = 2.5 + 5 * (L["time"] + 1) / 2 + 2.5 * (L["weight"] + 1) / 2
    pts = []
    for _ in range(n):
        if L["time"] > 0 and rng.random() < 0.07 * (L["time"] + 0.2):
            ang += rng.normal(0, 2.0)                                  # sudden: jerks
        ang += rng.normal(0, 0.32 * (1 - L["space"]) / 2 + 0.02)       # indirect: wandering
        x += np.cos(ang) * speed; y += np.sin(ang) * speed
        if not 20 < x < W - 20: ang = np.pi - ang; x = float(np.clip(x, 20, W - 20))
        if not 20 < y < H - 20: ang = -ang; y = float(np.clip(y, 20, H - 20))
        pts.append((x, y))
    return np.array(pts)

def trace_colors(p, k, rng):
    """Palette from temperament: valence -> cool..warm hue, arousal -> saturation; negative + aroused -> clashing hues."""
    v, a = p["valence"], p["arousal"]
    hue = (220 - (v + 1) / 2 * 190) % 360
    clash = 150 * a if v < 0 and a > 0.6 else 0
    cols = []
    for _ in range(k):
        h = (hue + rng.normal(0, 18) + (clash if rng.random() < 0.4 else 0)) % 360
        s = float(np.clip(0.25 + 0.65 * a + rng.normal(0, .08), 0, 1))
        val = float(np.clip(0.5 + 0.35 * (v + 1) / 2 + rng.normal(0, .08), 0, 1))
        cols.append(tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h / 360, s, val)))
    return cols

def paint_trace(canvas, p, seed=0, bristles=7):
    """Draw a person's gesture as a multi-bristle brush stroke onto a copy of canvas. This is their trace."""
    L = p["laban"]; rng = np.random.default_rng(seed + 100)
    img = np.array(canvas.convert("RGB")).astype(np.float32)
    path = gesture(p, seed)
    width = 3 + 10 * (L["weight"] + 1) / 2
    for col in trace_colors(p, bristles, rng):
        ov = img.copy()
        off = rng.normal(0, width * 0.9, size=2)
        jit = rng.normal(0, 1.0 + 3.0 * (L["flow"] + 1) / 2, size=path.shape)
        pts = (path + off + jit).astype(np.int32)
        cv2.polylines(ov, [pts], False, col, thickness=max(1, int(width * rng.uniform(.4, 1.1))), lineType=cv2.LINE_AA)
        img = img * 0.4 + ov * 0.6
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))

# ---------- H3: form axes (concept-slider directions in the conditioning space) ----------
AXES = {
    "energy": (["calm still brushwork", "slow smooth unhurried strokes", "tranquil quiet paint surface"],
               ["agitated swirling brushstrokes", "restless energetic slashing marks", "turbulent vibrating paint surface"]),
    "temperature": (["cool palette of blues, greens and violets", "icy cold color harmony", "cool silvery light"],
                    ["warm palette of reds, oranges and golds", "hot glowing color harmony", "warm golden light"]),
    "edges": (["soft blurred edges, forms dissolving into each other", "hazy sfumato transitions", "melting soft contours"],
              ["hard sharp edges, crisp graphic contours", "bold outlines and clean shapes", "precise hard-edged forms"]),
    "density": (["sparse airy composition, thin translucent washes", "delicate light touch, much empty space", "thin glazes, minimal marks"],
                ["dense heavy impasto, thick layered paint", "crowded richly worked surface", "heavy loaded brush, thick paint"]),
    "abstraction": (["precise realistic detailed rendering", "faithful naturalistic depiction", "careful representational detail"],
                    ["abstract expressive color fields, forms breaking apart", "nonrepresentational gestures and shapes", "dissolving into pure abstraction"]),
}
TENSION = (["harmonious unified palette, gentle transitions, balanced calm composition"],
           ["clashing complementary colors, fractured broken forms, discordant composition"])

_AX_CACHE = globals().setdefault("_AX_CACHE", {})
def axis_dir(name):
    """Mean(pos paraphrases) - mean(neg paraphrases): a direction that changes form, not subject."""
    if name not in _AX_CACHE:
        neg, pos = TENSION if name == "tension" else AXES[name]
        P = [E(f"{STYLE}, {t}") for t in pos]; N = [E(f"{STYLE}, {t}") for t in neg]
        _AX_CACHE[name] = (torch.stack([q[0] for q in P]).mean(0) - torch.stack([q[0] for q in N]).mean(0),
                           torch.stack([q[1] for q in P]).mean(0) - torch.stack([q[1] for q in N]).mean(0))
    return _AX_CACHE[name]

def form_cond(coefs, scale=0.5):
    """STYLE + sum(c_i * axis_i): coefs like {'energy': 0.8, 'temperature': -0.5}."""
    pe, pp = S_PE.clone(), S_PP.clone()
    for k, c in coefs.items():
        dpe, dpp = axis_dir(k); pe = pe + scale * c * dpe; pp = pp + scale * c * dpp
    return pe, pp

def persona_coefs(p):
    """Map voice + movement features to form axes (hand-set for round 1; learnable later)."""
    L, a, v = p["laban"], p["arousal"], p["valence"]
    return {"energy": float(np.clip(0.6 * (2 * a - 1) + 0.6 * L["time"], -1, 1)),
            "temperature": float(np.clip(v, -1, 1)),
            "edges": float(np.clip(-0.6 * L["flow"] + 0.5 * L["space"], -1, 1)),
            "density": float(np.clip(L["weight"], -1, 1)),
            "abstraction": float(np.clip(1.2 * a - 0.5, -1, 1))}

def fmt_coefs(c):
    return ", ".join(f"{k[:4]} {v:+.1f}" for k, v in c.items())

# ---------- render with structure-lock timing (added after D1: Canny at full strength overrides style) ----------
def render2(cond=None, ip=None, ip_scale=0.0, push=0.0, neg=None, control=None, cn_scale=0.3, cn_end=1.0,
            init=None, strength=0.5, seed=7):
    """Like render(), plus cn_end: stop the structure lock after this fraction of steps (layout early, style late)."""
    pe, pp = cond if cond is not None else (S_PE, S_PP)
    cfg = push > 1
    xl.set_ip_adapter_scale(ip_scale if ip is not None else 0.0)
    kw = dict(prompt_embeds=pe, pooled_prompt_embeds=pp,
              ip_adapter_image_embeds=ip_embeds(ip if ip is not None else ZERO_IP, cfg),
              controlnet_conditioning_scale=cn_scale, control_guidance_end=cn_end,
              num_inference_steps=4, generator=gen(seed))
    if cfg:
        npe, npp = neg if neg is not None else (S_PE, S_PP)
        kw.update(guidance_scale=push, negative_prompt_embeds=npe, negative_pooled_prompt_embeds=npp)
    else:
        kw.update(guidance_scale=0.0)
    ctrl = control if control is not None else EDGES
    if init is None:
        return xl(image=ctrl, width=W, height=H, **kw).images[0]
    return xl_i2i(image=init, control_image=ctrl, strength=strength, **kw).images[0]

SPARSE_EDGES = globals().get("SPARSE_EDGES") or edges_of(opening.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(3)), 60, 140)
