# Live booth state on the GPU: one crowd, many visitors. Called by booth/booth_server.py through /exec.
import numpy as np

if "BOOTH" not in globals():
    BOOTH = {"C": {k: 0.0 for k in AX3}, "history": [], "n": 0}

# Style-only injection keeps a painting's palette and drama without importing its figures (R3e:
# Goya/Delacroix at full strength brought a brawling crowd into the scene).
BOOTH_STYLE = globals().get("BOOTH_STYLE", 1.2)


def booth_reset():
    BOOTH.update({"C": {k: 0.0 for k in AX3}, "history": [], "n": 0})


def paint_booth(coefs, seed=7):
    return render2(ip=art_point(coefs), ip_scale=style_only(BOOTH_STYLE), seed=seed, **ART_CN)


def booth_visit(e):
    """e: {'energy','temperature','value'} in [-1, 1]. Returns (moment_img, crowd_img, info)."""
    e = {k: float(np.clip(e.get(k, 0.0), -1, 1)) for k in AX3}
    C = BOOTH["C"]
    novelty = float(np.clip(np.linalg.norm([e[k] - C[k] for k in AX3]) / 2.0, 0, 1))
    alpha = 0.25 + 0.25 * novelty                      # surprising visitors pull harder
    BOOTH["history"].append(e); BOOTH["n"] += 1
    recent = BOOTH["history"][-8:]
    spread = float(np.mean([np.std([h[k] for h in recent]) for k in AX3])) if len(recent) > 1 else 0.0
    discord = float(np.clip((spread - 0.45) * 1.6, 0, 0.7))
    moment = {k: C[k] + 0.85 * (e[k] - C[k]) for k in AX3} | {"discord": 0.0}
    newC = {k: C[k] + alpha * (e[k] - C[k]) for k in AX3}
    BOOTH["C"] = newC
    after = newC | {"discord": discord}
    info = {"n": BOOTH["n"], "you": e, "crowd": newC, "discord": round(discord, 2), "pull": round(alpha, 2),
            "you_nearest": nearest_art(art_point(e), 2), "crowd_nearest": nearest_art(art_point(after), 2)}
    return paint_booth(moment), paint_booth(after), info
