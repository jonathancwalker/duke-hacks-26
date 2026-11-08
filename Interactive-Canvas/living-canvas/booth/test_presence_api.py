#!/usr/bin/env python3
"""POST /api/presence (issue #7) and rendering its paintings, which are outside the lab's 36-painting library.

    python3 booth/test_presence_api.py

Offline: the scorer and the GPU lab are replaced by fakes. Also collectable by pytest.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402

VEC = [0.01] * 1024


class FakePresence:
    def __init__(self):
        self.calls = []

    def __call__(self, text, loudness, movement):
        self.calls.append((text, loudness, movement))
        return {"artists": [{"name": "a-painter_a-painting", "weight": 0.6, "label": "A Painter, A Painting"},
                            {"name": "b-painter_b-painting", "weight": 0.4, "label": "B Painter, B Painting"}],
                "vectors": {"a-painter_a-painting": VEC, "b-painter_b-painting": VEC},
                "read": {"source": "head", "emotions": {"sadness": 1.0}}}


def test_presence_takes_words_loudness_and_movement():
    fake = FakePresence()
    bs.PRESENCE = fake
    out = bs.presence_api({"feeling": "  My grandmother passed away last month. ", "loudness": 0.2, "movement": 0.1})
    assert fake.calls == [("My grandmother passed away last month.", 0.2, 0.1)]
    assert [a["name"] for a in out["artists"]] == ["a-painter_a-painting", "b-painter_b-painting"]
    assert set(out["vectors"]) == {"a-painter_a-painting", "b-painter_b-painting"}


def test_presence_clamps_inputs_and_reads_arousal_as_loudness():
    fake = FakePresence()
    bs.PRESENCE = fake
    bs.presence_api({"feeling": "We won!", "arousal": 3, "movement": -1})
    assert fake.calls[-1] == ("We won!", 1.0, 0.0)


def test_presence_unavailable_is_a_clear_error():
    bs.PRESENCE = None
    bs.PRESENCE_ERROR = "presence library not built"
    try:
        bs.presence_api({"feeling": "hi"})
    except bs.PresenceUnavailable as e:
        assert "not built" in str(e)
    else:
        raise AssertionError("expected PresenceUnavailable")


def test_health_says_whether_the_presence_scorer_is_ready():
    bs.PRESENCE, bs.PRESENCE_ERROR = None, "FileNotFoundError: presence_library.npz (build it with presence/build.py)"
    assert bs.presence_status() == "unavailable: FileNotFoundError: presence_library.npz (build it with presence/build.py)"
    bs.PRESENCE = FakePresence()
    assert bs.presence_status() == "ready"


def _capture_render(v):
    seen = {}
    orig = bs.lab_frame
    bs.lab_frame = lambda code, keys, fallbacks: seen.update(code=code, keys=keys) or {"image": "data:image/jpeg;base64,"}
    try:
        bs.vibe_render(v)
    finally:
        bs.lab_frame = orig
    return seen


def test_render_takes_presence_paintings_by_their_vectors():
    seen = _capture_render({"artists": [{"name": "a-painter_a-painting", "weight": 0.6}, {"name": "Monet, Water Lilies (1906)", "weight": 0.4}],
                            "vectors": {"a-painter_a-painting": VEC, "not-in-the-mix": VEC}})
    code = seen["code"]
    assert "def mix_vector(weights)" in code and "_EXT" in code
    assert code.index("def mix_vector") < code.index("vibe_frame(")
    assert "a-painter_a-painting" in code.split("vibe_frame(")[0]
    assert "not-in-the-mix" not in code                       # only paintings in the mix are sent


def test_render_without_vectors_is_unchanged():
    code = _capture_render({"artists": [{"name": "Monet, Water Lilies (1906)", "weight": 1.0}]})["code"]
    assert "_EXT" not in code and code.startswith("show(vibe_frame(")


def test_render_rejects_vectors_that_are_not_1024_numbers():
    for bad in ([0.1] * 10, ["0.1"] * 1024, [float("nan")] * 1024, "__import__('os')"):
        try:
            _capture_render({"artists": [{"name": "x", "weight": 1}], "vectors": {"x": bad}})
        except ValueError:
            continue
        raise AssertionError(f"accepted a bad vector: {str(bad)[:40]}")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("presence api: ok")
