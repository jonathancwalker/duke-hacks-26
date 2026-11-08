#!/usr/bin/env python3
"""The projector gallery shows tonight's latest shared canvas (issue #26).

    python3 booth/test_gallery.py

Runs offline against a temporary visits folder. Also collectable by pytest.
"""
import base64
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

# JPEG start/end markers are enough: the gallery only needs the file to exist, not to decode.
JPEG = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xd9").decode()


def shown(state):
    """The state with the canvas URL's cache-busting version dropped, for comparing."""
    return {**state, "canvas": state["canvas"] and state["canvas"].split("?v=")[0]}


class Tonight:
    """Point the server at an empty visits folder for the duration of a test."""
    def __enter__(self):
        self.dir, self.saved = tempfile.mkdtemp(), (bs.VISITS, bs.TONIGHT)
        bs.VISITS, bs.TONIGHT = self.dir, os.path.join(self.dir, "current")
        return self

    def __exit__(self, *exc):
        bs.VISITS, bs.TONIGHT = self.saved
        shutil.rmtree(self.dir)


def test_empty_night_has_no_canvas():
    with Tonight():
        assert bs.gallery_state() == {"visits": 0, "id": None, "canvas": None, "name": None}


def test_one_saved_visit_shows_canvas_0001():
    with Tonight():
        bs.visit_save({"reading": "quiet hope", "canvas": JPEG, "mood": JPEG})
        assert shown(bs.gallery_state()) == {"visits": 1, "id": "0001", "canvas": "/visits/0001-canvas.jpg", "name": "Visitor 1"}


def test_latest_visit_wins():
    with Tonight():
        for _ in range(3):
            bs.visit_save({"canvas": JPEG})
        assert shown(bs.gallery_state()) == {"visits": 3, "id": "0003", "canvas": "/visits/0003-canvas.jpg", "name": "Visitor 3"}


def test_visit_without_canvas_keeps_the_last_canvas():
    with Tonight():
        bs.visit_save({"canvas": JPEG})
        bs.visit_save({"reading": "no image saved"})
        assert shown(bs.gallery_state()) == {"visits": 2, "id": "0001", "canvas": "/visits/0001-canvas.jpg", "name": "Visitor 2"}


def test_new_night_clears_the_gallery():
    with Tonight():
        bs.visit_save({"canvas": JPEG})
        bs.visits_clear()
        assert bs.gallery_state() == {"visits": 0, "id": None, "canvas": None, "name": None}


def test_new_nights_0001_gets_a_new_url():
    """Ids restart at 0001 after Reset, so the URL must change or the projector shows last night's cached canvas."""
    with Tonight():
        bs.visit_save({"canvas": JPEG})
        first = bs.gallery_state()["canvas"]
        bs.visits_clear()
        bs.visit_save({"canvas": JPEG})
        os.utime(os.path.join(bs.TONIGHT, "0001-canvas.jpg"), ns=(1, 1))   # a different write time than the first
        assert bs.gallery_state()["canvas"] != first


def test_gallery_page_and_state_are_served():
    with Tonight():
        bs.visit_save({"canvas": JPEG})
        srv = ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            with urllib.request.urlopen(base + "/gallery") as r:
                assert r.headers["Content-Type"].startswith("text/html")
                assert b"/vibe/gallery.js" in r.read()
            with urllib.request.urlopen(base + "/api/gallery") as r:
                canvas = json.load(r)["canvas"]
                assert canvas.startswith("/visits/0001-canvas.jpg?v="), canvas
            with urllib.request.urlopen(base + canvas) as r:
                assert r.read()[:2] == b"\xff\xd8"
        finally:
            srv.shutdown(); srv.server_close()


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"ok    {name}")
            except Exception as e:
                failed += 1; print(f"FAIL  {name}: {e.__class__.__name__}: {e}")
    sys.exit(1 if failed else 0)
