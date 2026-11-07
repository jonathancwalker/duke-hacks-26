CN = dict(cn_scale=0.35, cn_end=0.5)   # early-only structure lock (from D2/D3)
# H2 · Trace underpainting. Four people's gestures stacked as brush layers on the opening painting,
# then a diffusion finish. Do the marks survive, and does it still read as a painting?
import time
layers, cur = [opening], opening
for i, k in enumerate(ORDER):
    cur = paint_trace(cur, PERSONAS[k], seed=i); layers.append(cur)
rows, labels = [], []
t0 = time.time(); n = 0
for i in range(1, len(layers)):
    row = [layers[i]] + [render2(init=layers[i], strength=s, **CN) for s in (0.35, 0.5, 0.65)]; n += 3
    rows.append(row); labels.append(f"after {i} visitor(s): " + ", ".join(ORDER[:i]))
print(f"{(time.time() - t0) / n:.2f}s per finish frame")
show(board(rows, labels, ["underpainting (raw traces)", "finish strength 0.35", "finish 0.5", "finish 0.65"],
           title="E2 · H2 trace underpainting: gestures stacked, then diffusion finish"), "E2_trace")
