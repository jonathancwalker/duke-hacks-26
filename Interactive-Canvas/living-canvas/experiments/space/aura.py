"""Feeling space D: color aura. What a visitor says -> a 5-color palette plus brightness and saturation, no paintings.

Mappings compared (all scored with metrics.report_outputs on feelings.json, palette distance = matched CIEDE2000):
  a_affect_clip    valence/arousal/dominance from CLIP text similarity to anchor phrases -> color rule
  a_affect_gemini  valence/arousal/dominance rated by Gemini -> the same color rule
  b_clip_swatch    CLIP text vs 580 solid color swatch images, swatch bias removed, 5 diverse picks
  c_gemini         Gemini returns 5 hex colors directly (response schema)

Color rule (Valdez & Mehrabian 1994): brightness tracks pleasure (and falls a little with dominance), saturation
tracks arousal. Hue comes from the angle on the valence-arousal circle: pleasant+aroused = yellow-orange, unpleasant
+aroused = red, unpleasant+calm = blue-violet, pleasant+calm = green-teal (a design choice, not from V&M).

Run on a Mac, no GPU needed:
  uv run --no-project --python 3.12 --with torch --with open_clip_torch --with scipy --with pillow \
      --with google-genai python -I aura.py            # add --no-gemini to skip Vertex calls
Gemini answers are cached in out/aura_gemini_cache.json, so reruns are free and reproducible.
"""
import argparse, json, math, os, re, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import metrics
from aura_color import (lch_to_rgb, rgb_to_hex, rgb_to_lab, hex_to_rgb, palette_lab, palette_distance,
                        within_palette_spread, brightness_saturation, ciede2000, in_gamut, lab_to_rgb_unclipped)

OUT = os.path.join(HERE, "out")
CACHE = os.path.expanduser("~/.cache/living-canvas-aura")
CLIP_ID = "hf-hub:laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
GEMINI_MODEL = os.environ.get("AURA_GEMINI_MODEL", "gemini-3.8-flash")
GCP_PROJECT = os.environ.get("AURA_GCP_PROJECT", "hackathon-514014")

# Anchor phrases for each affect axis (positive pole, negative pole). Not taken from feelings.json.
ANCHORS = {
    "valence": (["I feel happy.", "This is wonderful.", "I am delighted.", "I feel joyful and good."],
                ["I feel sad.", "This is awful.", "I am miserable.", "I feel hurt and bad."]),
    "arousal": (["I feel excited and wired.", "I'm frantic.", "My heart is racing.", "I'm wide awake and energized."],
                ["I feel calm and sleepy.", "I'm relaxed and slow.", "I feel drowsy.", "I'm tranquil and still."]),
    "dominance": (["I feel in control.", "I am powerful.", "I'm confident and strong.", "I'm in charge."],
                  ["I feel helpless.", "I'm powerless.", "I feel small and weak.", "Things are out of my control."]),
}

# Generic things people say, used only to calibrate scales and to remove swatch bias. Not the test set.
CALIBRATION = [
    "I had coffee this morning.", "The bus was late again.", "I love this city.", "My dog is sick.",
    "We're going to the beach tomorrow.", "I can't find my keys.", "This place is beautiful.",
    "I failed my driving test.", "My sister just had a baby.", "Work has been really boring lately.",
    "I'm hungry.", "It's raining outside.", "I got a new job!", "My phone is broken.",
    "I'm meeting friends later.", "The traffic was terrible.", "I just moved here from Ohio.",
    "I'm worried about my mom.", "This is my first time here.", "I can't stop laughing.",
    "The food here is great.", "I'm bored.", "I'm stressed about money.", "We got engaged last week!",
    "My cat knocked over a plant.", "I'm not sure how I feel.", "It's my birthday today.",
    "I miss my old friends.", "The music is too loud.", "I just ran a marathon.",
]


# ---------- shared color rule: VAD in [-1, 1] -> palette ----------

# (angle on the valence-arousal circle in degrees, LCh hue in degrees)
_HUE_ANCHORS = [(45, 75), (135, 25), (225, -80), (315, -190), (405, -285)]   # unwrapped so interpolation is monotone


def _hue_for(v, a):
    ang = math.degrees(math.atan2(a, v)) % 360
    if ang < 45:
        ang += 360
    for (x0, h0), (x1, h1) in zip(_HUE_ANCHORS, _HUE_ANCHORS[1:]):
        if x0 <= ang <= x1:
            return (h0 + (h1 - h0) * (ang - x0) / (x1 - x0)) % 360
    return 75.0


def vad_palette(v, a, d):
    """Valdez & Mehrabian-style aura: L* tracks valence (minus a little dominance), chroma tracks arousal,
    hue from the valence-arousal angle; weak affect (near the origin) fades toward neutral grey."""
    v, a, d = (float(np.clip(x, -1, 1)) for x in (v, a, d))
    h = _hue_for(v, a)
    r = min(1.0, math.hypot(v, a) / 0.6)
    L = 55 + 22 * v - 6 * d
    C = (12 + 48 * (a + 1) / 2) * (0.35 + 0.65 * r)
    # base, lighter analogous, darker analogous, highlight, shadow
    shades = [(L, C, h), (L + 14, C * 0.75, h + 22), (L - 16, C * 0.9, h - 22),
              (L + 30, C * 0.4, h + 45), (L - 32, C * 0.55, h - 40)]
    pal = [rgb_to_hex(lch_to_rgb(float(np.clip(l, 8, 97)), c, hh)) for l, c, hh in shades]
    return {"colors": pal}


# ---------- CLIP ----------

def clip_model():
    import torch, open_clip
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(CLIP_ID)
    model = model.to(dev).eval()
    return model, preprocess, open_clip.get_tokenizer(CLIP_ID), dev


def embed_texts(texts, clip):
    import torch
    model, _, tok, dev = clip
    with torch.no_grad():
        e = model.encode_text(tok(texts).to(dev)).float()
    e = e / e.norm(dim=-1, keepdim=True)
    return e.cpu().numpy()


def swatch_set():
    """580 in-gamut colors on an LCh grid (L 15..95, chroma 0..100, 24 hues) plus greys."""
    labs = []
    for L in range(15, 100, 10):
        labs.append([L, 0, 0])
        for C in range(15, 105, 15):
            for h in range(0, 360, 15):
                lab = [L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h))]
                if in_gamut(np.array(lab)):
                    labs.append(lab)
    labs = np.array(labs, float)
    return labs, [rgb_to_hex(np.clip(lab_to_rgb_unclipped(l), 0, 1)) for l in labs]


def embed_swatches(hexes, clip):
    import torch
    from PIL import Image
    model, preprocess, _, dev = clip
    path = os.path.join(CACHE, f"swatches_{len(hexes)}.npy")
    if os.path.exists(path):
        return np.load(path)
    out = []
    with torch.no_grad():
        for i in range(0, len(hexes), 32):
            ims = torch.stack([preprocess(Image.new("RGB", (224, 224), h)) for h in hexes[i:i + 32]]).to(dev)
            e = model.encode_image(ims).float()
            out.append((e / e.norm(dim=-1, keepdim=True)).cpu().numpy())
            print(f"  swatches {i + len(ims)}/{len(hexes)}", end="\r", file=sys.stderr)
    out = np.concatenate(out)
    os.makedirs(CACHE, exist_ok=True)
    np.save(path, out)
    return out


def affect_axes(texts, clip):
    """Project texts on each anchor axis; scale so the anchor poles sit at +-1 around their midpoint,
    then use the calibration sentences' spread to stretch (tanh keeps it in [-1, 1])."""
    E = embed_texts(texts, clip)
    C = embed_texts(CALIBRATION, clip)
    out = {}
    for axis, (pos, neg) in ANCHORS.items():
        P, N = embed_texts(pos, clip).mean(0), embed_texts(neg, clip).mean(0)
        u = P - N
        mid = (P + N) @ u / 2
        sd = (C @ u).std()
        out[axis] = np.tanh((E @ u - mid) / (2 * sd))
    return out


def diverse_top(scores, labs, hexes, k=5, min_de=15.0):
    """Walk swatches by score and keep one only if it is at least min_de CIEDE2000 from those already kept."""
    picked = []
    for j in np.argsort(-scores):
        if all(ciede2000(labs[j], labs[p]) >= min_de for p in picked):
            picked.append(j)
            if len(picked) == k:
                break
    return picked


# ---------- Gemini ----------

GEM_PALETTE_SCHEMA = {"type": "OBJECT", "properties": {
    "colors": {"type": "ARRAY", "items": {"type": "STRING", "description": "hex color like #a1b2c3"},
               "minItems": 5, "maxItems": 5},
    "brightness": {"type": "NUMBER", "description": "0 dark .. 1 bright"},
    "saturation": {"type": "NUMBER", "description": "0 grey .. 1 vivid"}},
    "required": ["colors", "brightness", "saturation"]}
GEM_VAD_SCHEMA = {"type": "OBJECT", "properties": {
    "valence": {"type": "NUMBER", "description": "-1 unpleasant .. 1 pleasant"},
    "arousal": {"type": "NUMBER", "description": "-1 calm, sleepy .. 1 excited, agitated"},
    "dominance": {"type": "NUMBER", "description": "-1 helpless .. 1 in control"}},
    "required": ["valence", "arousal", "dominance"]}
GEM_PALETTE_PROMPT = ("A visitor at an interactive art installation said: \"{text}\"\n"
                      "Choose a palette of exactly 5 colors (an aura) that expresses the feeling behind what they said, "
                      "the way a colorist would. Return hex colors, plus the overall brightness and saturation (0 to 1).")
GEM_VAD_PROMPT = ("A visitor at an interactive art installation said: \"{text}\"\n"
                  "Rate the feeling behind it on valence, arousal and dominance, each from -1 to 1.")


HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def valid_answer(kind, ans):
    """Strict check of a Gemini answer; an invalid one is re-asked (as the booth would) and counted."""
    try:
        if kind == "palette":
            return len(ans["colors"]) == 5 and all(isinstance(c, str) and HEX.match(c.strip()) for c in ans["colors"])
        return all(-1 <= float(ans[k]) <= 1 for k in ("valence", "arousal", "dominance"))
    except (KeyError, TypeError, ValueError):
        return False


def _gemini_call(client, cfg, prompt):
    for wait in (15, 30, 60, 120, None):   # 429 RESOURCE_EXHAUSTED on the hackathon quota: back off and retry
        try:
            r = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=cfg)
            return json.loads(r.text)
        except json.JSONDecodeError:
            return {"_unparseable": True}
        except Exception as e:
            if "429" not in str(e) or wait is None:
                raise
            time.sleep(wait)


def gemini_answers(texts, kind, rep, use_api, max_tries=3):
    """Cached Gemini answers. Invalid answers are kept under cache['_invalid'] so the failure rate can be reported."""
    path = os.path.join(OUT, "aura_gemini_cache.json")
    cache = json.load(open(path)) if os.path.exists(path) else {}
    invalid = cache.setdefault("_invalid", [])
    key = lambda t: f"{GEMINI_MODEL}|{kind}|{rep}|{t}"
    for t in texts:   # answers cached before validation existed
        if key(t) in cache and not valid_answer(kind, cache[key(t)]):
            invalid.append({"key": key(t), "answer": cache.pop(key(t))})
    missing = [t for t in texts if key(t) not in cache]
    if missing and use_api:
        from google import genai
        from google.genai import types
        client = genai.Client(vertexai=True, project=GCP_PROJECT, location="global")
        prompt, schema = (GEM_PALETTE_PROMPT, GEM_PALETTE_SCHEMA) if kind == "palette" else (GEM_VAD_PROMPT, GEM_VAD_SCHEMA)
        cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema, temperature=1.0)
        os.makedirs(OUT, exist_ok=True)
        try:
            for i, t in enumerate(missing):
                tries = sum(1 for x in invalid if x["key"] == key(t))
                while tries < max_tries:
                    ans = _gemini_call(client, cfg, prompt.format(text=t))
                    if valid_answer(kind, ans):
                        cache[key(t)] = ans
                        break
                    invalid.append({"key": key(t), "answer": ans})
                    tries += 1
                json.dump(cache, open(path, "w"), indent=1, sort_keys=True)   # save as we go
                print(f"  gemini {kind} rep{rep} {i + 1}/{len(missing)}", end="\r", file=sys.stderr)
        except Exception as e:
            print(f"\n  gemini stopped: {e.__class__.__name__}: {str(e)[:160]}", file=sys.stderr)
    json.dump(cache, open(path, "w"), indent=1, sort_keys=True)
    if any(key(t) not in cache for t in texts):
        return None
    return [cache[key(t)] for t in texts]


def gemini_invalid_rate(kind):
    """Share of Gemini calls of this kind whose answer failed the strict check (and had to be re-asked)."""
    path = os.path.join(OUT, "aura_gemini_cache.json")
    cache = json.load(open(path)) if os.path.exists(path) else {}
    bad = sum(1 for x in cache.get("_invalid", []) if f"|{kind}|" in x["key"])
    good = sum(1 for k in cache if f"|{kind}|" in k)
    return round(bad / max(1, bad + good), 3), bad, bad + good


def clean_hex(colors):
    out = []
    for c in colors[:5]:
        try:
            out.append(rgb_to_hex(hex_to_rgb(c)))
        except Exception:
            out.append("#808080")
    return out + ["#808080"] * (5 - len(out))


# ---------- scoring and board ----------

def score(name, palettes, feelings, opposites, repeat=None):
    labs = [palette_lab(p["colors"]) for p in palettes]
    r = metrics.report_outputs(name, labs, palette_distance, feelings, opposites)
    # Absolute scale alongside the shared ratios (Delta E 2000), so a ratio on near-identical palettes isn't misread.
    para, opp = metrics._pairs(feelings, opposites)
    rng = np.random.default_rng(0)
    rand = [tuple(rng.choice(len(labs), 2, replace=False)) for _ in range(400)]
    mean_d = lambda ps: round(float(np.mean([palette_distance(labs[a], labs[b]) for a, b in ps])), 1)
    r.update({"dE_random": mean_d(rand), "dE_paraphrase": mean_d(para), "dE_opposite": mean_d(opp),
              "within_palette_dE": round(float(np.mean([within_palette_spread(l) for l in labs])), 1)})
    # Palette-level collapse: share of pairs of *different* feelings whose auras are near-identical (dE < 5).
    diff = [(a, b) for a in range(len(labs)) for b in range(a + 1, len(labs)) if feelings[a]["para"] != feelings[b]["para"]]
    r["near_duplicate_share"] = round(float(np.mean([palette_distance(labs[a], labs[b]) < 5 for a, b in diff])), 3)
    if repeat is not None:   # same text, second sample: how stable the mapping is run to run
        rl = [palette_lab(p["colors"]) for p in repeat]
        r["dE_repeat"] = round(float(np.mean([palette_distance(a, b) for a, b in zip(labs, rl)])), 1)
    return r


def board(columns, feelings, path):
    from PIL import Image, ImageDraw, ImageFont
    sw, rh, lw, gap, head = 26, 22, 330, 14, 40
    names = list(columns)
    W = lw + len(names) * (5 * sw + gap) + gap
    H = head + len(feelings) * rh + 8
    im = Image.new("RGB", (W, H), "#f4f1ea")
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
        bold = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 12)
    except OSError:
        font = bold = ImageFont.load_default()
    for j, n in enumerate(names):
        dr.text((lw + j * (5 * sw + gap), 14), n, fill="#222", font=bold)
    for i, f in enumerate(feelings):
        y = head + i * rh
        if i % 2 == 0 and i:
            dr.line([(8, y - 1), (W - 8, y - 1)], fill="#d8d2c4")
        t = f["text"] if len(f["text"]) <= 40 else f["text"][:39] + "…"
        dr.text((8, y + 4), f"{f['id']:<11}", fill="#222", font=bold)
        dr.text((88, y + 4), t, fill="#444", font=font)
        for j, n in enumerate(names):
            x0 = lw + j * (5 * sw + gap)
            for k, c in enumerate(columns[n][i]["colors"]):
                dr.rectangle([x0 + k * sw, y + 2, x0 + (k + 1) * sw - 1, y + rh - 3], fill=c)
    im.save(path, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-gemini", action="store_true", help="use only cached Gemini answers")
    args = ap.parse_args()
    feelings, opposites = metrics.load_feelings()
    texts = [f["text"] for f in feelings]
    os.makedirs(OUT, exist_ok=True)
    cols, reports, extra = {}, [], {}

    print("loading CLIP", CLIP_ID, file=sys.stderr)
    clip = clip_model()

    # (a) affect -> color, CLIP anchors
    vad = affect_axes(texts, clip)
    cols["a_affect_clip"] = [vad_palette(vad["valence"][i], vad["arousal"][i], vad["dominance"][i]) for i in range(len(texts))]
    extra["a_affect_clip_vad"] = {f["id"]: [round(float(vad[k][i]), 2) for k in ("valence", "arousal", "dominance")]
                                  for i, f in enumerate(feelings)}

    # (a') affect -> color, Gemini ratings
    gv = gemini_answers(texts, "vad", 0, not args.no_gemini)
    if gv:
        cols["a_affect_gemini"] = [vad_palette(g["valence"], g["arousal"], g["dominance"]) for g in gv]
        extra["a_affect_gemini_vad"] = {f["id"]: [g["valence"], g["arousal"], g["dominance"]] for f, g in zip(feelings, gv)}

    # (b) CLIP text vs swatch images, with each swatch's bias (its mean similarity to generic sentences) removed
    labs, hexes = swatch_set()
    S = embed_swatches(hexes, clip)
    T = embed_texts([f"the color of this feeling: {t}" for t in texts], clip)
    Cal = embed_texts([f"the color of this feeling: {t}" for t in CALIBRATION], clip)
    raw = T @ S.T
    centered = raw - (Cal @ S.T).mean(0, keepdims=True)
    for name, sc in (("b_clip_swatch_raw", raw), ("b_clip_swatch", centered)):
        cols[name] = [{"colors": [hexes[j] for j in diverse_top(sc[i], labs, hexes)]} for i in range(len(texts))]
        reports.append(dict(metrics.report_scores(name + " (as swatch library)", sc, feelings, opposites), n_swatches=len(hexes)))

    # (c) Gemini palette directly
    gp = gemini_answers(texts, "palette", 0, not args.no_gemini)
    gp1 = gemini_answers(texts, "palette", 1, not args.no_gemini)
    if gp:
        cols["c_gemini"] = [{"colors": clean_hex(g["colors"]), "brightness": g.get("brightness"),
                             "saturation": g.get("saturation")} for g in gp]
    else:
        print("Gemini answers not available: skipping c_gemini and a_affect_gemini", file=sys.stderr)

    gv1 = gemini_answers(texts, "vad", 1, not args.no_gemini)
    repeats = {"c_gemini": [{"colors": clean_hex(g["colors"])} for g in gp1] if gp1 else None,
               "a_affect_gemini": [vad_palette(g["valence"], g["arousal"], g["dominance"]) for g in gv1] if gv1 else None}

    # every output gets the measured brightness/saturation of its palette
    for name, pals in cols.items():
        for p in pals:
            p["brightness_measured"], p["saturation_measured"] = brightness_saturation(palette_lab(p["colors"]))
        r = score(name, pals, feelings, opposites, repeats.get(name))
        kind = {"c_gemini": "palette", "a_affect_gemini": "vad"}.get(name)
        if kind:
            r["invalid_answer_rate"], r["invalid_answers"], r["gemini_calls"] = gemini_invalid_rate(kind)
        reports.insert(0, r)
    reports = sorted([r for r in reports if "coverage_top1" not in r], key=lambda r: r["candidate"]) + \
              [r for r in reports if "coverage_top1" in r]

    with open(os.path.join(OUT, "aura_outputs.json"), "w") as f:
        json.dump({"feelings": [f["id"] for f in feelings], "palettes": cols, "affect": extra}, f, indent=1)
    with open(os.path.join(OUT, "aura_metrics.json"), "w") as f:
        json.dump(reports, f, indent=1)
    shown = {k: cols[k] for k in ("a_affect_clip", "a_affect_gemini", "b_clip_swatch", "c_gemini") if k in cols}
    board(shown, feelings, os.path.join(OUT, "aura_board.png"))
    for r in reports:
        print(json.dumps(r))


if __name__ == "__main__":
    main()
