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

rows, labels = [], []
for words in ["I'm angry about how things are going.", "Dancing all night."]:
    c = {k: DIRECTOR[words][k] for k in AX3}; v = art_point(c)
    rows.append([render2(ip=v, ip_scale=0.85, **ART_CN), render2(ip=v, ip_scale=style_only(1.0), **ART_CN),
                 render2(ip=v, ip_scale=style_only(1.4), **ART_CN), render2(ip=v, ip_scale=0.55, **ART_CN)])
    labels.append(words)
show(board(rows, labels, ["full 0.85 (figures leak)", "style-only 1.0", "style-only 1.4", "full 0.55"], cell=(448, 252), left=200,
           title="R3e · keep the drama, drop the figures"), "R3e_style_only")
