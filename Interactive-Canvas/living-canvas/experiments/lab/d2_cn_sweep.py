# How loose can the structure lock be while the chapel still holds and the style comes through?
refs = ["Van Gogh, The Starry Night (1889)", "Whistler, Nocturne in Black and Gold (1875)", "Hokusai, The Great Wave (1831)"]
settings = [("cn .15", dict(cn_scale=0.15)), ("cn .25", dict(cn_scale=0.25)), ("cn .35 until 50%", dict(cn_scale=0.35, cn_end=0.5)),
            ("cn .5 until 25%", dict(cn_scale=0.5, cn_end=0.25)), ("sparse edges cn .35", dict(cn_scale=0.35, control=SPARSE_EDGES))]
rows, labels = [], []
for nm in refs:
    rows.append([ART[nm]] + [render2(ip=ART_V[nm], ip_scale=1.0, **kw) for _, kw in settings]); labels.append(nm)
show(board(rows, labels, ["reference"] + [s for s, _ in settings], title="D2 · structure lock vs style (IP-Adapter 1.0)"), "D2_cn_sweep")
