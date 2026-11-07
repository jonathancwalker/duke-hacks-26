# Vibe paint (lab side): the painting is changed only along a visitor's hand path. The GPU repaints the scene in the
# visitor's mood; the page shows that repainting only through their path.
#
# What the rounds showed (HYPOTHESES.md): style-only injection at 1.4 carries tone without importing figures.
# Blending painters, palette matching and color words barely change the chapel, because the scene prompt pulls
# everything toward the same greens. Letting the mood set the scene's light and weather (Gemini's "atmosphere")
# separates moods most. Without a scene (abstract mode) moods are the most distinct of all.

VIBE_STYLE = 1.4
SCENE = "an oil painting of a gothic chapel tower above still water, reflections on the water, visible brushstrokes"
ABSTRACT = "an abstract expressive painting, gestural brushstrokes and loose color fields, no objects"
_VIBE_COND = globals().setdefault("_VIBE_COND", {})


def _cond(text):
    if text not in _VIBE_COND:
        if len(_VIBE_COND) > 200:
            _VIBE_COND.clear()
        _VIBE_COND[text] = E(text)
    return _VIBE_COND[text]


def vibe_point(weights, energy=0.5, warmth=0.0, light=0.0):
    """Painting mix (Gemini's picks) pushed along the art-space axes by the visitor's energy, warmth and light."""
    v = mix_vector(weights)
    v = v + (float(energy) - 0.5) * 2 * ART_AXES["energy"] + float(warmth) * ART_AXES["temperature"] + float(light) * ART_AXES["value"]
    return v / v.norm() * MEAN_NORM


def vibe_frame(weights, energy=0.5, warmth=0.0, light=0.0, atmosphere="", mode="scene", seed=7):
    """mode 'scene': the chapel in the visitor's light and weather, aligned to the base. 'abstract': no scene."""
    ip = vibe_point(weights, energy, warmth, light)
    if mode == "abstract":
        return render2(cond=_cond(ABSTRACT), ip=ip, ip_scale=style_only(VIBE_STYLE), seed=seed, cn_scale=0.0, cn_end=1.0)
    text = f"{SCENE}, {atmosphere.strip()}" if atmosphere and atmosphere.strip() else SCENE
    return render2(cond=_cond(text), ip=ip, ip_scale=style_only(VIBE_STYLE), seed=seed, **ART_CN)


def base_frame(seed=7):
    """The starting underpainting: calm and pale, same scene and seed as every vibe frame."""
    return render2(cond=_cond(SCENE), ip=art_point({"energy": -0.6, "temperature": 0.1, "value": 0.6}),
                   ip_scale=style_only(VIBE_STYLE), seed=seed, **ART_CN)
