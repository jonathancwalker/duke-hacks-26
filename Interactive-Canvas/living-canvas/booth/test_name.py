#!/usr/bin/env python3
"""Optional name per visit (issue #30): the saved visit credits the visitor's name, or "Visitor N".

    python3 booth/test_name.py

Runs offline against a temporary visits folder. Also collectable by pytest.
"""
import json
import os
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402
from test_gallery import JPEG, Tonight  # noqa: E402


def saved(vid):
    with open(os.path.join(bs.TONIGHT, f"{vid}.json")) as f:
        return json.load(f)


def test_credit_name():
    assert bs.credit_name("Rachel Chen", 23) == "Rachel Chen"
    assert bs.credit_name("", 23) == "Visitor 23"
    assert bs.credit_name(None, 23) == "Visitor 23"
    assert bs.credit_name("   ", 23) == "Visitor 23"


def test_offensive_name_falls_back_to_visitor_n():
    assert bs.credit_name("Dumb Ass", 7) == "Visitor 7"
    assert bs.credit_name("sh1t head", 7) == "Visitor 7"


def test_name_is_capped_and_single_line():
    n = bs.credit_name("A" * 80, 1)
    assert len(n) <= bs.NAME_MAX, n
    assert bs.credit_name("Ada\nLovelace", 1) == "Ada Lovelace"


def test_skipped_visit_23_is_saved_as_visitor_23():
    with Tonight():
        for _ in range(22):
            bs.visit_save({"name": "Someone"})
        assert bs.visit_save({"name": None}) == {"id": "0023"}
        assert saved("0023")["name"] == "Visitor 23"


def test_spoken_name_is_saved():
    with Tonight():
        bs.visit_save({"name": "Rachel Chen"})
        assert saved("0001")["name"] == "Rachel Chen"


def test_gallery_credits_the_latest_name():
    with Tonight():
        assert bs.gallery_state()["name"] is None
        bs.visit_save({"name": "Rachel Chen", "canvas": JPEG})
        assert bs.gallery_state()["name"] == "Rachel Chen"
        bs.visit_save({"canvas": JPEG})
        assert bs.gallery_state()["name"] == "Visitor 2"


def test_name_round_trips_over_http():
    with Tonight():
        srv = ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            req = urllib.request.Request(base + "/api/visits", json.dumps({"name": "Ada", "canvas": JPEG}).encode(),
                                         {"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as r:
                assert json.load(r) == {"id": "0001"}
            with urllib.request.urlopen(base + "/api/gallery") as r:
                assert json.load(r)["name"] == "Ada"
            with urllib.request.urlopen(base + "/api/visits") as r:
                assert json.load(r)[0]["name"] == "Ada"
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
