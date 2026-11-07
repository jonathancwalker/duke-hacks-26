# Live booth state on the GPU: one crowd, many visitors. Called by booth/booth_server.py through /exec.
import numpy as np
import torch

if "BOOTH" not in globals():
    BOOTH = {"C": {k: 0.0 for k in AX3}, "history": [], "n": 0}
# Painting-mix memory (round 4). Added with setdefault so a session started by older booth code keeps working.
if len(BOOTH.setdefault("M", np.zeros(len(ART_NAMES)))) != len(ART_NAMES):
    BOOTH["M"] = np.zeros(len(ART_NAMES))

# Style-only injection keeps a painting's palette and drama without importing its figures (R3e:
# Goya/Delacroix at full strength brought a brawling crowd into the scene).
BOOTH_STYLE = globals().get("BOOTH_STYLE", 1.2)
# Round 4 hybrid: the mix gives character, the axes give intensity (+36% output spread over axes alone).
HYB_MIX, HYB_AXES = 1.5, 0.6


def booth_reset():
    BOOTH.update({"C": {k: 0.0 for k in AX3}, "M": np.zeros(len(ART_NAMES)), "history": [], "n": 0})


def mix_array(mix):
    a = np.zeros(len(ART_NAMES))
    for name, w in (mix or {}).items():
        if name in ART_NAMES and w > 0:
            a[ART_NAMES.index(name)] += float(w)
    return a


def booth_point(coefs, M=None):
    """Hybrid when the painting mix M has weight: center + 1.5 * mass * (blend - center) + 0.6 * axes.
    Without a mix this is exactly art_point(coefs), the pre-round-4 placement. Discord always adds at full strength."""
    axes = sum(coefs.get(k, 0.0) * ART_AXES[k] for k in AX3)
    discord = coefs.get("discord", 0.0) * ART_AXES["discord"]
    mass = float(M.sum()) if M is not None else 0.0
    if mass > 1e-6:
        w = torch.tensor(M / mass, dtype=ART_M.dtype, device=ART_M.device)[:, None]
        blend = (w * ART_M).sum(0, keepdim=True)
        v = CENTER + HYB_MIX * min(mass, 1.0) * (blend - CENTER) + HYB_AXES * axes + discord
    else:
        v = CENTER + axes + discord
    return v / v.norm() * MEAN_NORM


def paint_booth(coefs, M=None, seed=7):
    return render2(ip=booth_point(coefs, M), ip_scale=style_only(BOOTH_STYLE), seed=seed, **ART_CN)


def booth_current():
    M = BOOTH["M"]
    return paint_booth(BOOTH["C"] | {"discord": 0.0}, M if M.sum() > 0 else None)


def top_mix(M, k=3):
    if M is None or M.sum() <= 0:
        return []
    idx = np.argsort(-M)[:k]
    return [[ART_NAMES[i].split(" (")[0], round(float(M[i] / M.sum()), 2)] for i in idx if M[i] > 0]


def booth_visit(e, mix=None):
    """e: {'energy','temperature','value'} in [-1, 1]; mix: {painting name: weight} or empty for axes-only.
    Returns (moment_img, crowd_img, info)."""
    e = {k: float(np.clip(e.get(k, 0.0), -1, 1)) for k in AX3}
    m = mix_array(mix); has_mix = m.sum() > 0
    C, M = BOOTH["C"], BOOTH["M"]
    novelty = float(np.clip(np.linalg.norm([e[k] - C[k] for k in AX3]) / 2.0, 0, 1))
    alpha = 0.25 + 0.25 * novelty                      # surprising visitors pull harder
    BOOTH["history"].append(e); BOOTH["n"] += 1
    recent = BOOTH["history"][-8:]
    spread = float(np.mean([np.std([h[k] for h in recent]) for k in AX3])) if len(recent) > 1 else 0.0
    discord = float(np.clip((spread - 0.45) * 1.6, 0, 0.7))
    moment = {k: C[k] + 0.85 * (e[k] - C[k]) for k in AX3} | {"discord": 0.0}
    moment_M = M + 0.85 * (m - M) if has_mix else None
    newC = {k: C[k] + alpha * (e[k] - C[k]) for k in AX3}
    newM = M + alpha * (m - M) if has_mix else M
    BOOTH["C"], BOOTH["M"] = newC, newM
    after = newC | {"discord": discord}
    crowd_M = newM if newM.sum() > 0 else None
    info = {"n": BOOTH["n"], "you": e, "crowd": newC, "discord": round(discord, 2), "pull": round(alpha, 2),
            "placement": "hybrid" if has_mix else "axes",
            "you_mix": top_mix(m if has_mix else None), "crowd_mix": top_mix(crowd_M),
            "you_nearest": nearest_art(booth_point(e, m if has_mix else None), 2),
            "crowd_nearest": nearest_art(booth_point(after, crowd_M), 2)}
    return paint_booth(moment, moment_M), paint_booth(after, crowd_M), info
