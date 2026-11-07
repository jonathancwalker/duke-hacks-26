CN = dict(cn_scale=0.35, cn_end=0.5)   # early-only structure lock (from D2/D3)
# H3 · Form axes. Sweep each art-theory axis alone (-1, 0, +1) with guidance push, then map personas.
# Pass: each axis changes form (brushwork / palette / edges / density / abstraction), not weather or subject.
import time
PUSH = 3.0
rows, labels = [], []
t0 = time.time(); n = 0
for name in AXES:
    rows.append([render2(cond=form_cond({name: c}), push=PUSH, **CN) for c in (-1, 0, 1)]); n += 3
    labels.append(f"{name}: {AXES[name][0][0]}  <->  {AXES[name][1][0]}")
print(f"{(time.time() - t0) / n:.2f}s per frame (push {PUSH})")
show(board(rows, labels, ["-1", "0", "+1"], title="E3a · H3 single-axis sweeps"), "E3a_axes")

rows, labels = [], []
for k in ORDER:
    c = persona_coefs(PERSONAS[k])
    rows.append([render2(cond=form_cond(c), push=PUSH, **CN), render2(cond=form_cond(c, scale=0.8), push=PUSH, **CN)])
    labels.append(f"{k.upper()} ({PERSONAS[k]['voice']}): {fmt_coefs(c)}")
show(board(rows, labels, ["persona, axis scale 0.5", "persona, axis scale 0.8"],
           title="E3b · H3 personas on form axes (same subject, different temperament)"), "E3b_personas")
