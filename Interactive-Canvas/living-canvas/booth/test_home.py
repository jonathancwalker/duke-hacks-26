#!/usr/bin/env python3
"""The station (/vibe) is the booth's home page; the first booth page moved to /booth.

    python3 booth/test_home.py

Runs offline against the real request handler. Also collectable by pytest.
"""
import http.client
import os
import sys
import threading
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402


def get(path):
    """GET path from a throwaway server; redirects are not followed, so a 302 shows as a 302."""
    srv = ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
        c.request("GET", path)
        r = c.getresponse()
        return r.status, r.getheader("Location"), r.read()
    finally:
        srv.shutdown()


def test_bare_address_opens_the_station():
    status, where, _ = get("/")
    assert (status, where) == (302, "/vibe"), (status, where)


def test_bare_address_keeps_the_query_for_the_station():
    status, where, _ = get("/?event=concert")
    assert (status, where) == (302, "/vibe?event=concert"), (status, where)


def test_first_booth_page_still_reachable_at_booth():
    status, _, body = get("/booth")
    assert status == 200 and b"<html" in body.lower(), status


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok -", name)
