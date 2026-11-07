# Why do blends barely transfer when single artworks transfer strongly? Test embedding length.
wh = "Whistler, Nocturne in Black and Gold (1875)"
ws = art_weights(PERSONAS["grief"]["temperament"])
single = ART_V[wh]; blend = art_vec(ws)
mean_norm = float(ART_M.norm(dim=-1).mean())
renorm = blend / blend.norm() * mean_norm
print("norms: single", round(float(single.norm()), 2), "| blend", round(float(blend.norm()), 2), "| library mean", round(mean_norm, 2))
print("cos(single, blend) =", round(float(torch.nn.functional.cosine_similarity(single, blend)), 3))
print("pairwise cos between artworks: mean", round(float((ART_MN @ ART_MN.T).fill_diagonal_(0).sum() / (len(ART_NAMES) * (len(ART_NAMES) - 1))), 3))
frames = [render2(ip=x, ip_scale=1.0, cn_scale=0.3) for x in (single, art_vec([(wh, 0, 1.0)]), blend, renorm)]
show(board([frames], ["grief"], ["Whistler alone", "Whistler via art_vec", "grief blend (raw)", "grief blend, renormalized"]), "D3_blend_norm")
