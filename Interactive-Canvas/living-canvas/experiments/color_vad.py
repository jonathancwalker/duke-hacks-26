#!/usr/bin/env python3
"""Issue #9 spike, mapping (b): an aura from feeling, via the NRC VAD Lexicon v2.1 (Mohammad, 2025).

    python3 color_vad.py /path/to/NRC-VAD-Lexicon-v2.1.txt lab/c1_feelings.json > lab/c1_vad_palettes.json

The lexicon is free for non-commercial research but may not be redistributed, so it is NOT in git. Get it from
https://saifmohammad.com/WebPages/nrc-vad.html. This application makes use of the NRC VAD Lexicon, created by
Saif M. Mohammad at the National Research Council Canada.

Words -> valence/arousal/dominance (each -1..1): longest-match multi-word expressions first, then single words
(with a crude suffix strip, so "passed away" finds "pass away"); each matched term is weighted by how emotional it
is, (|v| + |a|)^2, so "furious" outweighs "landlord". If a feeling also carries "vad_claude" (scores Claude wrote
by reading the sentence, as round 3's art director did), the same color rule is drawn from those too, which
separates "is the reading right?" from "is the color rule right?".

VAD -> color, per Valdez & Mehrabian (1994): their regressions
    pleasure = .69 B + .22 S,   arousal = -.31 B + .60 S,   dominance = -.76 B + .32 S
are inverted for brightness B and saturation S from (pleasure, arousal); brightness tracks pleasure and
saturation tracks arousal. Their hue effects were weak, so hue comes from the position on Russell's circumplex
(an assumption, documented in HYPOTHESES.md): pleasant + aroused -> warm yellow-orange, pleasant + calm ->
green-teal, unpleasant + calm -> blue-violet, unpleasant + aroused -> red. Dominance widens the palette's
light-dark contrast. Colors are built in CIE LCh, so lightness and chroma are perceptual.
"""
import json, math, re, sys

STOP = {"i", "im", "i'm", "my", "me", "the", "a", "an", "and", "of", "to", "is", "it", "in", "on", "just",
        "so", "about", "what", "will", "say", "even", "our", "we", "much", "kind", "think", "things", "still"}


def load(path):
    lex = {}
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            t, v, a, d = line.rstrip("\n").split("\t")
            lex[t.lower()] = (float(v), float(a), float(d))
    return lex


def vad(text, lex):
    toks = re.findall(r"[a-z']+", text.lower().replace("’", "'"))
    def find(term):
        if term in lex:
            return term
        w = term.split(" ")
        for suf, rep in (("ied", "y"), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"), ("s", "")):
            if w[0].endswith(suf):
                t = " ".join([w[0][: -len(suf)] + rep] + w[1:])
                if t in lex:
                    return t
        return None
    hits, i = [], 0
    while i < len(toks):
        for n in (3, 2, 1):
            term = find(" ".join(toks[i:i + n])) if len(toks[i:i + n]) == n else None
            if term and (n > 1 or toks[i] not in STOP):
                hits.append((term, lex[term])); i += n; break
        else:
            i += 1
    if not hits:
        return (0.0, 0.0, 0.0), []
    w = [(abs(v) + abs(a)) ** 2 + 1e-3 for _, (v, a, _) in hits]
    m = tuple(sum(wi * h[1][k] for wi, h in zip(w, hits)) / sum(w) for k in range(3))
    return m, [t for t, _ in hits]


# ---------- color ----------
def lab_to_srgb(L, a, b):
    fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    finv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    X, Y, Z = 0.95047 * finv(fx), finv(fy), 1.08883 * finv(fz)
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    bl = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    gam = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return tuple(gam(c) for c in (r, g, bl))


def lch(L, C, h):
    """LCh -> sRGB hex, lowering chroma until it fits the gamut (lightness kept off pure black and white)."""
    L = max(6.0, min(95.0, L))
    while C > 0:
        rgb = lab_to_srgb(L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h)))
        if all(-0.001 <= c <= 1.001 for c in rgb):
            break
        C -= 1
    else:
        rgb = lab_to_srgb(L, 0, 0)
    return "#%02x%02x%02x" % tuple(round(min(1, max(0, c)) * 255) for c in rgb)


QUAD = [(45, 72), (135, 25), (225, 285), (315, 165)]   # circumplex angle -> LCh hue (deg)


def hue(p, a):
    ang = math.degrees(math.atan2(a, p)) % 360            # 0 = pleasant, 90 = aroused
    pts = QUAD + [(QUAD[0][0] + 360, QUAD[0][1])]
    lo = max(q for q in pts if q[0] <= ang) if ang >= QUAD[0][0] else (QUAD[-1][0] - 360, QUAD[-1][1])
    hi = min(q for q in pts if q[0] > ang)
    t = (ang - lo[0]) / (hi[0] - lo[0])
    dh = ((hi[1] - lo[1] + 180) % 360) - 180               # shortest way round the hue wheel
    return (lo[1] + t * dh) % 360


def aura(v, a, d):
    det = 0.69 * 0.60 + 0.22 * 0.31
    B = (0.60 * v - 0.22 * a) / det                      # brightness from pleasure (and a little arousal)
    S = (0.31 * v + 0.69 * a) / det                      # saturation from arousal (and a little pleasure)
    clamp = lambda x: max(-1.0, min(1.0, x))
    L = 55 + 28 * clamp(B)
    C = 38 + 34 * clamp(S)
    h = hue(v, a)
    spread = 12 + 10 * (d + 1) / 2                       # dominance -> stronger light/dark contrast
    return [lch(L, C, h), lch(L + spread, C * 0.7, h - 18), lch(L - spread, C * 0.9, h + 18),
            lch(L + 0.5 * spread, C * 1.1, h + 35), lch(L - 1.6 * spread, C * 0.6, h - 30)]


if __name__ == "__main__":
    lex = load(sys.argv[1])
    feelings = json.load(open(sys.argv[2]))["feelings"]
    out = {"feelings": []}
    for f in feelings:
        (v, a, d), terms = vad(f["text"], lex)
        row = {"id": f["id"], "vad": [round(v, 3), round(a, 3), round(d, 3)], "terms": terms,
               "aura": [{"hex": h} for h in aura(v, a, d)]}
        if "vad_claude" in f:
            row["aura_claude"] = [{"hex": h} for h in aura(*f["vad_claude"])]
        out["feelings"].append(row)
    json.dump(out, sys.stdout, indent=1)
