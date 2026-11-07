# Round 2 · a whole night, in two halves (first run: visitors 1-8; second run: 9-16). State persists on the server.
import numpy as np

if "NIGHT" not in globals() or len(NIGHT["history"]) >= len(NIGHT_VISITORS):
    NIGHT = {"C": {k: 0.0 for k in AX3}, "history": [], "states": [{k: 0.0 for k in AX3} | {"discord": 0.0}],
             "moments": [], "crowd": [paint_art({k: 0.0 for k in AX3} | {"discord": 0.0})]}
start = len(NIGHT["history"]); stop = min(start + 8, len(NIGHT_VISITORS))
rows, labels = [], []
for i in range(start, stop):
    words, a, v, w, t, s, f = NIGHT_VISITORS[i]
    e = visitor_coefs(a, v, w, t, s, f)
    C = NIGHT["C"]
    novelty = float(np.clip(np.linalg.norm([e[k] - C[k] for k in AX3]) / 2.0, 0, 1))
    alpha = 0.25 + 0.25 * novelty                       # surprising visitors pull harder
    NIGHT["history"].append(e)
    recent = NIGHT["history"][-8:]
    spread = float(np.mean([np.std([h[k] for h in recent]) for k in AX3])) if len(recent) > 1 else 0.0
    # v1 (1.6 * spread) saturated by visitor 3: any varied night has spread ~0.7. Only unusual division counts.
    discord = float(np.clip((spread - 0.45) * 1.6, 0, 0.7))   # a divided room -> fractured painting
    moment = {k: C[k] + 0.85 * (e[k] - C[k]) for k in AX3} | {"discord": 0.0}   # your moment is yours alone
    C = {k: C[k] + alpha * (e[k] - C[k]) for k in AX3}
    NIGHT["C"] = C
    after = C | {"discord": discord}
    NIGHT["states"].append(after)
    fm, fc = paint_art(moment), paint_art(after)
    NIGHT["moments"].append(fm); NIGHT["crowd"].append(fc)
    rows.append([fm, fc])
    labels.append(f"{i + 1}. \"{words}\" | you: e{e['energy']:+.1f} t{e['temperature']:+.1f} v{e['value']:+.1f} | "
                  f"crowd: e{C['energy']:+.2f} t{C['temperature']:+.2f} v{C['value']:+.2f} discord {discord:.2f} | "
                  f"pull {alpha:.2f} | crowd nearest: {', '.join(nearest_art(art_point(after)))}")
    print(labels[-1])
show(board(rows, labels, ["YOUR MOMENT (crowd pulled 85% toward you)", "CROWD AFTER YOU"], cell=(512, 288), left=240,
           title=f"Round 2 · a night of visitors {start + 1}-{stop}"), f"N_visitors_{start + 1:02d}_{stop:02d}")
