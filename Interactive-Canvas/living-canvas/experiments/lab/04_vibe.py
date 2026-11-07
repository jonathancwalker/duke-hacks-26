# Vibe paint (lab side): the painting is changed only along a visitor's hand path. The GPU renders the SAME scene
# (same seed, same chapel outline lock) in the visitor's mood, so it lines up pixel for pixel with the current
# painting; the page composites it through the path mask.
#
# V1 rounds: style-only injection carries tone as well as brushwork (grief went dark green, triumph bold); full
# injection imports figures again. A bold starting painting hid bright moods, so the night starts from a calm,
# pale underpainting and every visitor's swath stands out against it.

VIBE_STYLE = 1.4


def vibe_point(weights, energy=0.5, warmth=0.0, light=0.0):
    """Painting mix (Gemini's picks) pushed along the art-space axes by the visitor's energy, warmth and light."""
    v = mix_vector(weights)
    v = v + (float(energy) - 0.5) * 2 * ART_AXES["energy"] + float(warmth) * ART_AXES["temperature"] + float(light) * ART_AXES["value"]
    return v / v.norm() * MEAN_NORM


def vibe_frame(weights, energy=0.5, warmth=0.0, light=0.0, seed=7):
    return render2(ip=vibe_point(weights, energy, warmth, light), ip_scale=style_only(VIBE_STYLE), seed=seed, **ART_CN)


def base_frame(seed=7):
    """The starting underpainting: calm and pale, same scene and seed as every vibe frame."""
    return render2(ip=art_point({"energy": -0.6, "temperature": 0.1, "value": 0.6}), ip_scale=style_only(VIBE_STYLE), seed=seed, **ART_CN)
