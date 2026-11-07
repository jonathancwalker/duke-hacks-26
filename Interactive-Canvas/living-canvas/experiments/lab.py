#!/usr/bin/env python3
"""Run an experiment on the Colab lab server.

    python3 lab.py lab/e1_art_space.py          # sends lab/00_lib.py + the experiment, saves images to runs/
    python3 lab.py --health

Connection details live in .lab.json ({"url": ..., "token": ...}), which is gitignored.
"""
import base64, json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, ".lab.json")
UA = {"User-Agent": "living-canvas-lab/0.1", "Content-Type": "application/json"}


def cfg():
    with open(CFG) as f:
        return json.load(f)


def call(path, payload=None, timeout=115):
    c = cfg()
    data = None if payload is None else json.dumps({**payload, "token": c["token"]}).encode()
    req = urllib.request.Request(c["url"].rstrip("/") + path, data=data, headers=UA, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def run(exp_path, data_path=None):
    libs = sorted(f for f in os.listdir(os.path.join(HERE, "lab")) if f[:2].isdigit() and f.endswith(".py"))
    lib = "\n\n".join(open(os.path.join(HERE, "lab", f)).read() for f in libs)   # 00_lib.py, 01_*.py, ...
    data = ""
    if data_path:   # local JSON the experiment reads as DATA (the lab can't see this machine's files)
        with open(data_path) as f:
            data = "\n\nimport json as _json\nDATA = _json.loads(" + repr(f.read()) + ")\n"
    code = lib + data + "\n\n# ---- experiment ----\n" + open(exp_path).read()
    tag = os.path.splitext(os.path.basename(exp_path))[0]
    try:
        out = call("/exec", {"code": code})
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:500]}")
    d = os.path.join(HERE, "runs", time.strftime("%m%d-%H%M%S") + "-" + tag)
    os.makedirs(d, exist_ok=True)
    for im in out["images"]:
        data = base64.b64decode(im["jpg"])
        ext = ".gif" if data[:4] == b"GIF8" else ".jpg"   # Raw() payloads come back in their own format
        with open(os.path.join(d, im["name"] + ext), "wb") as f:
            f.write(data)
    if out["stdout"].strip():
        print(out["stdout"].rstrip())
    if out["error"]:
        print("ERROR\n" + out["error"])
    print(f"-> {len(out['images'])} image(s) in {d} ({out['seconds']}s on GPU)")


if __name__ == "__main__":
    if sys.argv[1:] == ["--health"]:
        print(call("/health"))
    elif len(sys.argv) == 4 and sys.argv[2] == "--data":
        run(sys.argv[1], sys.argv[3])    # python3 lab.py lab/r4_mix.py --data lab/r4_readings.json
    else:
        run(sys.argv[1])
