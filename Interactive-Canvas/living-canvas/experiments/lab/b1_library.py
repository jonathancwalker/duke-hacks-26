# Brush round 1: grow the library and eyeball every painting + its palette + assigned brush.
from PIL import ImageDraw
added = ensure_library()
print(f"added {added}; library now {len(ART_NAMES)} paintings")
cards = []
for n in ART_NAMES:
    c = Image.new("RGB", (240, 200), "white"); t = ART[n].copy(); t.thumbnail((240, 150)); c.paste(t, ((240 - t.width) // 2, 0))
    d = ImageDraw.Draw(c)
    for i, hx in enumerate(palette_of(n)):
        d.rectangle([i * 40, 152, i * 40 + 39, 172], fill=hx)
    d.text((2, 176), n[:38], fill="black"); d.text((2, 188), brush_for(n), fill="gray")
    cards.append(c)
cols = 8; rows = (len(cards) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 240, rows * 200), "white")
for i, c in enumerate(cards):
    sheet.paste(c, ((i % cols) * 240, (i // cols) * 200))
show(sheet, "B1_library")
