"""ArtEmis thread · step 0: index Artificio/WikiArt metadata (no images) so ArtEmis paintings can be joined to images.

Reads only the text columns of the 4 parquet shards over HTTP (a few MB), writes wikiart_index.parquet to the cache.
Run: uv run --no-project --with pyarrow --with huggingface_hub --with pandas python -I artemis_00_index.py
"""
import os, re
import pandas as pd, pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

CACHE = os.environ.get("ARTEMIS_CACHE", os.path.expanduser("~/.cache/living-canvas/artemis"))
REPO = "datasets/Artificio/WikiArt"


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower().replace("'", "")).strip("-")
    return s


def main():
    fs = HfFileSystem()
    shards = sorted(p for p in fs.ls(f"{REPO}/data", detail=False) if p.endswith(".parquet"))
    rows = []
    for si, p in enumerate(shards):
        f = pq.ParquetFile(fs.open(p))
        for rg in range(f.metadata.num_row_groups):
            t = f.read_row_group(rg, columns=["title", "artist", "date", "genre", "style", "filename"]).to_pandas()
            t["shard"], t["row_group"], t["row"] = p, rg, range(len(t))
            rows.append(t)
        print(p, f.metadata.num_rows, flush=True)
    df = pd.concat(rows, ignore_index=True)
    df["artist_slug"], df["title_slug"] = df.artist.map(slug), df.title.map(slug)
    os.makedirs(CACHE, exist_ok=True)
    df.to_parquet(os.path.join(CACHE, "wikiart_index.parquet"))
    print(len(df), "rows indexed ->", CACHE)


if __name__ == "__main__":
    main()
