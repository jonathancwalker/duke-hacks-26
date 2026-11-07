"""ArtEmis thread · step 1: join ArtEmis annotations to WikiArt images, embed both with CLIP ViT-H.

Inputs:  ARTEMIS_CSV (the ArtEmis release CSV: art_style, painting, emotion, utterance, repetition)
         wikiart_index.parquet from artemis_00_index.py
Fetches only the image column of the few parquet row groups needed to reach N_PAINTINGS joined paintings.
Writes to the cache (never the repo): paintings.parquet, img_emb.pt, utts.parquet, utt_emb.pt, thumbs/.
Run: ARTEMIS_CSV=/path/artemis_dataset_release_v0.csv uv run --no-project --with torch --with transformers \
       --with pillow --with pandas --with pyarrow --with huggingface_hub python -I artemis_01_build.py
"""
import io, os, re, sys, time
import pandas as pd, pyarrow.parquet as pq, torch
from PIL import Image
from huggingface_hub import HfFileSystem

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artemis_clip as C

CACHE = os.environ.get("ARTEMIS_CACHE", os.path.expanduser("~/.cache/living-canvas/artemis"))
N_PAINTINGS = int(os.environ.get("N_PAINTINGS", 6000))
EMOTIONS = ["amusement", "awe", "contentment", "excitement", "anger", "disgust", "fear", "sadness", "something else"]


def strip_tail(s):
    """WikiArt slugs often end in a year or a duplicate counter: the-starry-night-1889, portrait-1."""
    return re.sub(r"(-\d{1,4})+$", "", s)


def join(art, idx):
    art = art.copy()
    art["artist_slug"] = art.painting.str.split("_", n=1).str[0]
    art["title_key"] = art.painting.str.split("_", n=1).str[1].fillna("").map(strip_tail)
    idx = idx.copy()
    idx["title_key"] = idx.title_slug.map(strip_tail)
    idx = idx.drop_duplicates(["artist_slug", "title_key"], keep=False)  # ambiguous titles out
    pk = art.drop_duplicates("painting")[["painting", "art_style", "artist_slug", "title_key"]]
    pk = pk.drop_duplicates(["artist_slug", "title_key"], keep=False)
    return pk.merge(idx, on=["artist_slug", "title_key"], how="inner")


def main():
    art = pd.read_csv(os.environ["ARTEMIS_CSV"])
    art = art[art.emotion.isin(EMOTIONS) & art.utterance.notna()]
    idx = pd.read_parquet(os.path.join(CACHE, "wikiart_index.parquet"))
    j = join(art, idx)
    print(f"ArtEmis: {len(art)} annotations on {art.painting.nunique()} paintings; joined to WikiArt images: {len(j)}")
    # Take whole row groups, densest first, until we have enough paintings: keeps the image download small.
    rg = j.groupby(["shard", "row_group"]).size().sort_values(ascending=False)
    keep, n = [], 0
    for key, c in rg.items():
        keep.append(key); n += c
        if n >= N_PAINTINGS:
            break
    j = j.set_index(["shard", "row_group"]).loc[keep].reset_index()
    print(f"using {len(keep)} row groups -> {len(j)} paintings")

    fs, imgs, rows = HfFileSystem(), [], []
    os.makedirs(os.path.join(CACHE, "thumbs"), exist_ok=True)
    t0 = time.time()
    for (shard, g), sub in j.groupby(["shard", "row_group"]):
        col = pq.ParquetFile(fs.open(shard)).read_row_group(g, columns=["image"]).column("image").to_pylist()
        for _, r in sub.iterrows():
            im = Image.open(io.BytesIO(col[r.row]["bytes"])).convert("RGB")
            th = im.copy(); th.thumbnail((160, 160)); th.save(os.path.join(CACHE, "thumbs", f"{r.painting}.jpg"), quality=85)
            imgs.append(im); rows.append(r)
        print(f"  {shard.split('/')[-1][:14]} rg{g}: {len(imgs)} images, {time.time() - t0:.0f}s", flush=True)
    P = pd.DataFrame(rows).reset_index(drop=True)
    P["size"] = [f"{im.width}x{im.height}" for im in imgs]
    E = C.image(imgs)
    print("image embeds", tuple(E.shape), f"{time.time() - t0:.0f}s")

    U = art[art.painting.isin(set(P.painting))][["painting", "emotion", "utterance"]].reset_index(drop=True)
    U["p"] = U.painting.map({p: i for i, p in enumerate(P.painting)})
    UE = C.text(U.utterance.tolist())
    print("utterance embeds", tuple(UE.shape), f"{time.time() - t0:.0f}s")

    P[["painting", "art_style", "title", "artist", "date", "genre", "style", "size"]].to_parquet(os.path.join(CACHE, "paintings.parquet"))
    U.to_parquet(os.path.join(CACHE, "utts.parquet"))
    torch.save(E.half(), os.path.join(CACHE, "img_emb.pt")); torch.save(UE.half(), os.path.join(CACHE, "utt_emb.pt"))
    print("saved ->", CACHE)


if __name__ == "__main__":
    main()
