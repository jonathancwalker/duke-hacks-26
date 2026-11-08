#!/usr/bin/env python3
"""Mood palettes (issue #10): 8 test feelings give 8 visibly distinct palettes; voice and movement shift them.

    python3 booth/test_mood_palette.py          # offline: the rule-based reading of each feeling
    BOOTH_GCP_PROJECT=<id> python3 booth/test_mood_palette.py   # also through the real Gemini director (Vertex AI)

Also collectable by pytest. "Visibly distinct" = every pair of palettes is at least MIN_DE apart (mean CIE76 distance,
colors paired in order); about 10 is a clear difference side by side.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402
from mood_palette import hex_to_lab, mood_palette, palette_distance  # noqa: E402

MIN_DE = 12.0
FEELINGS = [  # sentence, voice energy 0..1
    ("I just found out my grandmother passed away", 0.2),
    ("We won the championship, I can't believe it!", 0.95),
    ("so nervous about my presentation tomorrow", 0.7),
    ("honestly just calm, slow Sunday morning", 0.15),
    ("I'm furious, my landlord kept the whole deposit", 0.9),
    ("in love, our first date went really well", 0.6),
    ("I feel lonely even in a crowded room", 0.25),
    ("scared of what my test results will say", 0.5),
]


def distinct(palettes):
    worst = min(((palette_distance(palettes[i], palettes[j]), i, j)
                 for i, j in itertools.combinations(range(len(palettes)), 2)))
    return worst


def check(label, palettes):
    d, i, j = distinct(palettes)
    print(f"{label}: closest pair is {FEELINGS[i][0][:28]!r} vs {FEELINGS[j][0][:28]!r} at {d:.1f}")
    for (text, _), p in zip(FEELINGS, palettes):
        print(f"  {text[:44]:44} {' '.join(p)}")
    assert d >= MIN_DE, f"{label}: palettes {i} and {j} are only {d:.1f} apart"


def test_rules_give_distinct_palettes():
    pals = [mood_palette(**{k: v for k, v in bs.rule_feeling(t.lower(), e).items()}, voice=e)["palette"] for t, e in FEELINGS]
    check("rules", pals)


def test_voice_makes_it_more_vivid_and_movement_brighter():
    quiet, loud = mood_palette(.3, .4, 0, 200, voice=0.1), mood_palette(.3, .4, 0, 200, voice=0.95)
    assert loud["chroma"] > quiet["chroma"]
    still, moving = mood_palette(.3, .4, 0, 200, movement=0.0), mood_palette(.3, .4, 0, 200, movement=1.0)
    assert moving["lightness"] > still["lightness"]
    contrast = lambda p: hex_to_lab(p[1])[0] - hex_to_lab(p[4])[0]   # lightest step minus deepest step
    assert contrast(moving["palette"]) > contrast(still["palette"])


def test_bad_input_still_gives_five_colors():
    for args in [(None, None, None, None, None), ("x", float("nan"), 5, "teal", "x"), (2, -2, 0, 9999, float("inf")),
                 (0, 0, 0, "#zzzzzz", "#12"), (0, 0, 0, "#808080", "#ff0000")]:
        p = mood_palette(*args, voice=None, movement="fast")["palette"]
        assert len(p) == 5 and all(c.startswith("#") and len(c) == 7 for c in p)


def test_gemini_gives_distinct_palettes():
    if bs.GEMINI is None:
        print("skipping Gemini (set BOOTH_GCP_PROJECT)")
        return
    pals, vads = [], []
    for text, energy in FEELINGS:
        d = bs.brush_direct({"feeling": text, "arousal": energy, "movement": 0.35})
        assert d["mood"]["source"] != "rules", f"Gemini did not read the feeling for {text!r}"
        pals.append(d["mood"]["palette"]); vads.append((d["mood"]["vad"], d["mood"]["hue"], d["mood"]["accent_hue"]))
    for (text, _), (vad, hue, acc) in zip(FEELINGS, vads):
        print(f"  {text[:44]:44} vad={vad} hue={hue} accent={acc}")
    check("gemini", pals)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
