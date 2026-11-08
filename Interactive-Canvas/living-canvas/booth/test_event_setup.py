#!/usr/bin/env python3
"""The operator sets up tonight's event on /setup and it goes live without a restart (issue #66).

    python3 booth/test_event_setup.py

Runs offline: a temporary events folder, a stand-in Gemini and a stand-in GPU lab. Also collectable by pytest.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import types
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import booth_server as bs  # noqa: E402

JAZZ = {"name": "Duke Jazz Night", "kind": "concert", "date": "2026-11-14",
        "context": "A student big band plays Ellington in the Chapel quad. Families on blankets, cold air, string lights.",
        "question": "Which note is still with you?",
        "scene": "an oil painting of a big band on a stone quad at night under string lights, brass glinting, visible brushstrokes",
        "voice": "Warm and plain, like a program note. Name the brass, the cold and the lights.",
        "closing": "Every listener tonight is painting this quad together. Your note is in it now."}


class Events:
    """Point the server at a copy of the two shipped events, with no saved active choice and no BOOTH_EVENT."""
    def __enter__(self):
        self.dir = tempfile.mkdtemp()
        for f in ("concert.json", "museum.json"):
            shutil.copy(os.path.join(bs.EVENTS, f), self.dir)
        self.saved = bs.EVENTS, bs.EVENT_ENV, bs._ACTIVE
        bs.EVENTS, bs.EVENT_ENV, bs._ACTIVE = self.dir, None, None
        return self

    def __exit__(self, *exc):
        bs.EVENTS, bs.EVENT_ENV, bs._ACTIVE = self.saved
        shutil.rmtree(self.dir)


class Server:
    def __enter__(self):
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), bs.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        return self

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, r.read(), r.headers["Content-Type"]

    def post(self, path, body):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def __exit__(self, *exc):
        self.srv.shutdown(); self.srv.server_close()


def fake_gemini(reply):
    """A stand-in for the Vertex client that answers every call with reply (a dict)."""
    calls = []

    def generate_content(model, contents, config):
        calls.append(contents)
        return types.SimpleNamespace(text=json.dumps(reply))
    return types.SimpleNamespace(models=types.SimpleNamespace(generate_content=generate_content)), calls


class Gemini:
    def __init__(self, client):
        self.client = client

    def __enter__(self):
        self.saved = bs.GEMINI, getattr(bs, "genai_types", None)
        bs.GEMINI, bs.genai_types = self.client, types.SimpleNamespace(GenerateContentConfig=lambda **k: k)

    def __exit__(self, *exc):
        bs.GEMINI, bs.genai_types = self.saved


# ---------------------------------------------------------------- save and go live
def test_saving_duke_jazz_night_writes_its_file_and_makes_it_active():
    with Events() as ev, Server() as s:
        code, saved = s.post("/api/event/save", JAZZ)
        assert code == 200, saved
        assert saved["id"] == "duke-jazz-night"
        with open(os.path.join(ev.dir, "duke-jazz-night.json")) as f:
            on_disk = json.load(f)
        assert on_disk["question"] == JAZZ["question"] and on_disk["voice"] == JAZZ["voice"]
        code, body, _ = s.get("/api/event")
        active = json.loads(body)
        assert active["id"] == "duke-jazz-night", active
        assert active["question"] == "Which note is still with you?"
        assert active["context"] == JAZZ["context"] and active["voice"] == JAZZ["voice"]


def test_active_event_survives_a_restart():
    with Events():
        bs.event_save(JAZZ)
        bs._ACTIVE = None                         # a restart forgets what was in memory
        assert bs.load_event()["id"] == "duke-jazz-night"


def test_booth_event_still_wins_on_restart():
    with Events():
        bs.event_save(JAZZ)
        bs._ACTIVE, bs.EVENT_ENV = None, "concert"
        assert bs.load_event()["id"] == "concert"


def test_saving_while_booth_event_is_set_still_goes_live():
    with Events():
        bs.EVENT_ENV = "concert"
        bs.event_save(JAZZ)
        assert bs.load_event()["id"] == "duke-jazz-night"


def test_resaving_concert_night_updates_concert_json_instead_of_copying_it():
    with Events() as ev:
        concert = bs.load_event("concert")
        saved = bs.event_save({**concert, "question": "What song are you still humming?"})
        assert saved["id"] == "concert"
        assert bs.load_event()["question"] == "What song are you still humming?"
        assert not os.path.exists(os.path.join(ev.dir, "concert-night.json"))


def test_save_with_an_unknown_id_uses_the_name():
    with Events():
        assert bs.event_save({**JAZZ, "id": "../museum"})["id"] == "duke-jazz-night"
        assert bs.event_save({**JAZZ, "id": "no-such-event"})["id"] == "duke-jazz-night"


def test_save_without_a_question_is_refused():
    with Events() as ev, Server() as s:
        code, body = s.post("/api/event/save", {**JAZZ, "question": "  "})
        assert code == 400, body
        assert "question" in body["error"]
        assert not os.path.exists(os.path.join(ev.dir, "duke-jazz-night.json"))


def test_save_refuses_an_unknown_kind():
    with Events():
        try:
            bs.event_save({**JAZZ, "kind": "rave"})
        except ValueError as e:
            assert "kind" in str(e)
        else:
            raise AssertionError("an unknown kind was saved")


def test_existing_events_still_load():
    with Events():
        for name in ("concert", "museum"):
            ev = bs.load_event(name)
            assert ev["id"] == name and ev["question"] and ev["scene"] and ev["closing"]


def test_events_list_names_every_event():
    with Events(), Server() as s:
        bs.event_save(JAZZ)
        code, body, _ = s.get("/api/events")
        ids = {e["id"]: e["name"] for e in json.loads(body)}
        assert ids["duke-jazz-night"] == "Duke Jazz Night" and "concert" in ids and "museum" in ids


# ---------------------------------------------------------------- draft
def test_draft_without_gemini_fills_all_four_fields():
    with Events(), Gemini(None):
        d = bs.event_draft({k: JAZZ[k] for k in ("name", "kind", "context", "date")})
        for k in ("question", "scene", "voice", "closing"):
            assert isinstance(d[k], str) and d[k].strip(), (k, d)
        assert d["source"] == "rules"
        assert "Duke Jazz Night" in d["closing"]


def test_draft_with_gemini_uses_its_writing_and_passes_the_event_as_data():
    reply = {k: JAZZ[k] for k in ("question", "scene", "voice", "closing")}
    client, calls = fake_gemini(reply)
    with Events(), Gemini(client):
        d = bs.event_draft({k: JAZZ[k] for k in ("name", "kind", "context", "date")})
    assert {k: d[k] for k in reply} == reply
    assert d["source"] != "rules"
    assert "<event>" in calls[0] and "Ellington" in calls[0]


def test_unsafe_drafted_field_falls_back_to_the_rules_line():
    reply = {"question": "How the hell are you?", "scene": JAZZ["scene"], "voice": JAZZ["voice"], "closing": JAZZ["closing"]}
    client, _ = fake_gemini(reply)
    with Events(), Gemini(client):
        d = bs.event_draft({k: JAZZ[k] for k in ("name", "kind", "context", "date")})
    assert bs.reading_is_safe(d["question"]) and d["question"] != reply["question"]
    assert d["scene"] == JAZZ["scene"]


class RateLimited(Exception):
    """Shaped like google.genai.errors.ClientError for a Vertex 429."""
    code = 429


def test_draft_retries_when_vertex_says_resource_exhausted():
    reply = {k: JAZZ[k] for k in ("question", "scene", "voice", "closing")}
    tries = []

    def generate_content(model, contents, config):
        tries.append(1)
        if len(tries) == 1:
            raise RateLimited("429 RESOURCE_EXHAUSTED. Resource exhausted. Please try again later.")
        return types.SimpleNamespace(text=json.dumps(reply))
    client = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=generate_content))
    saved = bs.DRAFT_RETRY_S
    bs.DRAFT_RETRY_S = (0, 0)
    try:
        with Events(), Gemini(client):
            d = bs.event_draft({k: JAZZ[k] for k in ("name", "kind", "context", "date")})
    finally:
        bs.DRAFT_RETRY_S = saved
    assert len(tries) == 2 and d["question"] == JAZZ["question"] and not d["source"].startswith("rules"), d


def test_draft_that_stays_rate_limited_says_why():
    def generate_content(model, contents, config):
        raise RateLimited("429 RESOURCE_EXHAUSTED")
    client = types.SimpleNamespace(models=types.SimpleNamespace(generate_content=generate_content))
    saved = bs.DRAFT_RETRY_S
    bs.DRAFT_RETRY_S = (0, 0)
    try:
        with Events(), Gemini(client):
            d = bs.event_draft({k: JAZZ[k] for k in ("name", "kind", "context", "date")})
    finally:
        bs.DRAFT_RETRY_S = saved
    assert d["source"].startswith("rules") and d["question"]
    assert "busy" in d["note"], d


def test_draft_endpoint_answers_with_gemini_off():
    with Events(), Gemini(None), Server() as s:
        code, d = s.post("/api/event/draft", {"name": "Spring Fest", "kind": "festival", "context": "", "date": ""})
        assert code == 200, d
        assert all(d[k].strip() for k in ("question", "scene", "voice", "closing")), d


# ---------------------------------------------------------------- base frame and preview
def test_two_scenes_for_one_event_get_different_base_frame_keys():
    a = {"id": "duke-jazz-night", "scene": JAZZ["scene"]}
    b = {"id": "duke-jazz-night", "scene": "an oil painting of a chapel tower above still water, visible brushstrokes"}
    assert bs.base_key(a) != bs.base_key(b)
    assert bs.base_key(a) == bs.base_key(dict(a))


def test_preview_with_the_gpu_down_explains_instead_of_failing():
    saved = bs.lab_exec, bs.FRAMES
    bs.FRAMES = tempfile.mkdtemp()
    def down(*a, **k):
        raise ConnectionRefusedError("tunnel closed")
    bs.lab_exec = down
    try:
        with Events(), Server() as s:
            code, body = s.post("/api/event/preview", {"name": JAZZ["name"], "scene": JAZZ["scene"]})
            assert code == 503, body
            assert "GPU" in body["error"]
    finally:
        shutil.rmtree(bs.FRAMES)
        bs.lab_exec, bs.FRAMES = saved


def test_setup_page_is_served():
    with Server() as s:
        code, body, ctype = s.get("/setup")
        assert code == 200 and ctype.startswith("text/html")
        assert b"/vibe/setup.js" in body


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"ok    {name}")
            except Exception as e:
                failed += 1; print(f"FAIL  {name}: {e.__class__.__name__}: {e}")
    sys.exit(1 if failed else 0)
