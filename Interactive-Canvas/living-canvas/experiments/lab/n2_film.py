# Round 2 · film of the night. For each visitor: crowd -> ease into their moment -> hold -> settle into the new crowd.
# Run repeatedly: each call renders the next 5 visitors (stays under the tunnel's 100 s limit); the last call returns a GIF.
import io
import numpy as np

assert "NIGHT" in globals() and len(NIGHT["history"]) == len(NIGHT_VISITORS), "run n1_night.py for all 16 visitors first"
TWEENS = 2
if "FILM" not in globals() or FILM.get("done"):
    FILM = {"next": 0, "frames": [], "durations": [], "captions": []}


def lerp(a, b, t):
    return {k: a[k] + (b[k] - a[k]) * t for k in a}


start = FILM["next"]; stop = min(start + 5, len(NIGHT_VISITORS))
for i in range(start, stop):
    before, after = NIGHT["states"][i], NIGHT["states"][i + 1]
    e = NIGHT["history"][i]
    moment = {k: before[k] + 0.85 * (e[k] - before[k]) for k in AX3} | {"discord": 0.0}
    words = NIGHT_VISITORS[i][0]
    for t in np.linspace(0, 1, TWEENS + 2)[1:-1]:                     # ease into the moment
        FILM["frames"].append(paint_art(lerp(before, moment, t))); FILM["durations"].append(140); FILM["captions"].append("")
    FILM["frames"].append(paint_art(moment)); FILM["durations"].append(1600); FILM["captions"].append(f"{i + 1}. “{words}”")
    for t in np.linspace(0, 1, TWEENS + 2)[1:]:                       # settle into the crowd
        FILM["frames"].append(paint_art(lerp(moment, after, t))); FILM["durations"].append(140 if t < 1 else 700); FILM["captions"].append("")
FILM["next"] = stop
print(f"rendered visitors {start + 1}-{stop}, {len(FILM['frames'])} frames so far")

if stop == len(NIGHT_VISITORS):
    from PIL import ImageDraw
    out = []
    for f, cap in zip(FILM["frames"], FILM["captions"]):
        g = f.resize((640, 360))
        if cap:
            d = ImageDraw.Draw(g); d.rectangle([0, 326, 640, 360], fill=(16, 14, 20)); d.text((12, 337), cap[:90], fill=(240, 236, 226))
        out.append(g.convert("P", palette=Image.ADAPTIVE, colors=200))
    b = io.BytesIO()
    out[0].save(b, "GIF", save_all=True, append_images=out[1:], duration=FILM["durations"], loop=0, optimize=True)
    show(Raw(b.getvalue()), "night_film")
    show(board([[NIGHT["crowd"][0]] + NIGHT["crowd"][4:17:4]], ["crowd painting over the night"],
               ["opening", "after 4", "after 8", "after 12", "after 16"], cell=(384, 216)), "crowd_arc")
    FILM["done"] = True
    print(f"GIF: {len(out)} frames, {len(b.getvalue()) / 1e6:.1f} MB")
