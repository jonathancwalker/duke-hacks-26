#!/usr/bin/env python3
"""The station shows a privacy notice, and a saved visit never holds the visitor's words (issue #35).

    python3 booth/test_consent.py

Offline: no GPU lab or Gemini needed. Also collectable by pytest.
"""
import glob
import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402


def get_json(path):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{srv.server_port}{path}", timeout=5) as r:
            return json.load(r)
    finally:
        srv.shutdown(); srv.server_close()


def test_concert_event_api_returns_consent_text():
    ev = get_json("/api/event?event=concert")
    assert isinstance(ev.get("consent"), str) and ev["consent"].strip(), f"no consent text in {ev}"


def test_every_event_has_consent_text():
    for path in glob.glob(os.path.join(bs.EVENTS, "*.json")):
        name = os.path.basename(path)[:-5]
        assert bs.load_event(name)["consent"].strip(), f"events/{name}.json has no consent text"


def test_consent_lines_join_into_one_string():
    tmp = tempfile.mkdtemp()
    saved = bs.EVENTS
    try:
        ev = {"name": "T", "kind": "t", "question": "q?", "scene": "s", "closing": "c", "consent": ["Line one.", "Line two."]}
        with open(os.path.join(tmp, "t.json"), "w") as f:
            json.dump(ev, f)
        bs.EVENTS = tmp
        assert bs.load_event("t")["consent"] == "Line one.\nLine two."
    finally:
        bs.EVENTS = saved; shutil.rmtree(tmp)


def test_event_without_consent_is_rejected():
    tmp = tempfile.mkdtemp()
    saved = bs.EVENTS
    try:
        with open(os.path.join(tmp, "bare.json"), "w") as f:
            json.dump({"name": "B", "kind": "b", "question": "q?", "scene": "s", "closing": "c"}, f)
        bs.EVENTS = tmp
        try:
            bs.load_event("bare")
        except ValueError as e:
            assert "consent" in str(e)
        else:
            raise AssertionError("an event with no consent text loaded")
    finally:
        bs.EVENTS = saved; shutil.rmtree(tmp)


def test_saved_visit_keeps_no_words():
    tmp = tempfile.mkdtemp()
    saved = bs.TONIGHT
    words = "I just found out my grandmother passed away"
    try:
        bs.TONIGHT = tmp
        vid = bs.visit_save({"feeling": words, "transcript": words, "heard": {"feeling": words},
                             "reading": "grief, soft and slow", "painters": [], "start": "chapel",
                             "strokes": [[{"x": 1.0, "y": 2.0}]]})["id"]
        with open(os.path.join(tmp, f"{vid}.json")) as f:
            raw = f.read()
        rec = json.loads(raw)
        assert not {"feeling", "transcript", "heard", "words"} & rec.keys(), f"word fields saved: {sorted(rec)}"
        assert "grandmother" not in raw, "the visitor's words reached disk"
    finally:
        bs.TONIGHT = saved; shutil.rmtree(tmp)


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"ok    {name}")
            except Exception as e:
                failed += 1; print(f"FAIL  {name}: {e.__class__.__name__}: {e}")
    sys.exit(1 if failed else 0)
