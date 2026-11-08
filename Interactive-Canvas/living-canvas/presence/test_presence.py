"""Presence scorer (issue #7): a visitor's words, voice loudness and movement -> 3 painting weights.

    uv run --no-project --with pytest,torch,transformers,numpy python -I -m pytest presence -q -s

The first block needs no data. The second needs the built library (presence/build.py; skipped when it is missing).
The C5b regression also needs the eval board's out/ dir in PRESENCE_EVAL_OUT (skipped when unset).
"""
import json
import math
import os
import re
import statistics
import sys
import time

import numpy as np
import pytest

LC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LC)
from presence import scorer as P  # noqa: E402

EMO = P.EMO
IDX = {e: i for i, e in enumerate(EMO)}


def dist(**kw):
    p = np.zeros(len(EMO))
    for k, v in kw.items():
        p[IDX[k.replace("_", " ")]] = v
    return p / p.sum()


# ---------------------------------------------------------------- pure parts
def test_drop_something_else_renormalises():
    p = P.drop_something_else(dist(sadness=0.6, something_else=0.4))
    assert p[IDX["something else"]] == 0
    assert p[IDX["sadness"]] == pytest.approx(1.0)


def test_steer_at_neutral_arousal_changes_nothing():
    p = P.drop_something_else(dist(excitement=0.3, contentment=0.3, sadness=0.4))
    assert P.steer(p, 0.5, strength=2.0) == pytest.approx(p)


def test_loud_steer_multiplies_high_arousal_by_exp_and_scales_with_clarity():
    p = P.drop_something_else(dist(excitement=0.5, contentment=0.5))
    clear = P.clarity(p)
    q = P.steer(p, 1.0, strength=2.0)
    # excitement x exp(2 * 0.5 * clarity), contentment x its inverse, then renormalised
    s = math.exp(2.0 * 0.5 * clear)
    assert q[IDX["excitement"]] / q[IDX["contentment"]] == pytest.approx(s * s)
    assert 0 < clear < 1


def test_clarity_is_one_for_a_single_emotion_and_zero_for_flat():
    assert P.clarity(dist(sadness=1)) == pytest.approx(1.0)
    flat = P.drop_something_else(np.ones(len(EMO)))
    assert P.clarity(flat) == pytest.approx(0.0, abs=1e-6)


def test_mix_is_top_k_softmax_of_z_scores():
    row = np.array([0.0, 3.0, 1.0, 2.0, -1.0])
    top, w = P.mix_from_scores(row, k=3)
    assert list(top) == [1, 3, 2]
    z = (row - row.mean()) / (row.std() + 1e-9)
    e = np.exp(z[[1, 3, 2]] - z[1])
    assert w == pytest.approx(e / e.sum())


def test_config_defaults_live_in_the_config_file():
    cfg = P.load_config()
    assert cfg["lambda"] == 1.0
    assert cfg["votes"]["min"] == 6
    assert cfg["steer"] == 2.0


def test_blend_uses_gemini_half_and_half_when_it_is_there():
    head, gem = dist(sadness=1), dist(fear=1)
    assert P.blend(head, None, 0.5) == pytest.approx(head)
    assert P.blend(head, gem, 0.5) == pytest.approx(0.5 * head + 0.5 * gem)


# ---------------------------------------------------------------- with the built library
@pytest.fixture(scope="module")
def lib():
    try:
        return P.Library.load(P.load_config())
    except FileNotFoundError as e:
        pytest.skip(f"presence library not built: {e}")


def names(res):
    return [a["name"] for a in res["artists"]]


def test_returns_three_weights_with_their_clip_vectors(lib):
    res = lib.score("I feel peaceful and slow tonight.", 0.2, 0.1)
    assert len(res["artists"]) == 3
    assert sum(a["weight"] for a in res["artists"]) == pytest.approx(1.0, abs=0.01)
    for a in res["artists"]:
        v = res["vectors"][a["name"]]
        assert len(v) == 1024 and all(isinstance(x, float) for x in v)


def test_grief_and_triumph_land_on_different_paintings(lib):
    grief = lib.score("My grandmother passed away last month.", 0.2, 0.1)
    won = lib.score("We won! We actually won the championship!", 0.9, 0.9)
    assert not set(names(grief)) & set(names(won)), (names(grief), names(won))
    assert max(grief["read"]["emotions"], key=grief["read"]["emotions"].get) == "sadness"
    assert max(won["read"]["emotions"], key=won["read"]["emotions"].get) == "excitement"


def test_first_snow_picks_a_snow_painting(lib):
    res = lib.score("First snow of the year on the walk here.", 0.3, 0.2)
    titles = [a["title"] for a in res["artists"]]
    assert any(re.search(r"snow|winter", t, re.I) for t in titles), titles


def test_head_only_answer_is_under_300_ms(lib):
    texts = ["My grandmother passed away last month.", "We won! We actually won the championship!",
             "First snow of the year on the walk here.", "I'm nervous about my exams next week.",
             "I'm furious about how things are going.", "I feel peaceful and slow tonight."]
    lib.score("warm up", 0.5, 0.5)
    ms = []
    for i in range(36):
        t0 = time.perf_counter()
        lib.score(texts[i % len(texts)] + " " * (i // len(texts)), (i % 10) / 10, (i % 7) / 7)
        ms.append(1000 * (time.perf_counter() - t0))
    p50, p95 = statistics.median(ms), sorted(ms)[int(0.95 * len(ms)) - 1]
    print(f"\npresence head-only latency over {len(ms)} calls: p50 {p50:.1f} ms, p95 {p95:.1f} ms")
    assert p95 < 300


EVAL_OUT = os.environ.get("PRESENCE_EVAL_OUT")


@pytest.mark.skipif(not EVAL_OUT, reason="set PRESENCE_EVAL_OUT to the eval board's out/ dir")
def test_picks_match_the_eval_board_c5b(lib):
    """Same config as C5b (6-vote floor, lambda 1), same Gemini reads: the same three paintings and weights."""
    board = json.load(open(os.path.join(EVAL_OUT, "outputs", "C5b.json")))
    gem = json.load(open(os.path.join(EVAL_OUT, "gemini_emotions.json")))
    cases = {c["id"]: c for c in json.load(open(os.path.join(EVAL_OUT, "..", "cases.json")))["cases"]}
    assert lib.cfg["votes"] == {"min": 6, "soft_k": 0} and lib.cfg["lambda"] == 1.0
    for row in board["rows"]:
        c = cases[row["case"]]
        res = lib.score(c["text"], c["loudness"], c["movement"], gemini=np.array(gem[c["text"]]))
        assert names(res) == list(row["weights"]), (c["id"], names(res), list(row["weights"]))
        assert [a["weight"] for a in res["artists"]] == pytest.approx(list(row["weights"].values()), abs=0.002)


# ---------------------------------------------------------------- Gemini refines in the background
def test_gemini_read_refines_later_calls_without_blocking_the_first(lib):
    calls = []

    def slow_gemini(text):
        calls.append(text); time.sleep(0.5)
        return dist(sadness=1).tolist()

    pres = P.Presence(lib, gemini=slow_gemini)
    t0 = time.perf_counter()
    first = pres("My grandmother passed away last month.", 0.2, 0.1)
    assert time.perf_counter() - t0 < 0.3 and first["read"]["source"] == "head"
    later = pres("My grandmother passed away last month.", 0.2, 0.1, wait_s=2.0)
    assert later["read"]["source"] == "head+gemini"
    assert calls == ["My grandmother passed away last month."]      # one Gemini call per sentence
