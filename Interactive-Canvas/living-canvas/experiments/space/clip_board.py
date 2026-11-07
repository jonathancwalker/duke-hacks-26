"""Candidate A: board of top-3 picks for 12 feelings, current method vs the repaired one (for the blind human check).

Usage: python -I clip_board.py  ->  out/clip_board.png (+ out/clip_board_picks.json)
Columns: baseline (36 paintings, "a painting that feels {text}", cosine) | best fix on 36 | best fix on the larger library.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I drops the script dir
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from clip_common import OUT, cached_image_embeds, load_small_library
from clip_run import large_library, m_base, m_center_both, text_embeds, text_sets
from metrics import load_feelings

BOARD_FEELINGS = ["grief", "triumph", "calm", "rage", "anxious", "love", "lonely", "hope", "wonder", "exhausted",
                  "fear", "nostalgia"]
BEST = ("baseline/Rsent", "center both", m_center_both)     # chosen from out/clip_results.md
TH = 96


def font(sz):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def thumb(img):
    t = img.copy(); t.thumbnail((TH * 3 // 2, TH)); return t


def main():
    feelings, _ = load_feelings()
    rows = [i for i, f in enumerate(feelings) if f["id"] in BOARD_FEELINGS]
    names, imgs = load_small_library()
    I = cached_image_embeds("small", names, imgs)
    tx = text_embeds(feelings)
    Tb, Rb = text_sets(tx)[BEST[0]]
    cols = [("Today: 36 paintings, plain cosine", names, imgs, m_base(Tb, Rb, I)),
            (f"Repaired: 36 paintings, {BEST[1]}", names, imgs, BEST[2](Tb, Rb, I))]
    big = large_library(names, I)
    if big:
        bn, bI = big
        sub = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "wikiart_subset.json")))
        bimgs = imgs + [Image.open(s["path"]).convert("RGB") for s in sub]
        cols.append((f"Repaired: {len(bn)} paintings, {BEST[1]}", bn, bimgs, BEST[2](Tb, Rb, bI)))
    cw, left, top, rh = TH * 3 // 2 * 3 + 30, 260, 40, TH + 34
    W, H = left + cw * len(cols), top + rh * len(rows)
    board = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(board)
    f12, f14 = font(12), font(15)
    for c, (title, *_rest) in enumerate(cols):
        d.text((left + c * cw + 6, 12), title, fill="black", font=f14)
    picks = {}
    for r, i in enumerate(rows):
        y = top + r * rh
        txt = feelings[i]["text"]
        d.text((8, y + 6), feelings[i]["id"], fill="black", font=f14)
        words, line, ly = txt.split(), "", y + 26
        for w in words:
            if d.textlength(line + " " + w, font=f12) > left - 16:
                d.text((8, ly), line.strip(), fill="#555", font=f12); ly += 14; line = ""
            line += " " + w
        d.text((8, ly), line.strip(), fill="#555", font=f12)
        for c, (title, nm, im, S) in enumerate(cols):
            top3 = np.argsort(-S[i])[:3]
            picks.setdefault(feelings[i]["id"], {})[title] = [nm[j] for j in top3]
            x = left + c * cw + 6
            for j in top3:
                t = thumb(im[j]); board.paste(t, (x, y + 4))
                d.text((x, y + TH + 6), nm[j].split(",")[0][:18], fill="#333", font=f12)
                x += TH * 3 // 2 + 6
    for c in range(1, len(cols)):
        d.line([(left + c * cw - 6, 0), (left + c * cw - 6, H)], fill="#bbb", width=2)
    os.makedirs(OUT, exist_ok=True)
    board = board.convert("P", palette=Image.ADAPTIVE, colors=192)   # keep the committed PNG small
    board.save(os.path.join(OUT, "clip_board.png"), optimize=True)
    json.dump(picks, open(os.path.join(OUT, "clip_board_picks.json"), "w"), indent=1)
    print("saved", os.path.join(OUT, "clip_board.png"), board.size)


if __name__ == "__main__":
    main()
