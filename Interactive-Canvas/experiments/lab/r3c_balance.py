# Round 3 · Claude as art director vs the hand-set rule (temperature = valence, value = 0.7 valence - 0.3 weight).
# DIRECTOR values below were written by Claude reading each sentence plus its voice/movement features, standing in
# for the API call the booth will make. Pass: snow reads cool and bright, anger reads hot and dark, etc.
DIRECTOR = {
    "Finally submitted my thesis. I could sleep for a week.": dict(energy=-0.7, temperature=0.2, value=0.1, why="spent relief at dusk"),
    "Missing my grandma tonight.": dict(energy=-0.8, temperature=-0.3, value=-0.8, why="night, a single lamp"),
    "First snow of the year on the walk here.": dict(energy=-0.5, temperature=-0.8, value=0.6, why="cold, bright, hushed"),
    "I'm angry about how things are going.": dict(energy=1.0, temperature=0.7, value=-0.6, why="hot, dark, violent"),
    "Dancing all night.": dict(energy=1.0, temperature=0.6, value=-0.3, why="night lights, motion"),
    "Quiet. Peaceful. Home.": dict(energy=-0.9, temperature=0.6, value=0.2, why="warm hearth, stillness"),
}

norms = {k: round(float(v.norm()), 2) for k, v in ART_AXES.items()}
print("axis lengths:", norms)
target = sum(float(v.norm()) for v in ART_AXES.values()) / len(ART_AXES)
BAL = {k: v / v.norm() * target for k, v in ART_AXES.items()}
def paint_bal(coefs, ip=0.85, seed=7):
    v = CENTER.clone()
    for k, c in coefs.items(): v = v + c * BAL[k]
    return render2(ip=v / v.norm() * MEAN_NORM, ip_scale=ip, seed=seed, **ART_CN)
rows, labels = [], []
for words in ["I'm angry about how things are going.", "Dancing all night.", "First snow of the year on the walk here.", "Missing my grandma tonight."]:
    d = {k: DIRECTOR[words][k] for k in AX3}
    rows.append([paint_art(d), paint_bal(d), paint_bal({**d, "energy": d["energy"] * 0.6})])
    labels.append(f"\"{words}\" | e{d['energy']:+.1f} t{d['temperature']:+.1f} v{d['value']:+.1f} ({DIRECTOR[words]['why']})")
show(board(rows, labels, ["original axes", "equal-length axes", "equal-length, energy x0.6"], cell=(448, 252), left=250,
           title="R3c · balancing axis lengths"), "R3c_balance")
