"""ArtEmis thread · step 3: board of top-3 picks for 12 feelings, baseline vs the chosen designs (split 0 library).

Run: uv run --no-project --with pillow python -I artemis_03_board.py [design ...]   (default: A-emo+clip A-human8)
Writes out/artemis_board.png (small JPEG-quality PNG, thumbnails only).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("ARTEMIS_CACHE", os.path.expanduser("~/.cache/living-canvas/artemis"))
FEELINGS = ["grief", "triumph", "calm", "rage", "anxious", "love", "lonely", "hope", "wonder", "excited", "fear", "playful"]
T = 80  # thumbnail cell


def thumb(p):
    im = Image.open(os.path.join(CACHE, "thumbs", f"{p}.jpg")).convert("RGB")
    im.thumbnail((T, T))
    cell = Image.new("RGB", (T, T), (245, 245, 245))
    cell.paste(im, ((T - im.width) // 2, (T - im.height) // 2))
    return cell


def main():
    designs = sys.argv[1:] or ["A-emo+clip", "A-human8"]
    R = json.load(open(os.path.join(HERE, "out", "artemis_results.json")))
    cols = ["baseline"] + designs
    lw, gap, head = 90, 14, 22
    W = lw + len(cols) * (3 * T) + gap * (len(cols) - 1)
    H = head + len(FEELINGS) * T
    board = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    for c, name in enumerate(cols):
        x0 = lw + c * (3 * T + gap)
        d.text((x0 + 4, 5), f"{name} (library {R['n_library']})", fill="black", font=font)
        for r, fid in enumerate(FEELINGS):
            for k, p in enumerate(R["picks_split0"][name][fid]):
                board.paste(thumb(p), (x0 + k * T, head + r * T))
    for r, fid in enumerate(FEELINGS):
        d.text((6, head + r * T + T // 2 - 6), fid, fill="black", font=font)
    path = os.path.join(HERE, "out", "artemis_board.png")
    board.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)  # keep the PNG small
    print(path, board.size, os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    main()
