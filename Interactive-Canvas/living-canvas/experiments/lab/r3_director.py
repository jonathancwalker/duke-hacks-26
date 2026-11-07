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
by_words = {v[0]: v for v in NIGHT_VISITORS}
rows, labels = [], []
for words, d in DIRECTOR.items():
    rule = visitor_coefs(*by_words[words][1:])
    direct = {k: d[k] for k in AX3}
    rows.append([paint_art(rule), paint_art(direct)])
    labels.append(f"\"{words}\" | rule: e{rule['energy']:+.1f} t{rule['temperature']:+.1f} v{rule['value']:+.1f} | "
                  f"director: e{direct['energy']:+.1f} t{direct['temperature']:+.1f} v{direct['value']:+.1f} ({d['why']})")
show(board(rows, labels, ["hand-set rule", "Claude as art director"], cell=(448, 252), left=250,
           title="R3 · art director vs rule (each visitor's own point in art space)"), "R3_director")
