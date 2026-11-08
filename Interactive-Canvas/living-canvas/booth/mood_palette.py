"""A visitor's mood palette: 5 colors from how they feel, how loud they were and how they moved (issue #10).

Spike #9 (HYPOTHESES.md) chose the VAD aura: the language model reads valence, arousal and dominance from what the
visitor said, and Valdez & Mehrabian (1994) turn them into color. Their regressions
    pleasure = .69 B + .22 S,   arousal = -.31 B + .60 S,   dominance = -.76 B + .32 S
are inverted for brightness B and saturation S, so brightness tracks pleasure and saturation tracks arousal.

The spike's weak part was hue: taking it from the circumplex quadrant made grief, loneliness and boredom one grey-blue,
and nervousness, fury and fear one dark red; love came out yellow. So the reader also names the feeling's hue, and the
quadrant rule is only the fallback when it doesn't. It names two colors, as hex (models name colors far better than
they pick hue angles: asked for angles, Gemini gave grief and loneliness the same blue and ochre). Only their hues are
used, the second for the last two colors, so neighbors such as grief and loneliness come out apart.

On top of the feeling:
  - voice energy (0 quiet .. 1 loud, from the mic) shifts saturation: a shouted feeling is more vivid than a whispered one;
  - movement (0 still .. 1 vigorous, from the pose tracker) shifts brightness and light-dark contrast.
Both nudge the palette; the feeling still decides it.

Colors are built in CIE LCh, so lightness and chroma steps look even, then fitted into sRGB.
"""
import math

QUAD = [(45, 72), (135, 25), (225, 285), (315, 165)]   # circumplex angle (0 pleasant, 90 aroused) -> LCh hue


def _clamp(x, lo=-1.0, hi=1.0):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    return lo if x != x else max(lo, min(hi, x))      # NaN -> lo


def _lab_to_srgb(L, a, b):
    fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    finv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    X, Y, Z = 0.95047 * finv(fx), finv(fy), 1.08883 * finv(fz)
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    bl = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    gam = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return tuple(gam(c) for c in (r, g, bl))


def _srgb_to_lab(rgb):
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    X = (0.4124 * lin[0] + 0.3576 * lin[1] + 0.1805 * lin[2]) / 0.95047
    Y = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    Z = (0.0193 * lin[0] + 0.1192 * lin[1] + 0.9505 * lin[2]) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))


def hex_to_lab(h):
    h = h.lstrip("#")
    return _srgb_to_lab([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def lch(L, C, h):
    """LCh -> sRGB hex, lowering chroma until it fits the gamut; lightness kept off pure black and white."""
    L = max(6.0, min(95.0, L))
    while C > 0:
        rgb = _lab_to_srgb(L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h)))
        if all(-0.001 <= c <= 1.001 for c in rgb):
            break
        C -= 1
    else:
        rgb = _lab_to_srgb(L, 0, 0)
    return "#%02x%02x%02x" % tuple(round(min(1, max(0, c)) * 255) for c in rgb)


def hsl_hue_to_lch(deg):
    """The HSL hue a language model names (0 red, 60 yellow, 120 green, 240 blue, 300 magenta) -> LCh hue angle."""
    h = (float(deg) % 360) / 60
    x = 1 - abs(h % 2 - 1)
    rgb = [(1, x, 0), (x, 1, 0), (0, 1, x), (0, x, 1), (x, 0, 1), (1, 0, x)][int(h) % 6]
    _, a, b = _srgb_to_lab(rgb)
    return math.degrees(math.atan2(b, a)) % 360


def circumplex_hue(v, a):
    """Fallback hue from the feeling's place on Russell's circumplex (spike #9's rule)."""
    ang = math.degrees(math.atan2(a, v)) % 360
    pts = QUAD + [(QUAD[0][0] + 360, QUAD[0][1])]
    lo = max(q for q in pts if q[0] <= ang) if ang >= QUAD[0][0] else (QUAD[-1][0] - 360, QUAD[-1][1])
    hi = min(q for q in pts if q[0] > ang)
    t = (ang - lo[0]) / (hi[0] - lo[0])
    dh = ((hi[1] - lo[1] + 180) % 360) - 180
    return (lo[1] + t * dh) % 360


def _hue(x, fallback):
    """A hue given as "#rrggbb" (its LCh hue) or as HSL degrees; anything unreadable -> fallback."""
    try:
        if isinstance(x, str) and x.strip().startswith("#"):
            L, a, b = hex_to_lab(x.strip()[:7])
            return math.degrees(math.atan2(b, a)) % 360 if math.hypot(a, b) > 4 else fallback   # grey has no hue
        return hsl_hue_to_lch(x) if x is not None else fallback
    except (TypeError, ValueError, OverflowError, IndexError):
        return fallback


def mood_palette(valence, arousal, dominance, hue=None, accent_hue=None, voice=0.5, movement=0.35):
    """valence, arousal, dominance: -1..1. hue, accent_hue: "#rrggbb" or HSL degrees, named by the reader; None falls
    back to the circumplex rule (hue) and fixed offsets from it (accent).
    voice: 0..1 loudness/energy. movement: 0..1 (0.35 when no body was seen, matching move.js).
    Returns {"palette": [5 hex], "hue": LCh hue used, "lightness", "chroma"}."""
    v, a, d = _clamp(valence), _clamp(arousal), _clamp(dominance)
    voice, movement = _clamp(voice, 0, 1), _clamp(movement, 0, 1)
    det = 0.69 * 0.60 + 0.22 * 0.31
    B = _clamp((0.60 * v - 0.22 * a) / det)                 # brightness from pleasure (and a little arousal)
    S = _clamp((0.31 * v + 0.69 * a) / det)                 # saturation from arousal (and a little pleasure)
    L = 55 + 28 * B + 8 * (movement - 0.35)                 # moving more lifts the palette a little
    C = max(18.0, 38 + 34 * S + 18 * (voice - 0.5))         # a louder voice makes it more vivid; never fully grey,
                                                            # or quiet sad feelings would all lose their hue
    h = _hue(hue, circumplex_hue(v, a))
    ac = _hue(accent_hue, None)
    spread = (12 + 10 * (d + 1) / 2) * (0.8 + 0.5 * movement)   # dominance and movement widen light-dark contrast
    pal = [lch(L, C, h), lch(L + spread, C * 0.7, h - 12), lch(L - spread, C * 0.9, h + 12),
           lch(L + 0.5 * spread, max(24.0, C * 1.1), ac if ac is not None else h + 35),
           lch(L - 1.6 * spread, C * 0.7, ac if ac is not None else h - 30)]
    return {"palette": pal, "hue": round(h, 1), "accent_hue": None if ac is None else round(ac, 1),
            "lightness": round(L, 1), "chroma": round(max(0.0, C), 1)}


def palette_distance(p, q):
    """Mean CIE76 distance between two palettes, colors paired in order (same recipe, so order lines up)."""
    return sum(math.dist(hex_to_lab(x), hex_to_lab(y)) for x, y in zip(p, q)) / min(len(p), len(q))
