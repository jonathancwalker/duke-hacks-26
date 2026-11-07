# Does style-only 1.2 (the booth default) still separate the calm cases, not just the dramatic ones?
cases = {
    "thesis relief": dict(energy=-0.7, temperature=0.2, value=0.1),
    "grandma": dict(energy=-0.8, temperature=-0.3, value=-0.8),
    "first snow": dict(energy=-0.5, temperature=-0.8, value=0.6),
    "quiet home": dict(energy=-0.9, temperature=0.6, value=0.2),
    "anger": dict(energy=1.0, temperature=0.7, value=-0.6),
    "joy": dict(energy=0.8, temperature=0.9, value=0.8),
}
rows, labels = [], []
for name, c in cases.items():
    rows.append([paint_art(c), paint_booth(c)]); labels.append(f"{name}: {c}")
show(board(rows, labels, ["full IP 0.85", "style-only 1.2 (booth default)"], cell=(448, 252), left=220,
           title="R3f · style-only across calm and dramatic cases"), "R3f_style_check")
