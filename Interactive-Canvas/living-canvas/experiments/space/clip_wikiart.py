"""Candidate A: fetch a style-stratified subset of huggan/wikiart (only the images we keep, ~0.5 MB each).

Uses the Hugging Face datasets-server /rows API for metadata, then downloads just the chosen images into
cache/wikiart/ (gitignored). No parquet shards (the full dataset is 5.3 GB).
Usage: python -I clip_wikiart.py [per_style=30]
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I drops the script dir
import json, os, random, sys, time, urllib.request
from clip_common import CACHE, UA, fetch

API = "https://datasets-server.huggingface.co"
DS = "dataset=huggan/wikiart&config=default&split=train"


def get(u, tries=6):
    for a in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90))
        except Exception as e:
            print(f"  retry ({e})", flush=True); time.sleep(20 * (a + 1))   # the API rate-limits (429): back off
    return None


def main(per_style=30, max_per_artist=14, max_unknown=60, seed=0):
    info = get(f"{API}/info?dataset=huggan/wikiart")["dataset_info"]["default"]
    feats, n = info["features"], info["splits"]["train"]["num_examples"]
    style_names, genre_names, artist_names = (feats[k]["names"] for k in ("style", "genre", "artist"))
    meta_path = os.path.join(CACHE, "wikiart_rows.json")
    rows = json.load(open(meta_path)) if os.path.exists(meta_path) else []   # resumable
    done = {r["idx"] // 100 * 100 for r in rows}
    for off in range(0, n, 100):          # all rows the datasets-server indexes (the first ~11k, sorted by artist)
        if off in done:
            continue
        r = get(f"{API}/rows?{DS}&offset={off}&length=100")
        if r is None:
            print(f"skipped offset {off}"); continue
        rows += [dict(idx=x["row_idx"], src=x["row"]["image"]["src"], style=x["row"]["style"],
                      genre=x["row"]["genre"], artist=x["row"]["artist"]) for x in r["rows"]]
        os.makedirs(CACHE, exist_ok=True)
        json.dump(rows, open(meta_path, "w"))
        print(f"metadata {len(rows)}", flush=True)
        time.sleep(3)
    rng = random.Random(seed)
    rng.shuffle(rows)
    picked, per_s, per_a = [], {}, {}
    for r in rows:
        if genre_names[r["genre"]] == "sketch_and_study":   # weak style sources for the IP-Adapter
            continue
        if per_s.get(r["style"], 0) >= per_style or per_a.get(r["artist"], 0) >= (max_unknown if r["artist"] == 0 else max_per_artist):
            continue
        per_s[r["style"]] = per_s.get(r["style"], 0) + 1; per_a[r["artist"]] = per_a.get(r["artist"], 0) + 1
        picked.append(r)
    out = []
    for i, r in enumerate(picked):
        p = os.path.join(CACHE, "wikiart", f"{r['idx']}.jpg")
        if fetch(r["src"], p, pause=0.3) is None:
            continue
        out.append(dict(idx=r["idx"], path=p, style=style_names[r["style"]], genre=genre_names[r["genre"]],
                        artist=artist_names[r["artist"]]))
        if i % 25 == 0:
            print(f"images {i}/{len(picked)}", flush=True)
    json.dump(out, open(os.path.join(CACHE, "wikiart_subset.json"), "w"), indent=1)
    print(f"kept {len(out)} images across {len(per_s)} styles, {len(per_a)} artists")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
