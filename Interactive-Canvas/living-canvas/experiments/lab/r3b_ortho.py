# R3 found the axes entangled: "warm" paintings (Klimt, Seurat) are also bright, so hot+dark (anger) came out bright yellow.
# Fix: Gram-Schmidt so each axis moves independently. Order = priority: value, energy, temperature, discord.
import torch
print("axis cosine before:", {f"{a[:4]}-{b[:4]}": round(float(torch.nn.functional.cosine_similarity(ART_AXES[a], ART_AXES[b])), 2)
                              for a, b in [("temperature", "value"), ("energy", "value"), ("energy", "temperature"), ("discord", "energy")]})
ortho, basis = {}, []
for name in ("value", "energy", "temperature", "discord"):
    v = ART_AXES[name].clone()
    for u in basis:
        v = v - (v @ u.T) / (u @ u.T) * u
    v = v / v.norm() * ART_AXES[name].norm()          # keep each axis's original strength
    ortho[name] = v; basis.append(v)
ART_AXES_ORTHO = ortho


def paint_art_o(coefs, ip=0.85, seed=7):
    v = CENTER.clone()
    for k, c in coefs.items(): v = v + c * ART_AXES_ORTHO[k]
    return render2(ip=v / v.norm() * MEAN_NORM, ip_scale=ip, seed=seed, **ART_CN)


rows, labels = [], []
for words in ["I'm angry about how things are going.", "First snow of the year on the walk here.", "Missing my grandma tonight.", "Dancing all night."]:
    d = {k: DIRECTOR[words][k] for k in AX3}
    rows.append([paint_art(d), paint_art_o(d)])
    labels.append(f"\"{words}\" | director: e{d['energy']:+.1f} t{d['temperature']:+.1f} v{d['value']:+.1f} ({DIRECTOR[words]['why']})")
sweep = [paint_art_o({"temperature": t, "value": v}) for t, v in [(1, -1), (1, 1), (-1, -1), (-1, 1)]]
show(board(rows, labels, ["original axes", "orthogonalized axes"], cell=(448, 252), left=250,
           title="R3b · orthogonalized art axes"), "R3b_ortho")
show(board([sweep], ["temperature x value (ortho)"], ["hot + dark", "hot + light", "cool + dark", "cool + light"], cell=(384, 216)), "R3b_grid")
