# H1 · Art-history space. Each persona's temperament -> nearest real artworks in CLIP space -> blended
# embedding -> IP-Adapter. Does the painting change in FORM (style) while the chapel stays?
import time
rows, labels = [], []
for k in ORDER:
    p = PERSONAS[k]; ws = art_weights(p["temperament"]); v = art_vec(ws)
    print(f"{k:8s} -> {fmt_weights(ws)}")
    t0 = time.time()
    full = render(ip=v, ip_scale=0.6)
    so = render(ip=v, ip_scale=style_only(1.0))
    so_push = render(ip=v, ip_scale=style_only(1.0), push=2.0)
    print(f"         {(time.time() - t0) / 3:.2f}s per frame")
    rows.append([ART[ws[0][0]], full, so, so_push])
    labels.append(f"{k.upper()}: \"{p['words']}\" | {p['temperament']} || nearest: {fmt_weights(ws)}")
show(board(rows, labels, ["nearest artwork", "IP-Adapter full 0.6", "style-only 1.0", "style-only 1.0 + push 2"],
           title="E1 · H1 art-history space: temperament -> blend of real artworks -> IP-Adapter"), "E1_art_space")
