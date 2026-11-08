#!/usr/bin/env python3
"""The line after each visit (issue #67) and the montage's closing reflection (issue #34).

    python3 booth/test_writing.py               # offline: Gemini is stubbed
    BOOTH_GCP_PROJECT=<id> python3 booth/test_writing.py --live   # also prints real lines and a reflection

Also collectable by pytest.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import types
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402

MUSEUM_CLOSING = "Every visitor tonight has painted a little of this chapel. Yours is in there now."


class Gemini:
    """Stand in for the Gemini client: reply(prompt, system) -> text (or raises). Records what it was asked."""
    def __init__(self, reply):
        self.reply, self.asked = reply, []

    def __enter__(self):
        def generate_content(model, contents, config):
            self.asked.append((contents, config["system_instruction"]))
            return types.SimpleNamespace(text=self.reply(contents, config["system_instruction"]))
        self.saved = bs.GEMINI, getattr(bs, "genai_types", None)
        bs.GEMINI = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=generate_content))
        bs.genai_types = types.SimpleNamespace(GenerateContentConfig=lambda **k: k)
        return self

    def __exit__(self, *exc):
        bs.GEMINI, bs.genai_types = self.saved


class NoGemini:
    def __enter__(self):
        self.saved, bs.GEMINI = bs.GEMINI, None

    def __exit__(self, *exc):
        bs.GEMINI = self.saved


class Tonight:
    """Point the server at an empty visits folder for the duration of a test."""
    def __enter__(self):
        self.dir, self.saved = tempfile.mkdtemp(), (bs.VISITS, bs.TONIGHT)
        bs.VISITS, bs.TONIGHT = self.dir, os.path.join(self.dir, "current")
        return self

    def __exit__(self, *exc):
        bs.VISITS, bs.TONIGHT = self.saved
        shutil.rmtree(self.dir)


# ---------------------------------------------------------------- the line after each visit (#67)
def test_no_gemini_shows_the_events_fixed_line():
    with NoGemini():
        assert bs.visit_line({"event": "museum", "reading": "quiet hope after a hard week", "before": 22})["line"] == MUSEUM_CLOSING


def test_unsafe_sentence_falls_back_to_the_fixed_line():
    with Gemini(lambda *_: "Twenty-two people painted before you, you damn legend."):
        assert bs.visit_line({"event": "museum", "reading": "joy", "before": 22})["line"] == MUSEUM_CLOSING


def test_sappy_words_fall_back_to_the_fixed_line():
    with Gemini(lambda *_: "Your beautiful soul is now woven into the chapel's tapestry."):
        assert bs.visit_line({"event": "museum", "reading": "joy", "before": 3})["line"] == MUSEUM_CLOSING


def test_line_is_never_more_than_one_sentence():
    two = "Twenty-two people painted before you; your stillness is part of their chapel now. The night goes on."
    with Gemini(lambda *_: two):
        line = bs.visit_line({"event": "museum", "reading": "stillness", "before": 22})["line"]
    assert line == "Twenty-two people painted before you; your stillness is part of their chapel now.", line


def test_exclamation_is_calmed_to_a_full_stop():
    with Gemini(lambda *_: "\"Nine people painted before you, and now the stage holds your joy too!\""):
        line = bs.visit_line({"event": "concert", "reading": "joy", "before": 9})["line"]
    assert line == "Nine people painted before you, and now the stage holds your joy too.", line


def test_model_error_or_silence_falls_back():
    def boom(*_):
        raise RuntimeError("quota")
    for reply in (boom, lambda *_: "", lambda *_: None):
        with Gemini(reply):
            assert bs.visit_line({"event": "museum", "reading": "x", "before": 1})["line"] == MUSEUM_CLOSING


def test_slow_model_falls_back_within_the_timeout():
    saved, bs.LINE_TIMEOUT_S = bs.LINE_TIMEOUT_S, 0.2
    try:
        with Gemini(lambda *_: (time.sleep(1), "Too late for this visitor.")[1]):
            t0 = time.time()
            out = bs.visit_line({"event": "museum", "reading": "x", "before": 1})
            assert out["line"] == MUSEUM_CLOSING and time.time() - t0 < 0.8, (out, time.time() - t0)
    finally:
        bs.LINE_TIMEOUT_S = saved


def test_prompt_carries_event_reading_and_count():
    with Gemini(lambda *_: "Twenty-two people painted before you; your stillness is part of their chapel now.") as g:
        out = bs.visit_line({"event": "museum", "reading": "a quiet pause held in gentle suspension", "before": 22})
    assert out["line"].startswith("Twenty-two"), out
    prompt, system = g.asked[0]
    for want in ("Duke Chapel Night", "gothic chapel tower", "a quiet pause held in gentle suspension", "22"):
        assert want in prompt, (want, prompt)
    assert "<visit>" in prompt and "data" in system


def test_event_context_and_voice_are_used_when_present():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "jazz.json"), "w") as f:
        json.dump({"name": "Jazz on the Quad", "kind": "concert", "question": "How did that set land?",
                   "scene": "an oil painting of a big band under string lights", "closing": "The quad is yours now.",
                   "context": "A student big band plays Ellington in the Chapel quad.",
                   "voice": "Warm and plain, like a program note."}, f)
    saved, bs.EVENTS = bs.EVENTS, d
    try:
        with Gemini(lambda *_: "Forty people painted before you; the quad keeps your warmth now.") as g:
            bs.visit_line({"event": "jazz", "reading": "warmth", "before": 40})
        prompt, system = g.asked[0]
        assert "plays Ellington" in prompt and "like a program note" in prompt, prompt
        with NoGemini():
            assert bs.visit_line({"event": "jazz", "reading": "warmth", "before": 40})["line"] == "The quad is yours now."
    finally:
        bs.EVENTS = saved
        shutil.rmtree(d)


def test_visitor_reading_cannot_be_unbounded():
    with Gemini(lambda *_: "One person painted before you; the chapel holds you both now.") as g:
        bs.visit_line({"event": "museum", "reading": "x" * 5000, "before": "lots"})
    prompt = g.asked[0][0]
    assert "x" * 200 not in prompt and "painted before them: 0" in prompt, prompt


# ---------------------------------------------------------------- the closing reflection (#34)
def test_no_gemini_reflection_is_the_count():
    with Tonight(), NoGemini():
        for i in range(84):
            bs.visit_save({"reading": f"mood {i}"})
        assert bs.reflection({"event": "museum"}) == {"reflection": "84 visitors. One painting.", "visitors": 84,
                                                       "source": "fallback"}


def test_one_visitor_reflection_is_singular():
    with Tonight(), NoGemini():
        bs.visit_save({"reading": "joy"})
        assert bs.reflection({"event": "museum"})["reflection"] == "1 visitor. One painting."


def test_reflection_reads_every_reading_of_the_night():
    readings = ["quiet hope after a hard week", "frustration burning hot and fast", "", "joy that will not sit still"]
    reply = "Four people gave the chapel a piece of their evening; none of it belongs to any one of them now."
    with Tonight(), Gemini(lambda *_: reply) as g:
        for r in readings:
            bs.visit_save({"reading": r})
        out = bs.reflection({"event": "museum"})
    assert out == {"reflection": reply, "visitors": 4, "source": bs.WRITING_MODEL}, out
    prompt = g.asked[0][0]
    for r in filter(None, readings):
        assert r in prompt, (r, prompt)
    assert "visitors tonight: 4" in prompt and "<readings>" in prompt


def test_reflection_keeps_at_most_two_sentences_and_stays_safe():
    with Tonight():
        for _ in range(3):
            bs.visit_save({"reading": "calm"})
        with Gemini(lambda *_: "Three people came. They painted one chapel. Then they went home."):
            assert bs.reflection({"event": "museum"})["reflection"] == "Three people came. They painted one chapel."
        with Gemini(lambda *_: "Three idiots painted a chapel."):
            assert bs.reflection({"event": "museum"})["reflection"] == "3 visitors. One painting."


def test_no_visits_reflection_has_nothing_to_say():
    with Tonight(), Gemini(lambda *_: "Nobody came.") as g:
        assert bs.reflection({"event": "museum"}) == {"reflection": "", "visitors": 0, "source": "fallback"}
    assert not g.asked


# ---------------------------------------------------------------- HTTP
def test_endpoints_are_served():
    with Tonight(), NoGemini():
        bs.visit_save({"reading": "joy"})
        srv = ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        def post(path, body):
            req = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        try:
            assert post("/api/line", {"reading": "joy", "before": 0})["line"] == bs.load_event()["closing"]
            assert post("/api/line", {"event": "concert", "reading": "joy", "before": 0})["line"].startswith("The whole crowd")
            assert post("/api/reflection", {"event": "museum"})["reflection"] == "1 visitor. One painting."
        finally:
            srv.shutdown(); srv.server_close()


# ---------------------------------------------------------------- live voice check
LIVE_VISITS = [("museum", "a quiet pause held in gentle suspension", 22),
               ("museum", "frustration burning hot and fast", 5),
               ("concert", "joy that will not sit still", 41),
               ("concert", "grief carried gently into the light", 13),
               ("museum", "nervous energy before something new", 0)]


def live_check():
    for ev, reading, before in LIVE_VISITS:
        out = bs.visit_line({"event": ev, "reading": reading, "before": before})
        print(f"  [{ev}, {before} before] {reading!r}\n      -> {out['line']}  ({out['source']})")
    with Tonight():
        for _, reading, _ in LIVE_VISITS * 4 + [("", "a long night, finally letting go", 0)] * 3:
            bs.visit_save({"reading": reading})
        out = bs.reflection({"event": "museum"})
    print(f"  reflection ({out['visitors']} visitors): {out['reflection']}  ({out['source']})")


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"ok    {name}")
            except Exception as e:
                failed += 1; print(f"FAIL  {name}: {e.__class__.__name__}: {e}")
    if "--live" in sys.argv:
        live_check() if bs.GEMINI is not None else print("live check skipped: no Gemini client (set BOOTH_GCP_PROJECT)")
    sys.exit(1 if failed else 0)
