# Issue #9 spike (lab side): two of the three feeling -> color mappings, for the same 12 feelings.
#   (a) palette of the nearest paintings: CLIP text -> top 3 artworks in the library -> k-means of their pixels
#   (c) CLIP swatches: score a grid of solid color swatches against the feeling's words, keep the best 5 distinct ones
# (b), the VAD aura, is drawn locally in color_vad.py. If DATA carries a lexicon sample, this also fits the embedding
#     version of VAD (ridge regression from CLIP text embeddings to the lexicon's scores) so phrases are read in context.
#
# Both CLIP mappings have a hub problem: a few paintings (Friedrich's Wanderer) and a few swatches (pale mint) score
# high for every prompt. "Debiased" subtracts each item's mean similarity over a bank of 40 unrelated feelings.
#
#   python3 lab.py lab/c1_color_map.py --data lab/c1_feelings.json      (prints JSON between PALETTES markers)
#   The lexicon sample is NOT in git (the NRC VAD Lexicon may not be redistributed); color_vad.py documents it.
import json
import cv2
from PIL import ImageDraw

K = 5
BANK = ["bored at work", "excited for the weekend", "tired after a long day", "proud of my little sister",
        "annoyed by traffic", "relieved the exam is over", "jealous of my friend", "grateful for my parents",
        "confused about my major", "playful and silly", "guilty about forgetting a birthday", "content with dinner",
        "frustrated with my code", "curious about space", "embarrassed I tripped", "nostalgic for summer camp",
        "overwhelmed by email", "peaceful by the lake", "restless and can't sleep", "disappointed in the result",
        "amused by a cat video", "shy meeting new people", "determined to finish", "sad the show ended",
        "thrilled about the concert", "worried about money", "sleepy on the bus", "cheerful in the sunshine",
        "irritated by noise", "inspired by a lecture", "heartbroken after the breakup", "silly with my roommate",
        "tense before the game", "lazy Saturday", "ashamed of what I said", "joyful at the wedding",
        "suspicious of the email", "comforted by tea", "anxious about the flight", "satisfied with my work"]


def hexs(rgb):
    return "#%02x%02x%02x" % tuple(int(round(float(c))) for c in rgb)


def rgb_to_lab(rgb):
    return cv2.cvtColor(np.array([[rgb]], np.float32) / 255, cv2.COLOR_RGB2LAB)[0, 0]


def lab_to_rgb(lab):
    """Float Lab (L 0..100) -> sRGB 0..255, plus whether it was inside the gamut."""
    rgb = cv2.cvtColor(np.array([[lab]], np.float32), cv2.COLOR_LAB2RGB)[0, 0]
    return np.clip(rgb, 0, 1) * 255, bool(np.all(rgb >= -0.004) and np.all(rgb <= 1.004))


# ---------- (a) nearest paintings ----------
ART_PRIOR = (ART_MN @ clip_text([f"a painting that feels {b}" for b in BANK]).T).mean(1)


def nearest_paintings(text, debias, k=3, temp=0.02):
    sims = (ART_MN @ clip_text([f"a painting that feels {text}"]).T).squeeze(1)   # 00_lib.py art_weights() prompt
    if debias:
        sims = sims - ART_PRIOR
    top = torch.topk(sims, k)
    w = torch.softmax(top.values / temp, 0)
    return [(ART_NAMES[i], 0.0, float(wi)) for i, wi in zip(top.indices.tolist(), w.tolist())]


def painting_palette(text, debias):
    ws = nearest_paintings(text, debias)
    rng = np.random.default_rng(0)
    px = []
    for name, _, w in ws:
        p = np.asarray(ART[name].convert("RGB").resize((128, 128)), np.float32).reshape(-1, 3)
        px.append(p[rng.choice(len(p), max(1, int(6000 * w)))])
    px = np.concatenate(px)
    lab = cv2.cvtColor(px[None] / 255, cv2.COLOR_RGB2LAB)[0]
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    _, lbl, centers = cv2.kmeans(lab.astype(np.float32), K, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    share = np.bincount(lbl.ravel(), minlength=K) / len(lbl)
    order = np.argsort(-share)
    cols = [{"hex": hexs(lab_to_rgb(centers[i])[0]), "share": round(float(share[i]), 3)} for i in order]
    return cols, [{"name": n, "weight": round(w, 3)} for n, _, w in ws]


# ---------- (c) CLIP vs color swatches ----------
SW = []
for h in range(0, 360, 15):
    for L in (25, 45, 65, 85):
        for C in (20, 45, 75):
            rgb, ok = lab_to_rgb([L, C * np.cos(np.radians(h)), C * np.sin(np.radians(h))])
            if ok:
                SW.append(rgb)
for L in (8, 30, 55, 78, 97):
    SW.append(lab_to_rgb([L, 0, 0])[0])
SW_LAB = np.array([rgb_to_lab(c) for c in SW])
SW_EMB = torch.cat([clip_image(Image.new("RGB", (224, 224), tuple(int(c) for c in rgb))) for rgb in SW])
SW_EMB = SW_EMB / SW_EMB.norm(dim=-1, keepdim=True)
print(f"{len(SW)} swatches embedded")
SW_PRIOR = (SW_EMB @ clip_text([f"a color that feels like this: {b}" for b in BANK]).T).mean(1).cpu().numpy()


def swatch_palette(text, debias, min_de=22):
    t = clip_text([f"a color that feels like this: {text}"])
    sims = (SW_EMB @ t.T).squeeze(1).cpu().numpy() - (SW_PRIOR if debias else 0)
    picked = []
    for i in np.argsort(-sims):
        if all(np.linalg.norm(SW_LAB[i] - SW_LAB[j]) >= min_de for j in picked):
            picked.append(i)
        if len(picked) == K:
            break
    return [{"hex": hexs(SW[i]), "score": round(float(sims[i]), 4)} for i in picked]


# ---------- (b) helper: VAD from an embedding, fit on the lexicon ----------
VAD_W = None
if DATA.get("lexicon"):
    words = [r[0] for r in DATA["lexicon"]]
    X = torch.cat([clip_text(words[i:i + 256]) for i in range(0, len(words), 256)]).double()
    Y = torch.tensor([r[1:4] for r in DATA["lexicon"]], dtype=torch.float64, device=X.device)
    n = len(words); cut = int(n * 0.9)
    def ridge(Xa, Ya, lam=0.5):
        Xa = torch.cat([Xa, torch.ones(len(Xa), 1, dtype=Xa.dtype, device=Xa.device)], 1)
        return torch.linalg.solve(Xa.T @ Xa + lam * torch.eye(Xa.shape[1], dtype=Xa.dtype, device=Xa.device), Xa.T @ Ya)
    def pred(Wt, Xa):
        return torch.cat([Xa, torch.ones(len(Xa), 1, dtype=Xa.dtype, device=Xa.device)], 1) @ Wt
    Wt = ridge(X[:cut], Y[:cut])
    P = pred(Wt, X[cut:])
    r = [float(torch.corrcoef(torch.stack([P[:, k], Y[cut:, k]]))[0, 1]) for k in range(3)]
    print("held-out correlation with the lexicon (V, A, D):", [round(x, 2) for x in r])
    VAD_W = ridge(X, Y)


def vad_embed(text):
    return [round(float(x), 3) for x in pred(VAD_W, clip_text([text]).double())[0]]


out = {"library_size": len(ART_NAMES), "swatches": len(SW), "feelings": []}
for f in DATA["feelings"]:
    row = {"id": f["id"]}
    for tag, db in (("raw", False), ("debiased", True)):
        pal, near = painting_palette(f["text"], db)
        row[f"paintings_{tag}"], row[f"nearest_{tag}"] = pal, near
        row[f"clip_{tag}"] = swatch_palette(f["text"], db)
    if VAD_W is not None:
        row["vad_embed"] = vad_embed(f["text"])
    out["feelings"].append(row)

# A quick contact sheet so the run can be eyeballed (the blind test hides which row is which)
cw, rh, left = 60, 46, 150
COLS = ["paintings_raw", "paintings_debiased", "clip_raw", "clip_debiased"]
sheet = Image.new("RGB", (left + 4 * (K * cw + 30), 30 + rh * len(out["feelings"])), (245, 242, 236))
d = ImageDraw.Draw(sheet)
for c, name in enumerate(COLS):
    d.text((left + c * (K * cw + 30), 8), name, fill=(0, 0, 0))
for r, f in enumerate(out["feelings"]):
    y = 30 + r * rh
    d.text((8, y + 14), f["id"], fill=(0, 0, 0))
    for c, pal in enumerate(f[k] for k in COLS):
        for i, col in enumerate(pal):
            x = left + c * (K * cw + 30) + i * cw
            d.rectangle([x, y, x + cw - 4, y + rh - 6], fill=col["hex"])
show(sheet, "c1_palettes")
print("PALETTES_JSON_START")
print(json.dumps(out))
print("PALETTES_JSON_END")
