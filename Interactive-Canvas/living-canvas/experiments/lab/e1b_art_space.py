# H1 · Art-history space, rerun with a looser structure lock (D2: cn 0.3 keeps the chapel and lets style through).
CN = dict(cn_scale=0.35, cn_end=0.5)   # D3: a full-length lock >= 0.3 flattens style; lock layout early only
rows, labels = [], []
for k in ORDER:
    p = PERSONAS[k]; ws = art_weights(p["temperament"]); v = art_vec(ws)
    rows.append([ART[ws[0][0]], render2(ip=v, ip_scale=0.7, **CN), render2(ip=v, ip_scale=1.0, **CN), render2(ip=v, ip_scale=style_only(1.0), **CN)])
    labels.append(f"{k.upper()}: \"{p['words']}\" | nearest: {fmt_weights(ws)}")
show(board(rows, labels, ["nearest artwork", "IP 0.7", "IP 1.0", "style-only 1.0"], title="E1b · persona -> blend of artworks -> painting (cn 0.35 for first 50%)"), "E1b_personas")

# Is it a real space? Walk from grief to joy, and render the whole crowd's blend.
vg, vj = art_vec(art_weights(PERSONAS["grief"]["temperament"])), art_vec(art_weights(PERSONAS["joy"]["temperament"]))
walk = [render2(ip=(1 - t) * vg + t * vj, ip_scale=0.8, **CN) for t in (0, 0.25, 0.5, 0.75, 1)]
crowd = sum(art_vec(art_weights(PERSONAS[k]["temperament"])) for k in ORDER) / len(ORDER)
show(board([walk, [render2(ip=crowd, ip_scale=0.8, **CN)]], ["walk: grief -> joy (IP 0.8)", "crowd blend of all four (IP 0.8)"],
           ["0", "0.25", "0.5", "0.75", "1"], title="E1c · moving through art space"), "E1c_walk")
