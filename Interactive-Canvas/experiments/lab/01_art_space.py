# Art-space axes (the round 1 winner) and the round 2 visitor list. Sent after 00_lib.py with every experiment.
import numpy as np
import torch


class Raw:
    """Send non-JPEG bytes (e.g. a GIF) back through show(): the server calls .convert().save()."""
    def __init__(self, data): self.data = data
    def convert(self, mode): return self
    def save(self, f, fmt=None, **kw): f.write(self.data)


def A(*names):
    idx = [i for i, n in enumerate(ART_NAMES) if any(n.startswith(x) for x in names)]
    return ART_M[idx].mean(0, keepdim=True)


# Each axis is a direction between two groups of real paintings in the IP-Adapter's CLIP image space.
# Round 3 added Romantic paintings (Goya, Delacroix, Gericault) so hot + dark + violent has somewhere to land.
ART_AXES = {
    "energy":      A("Van Gogh, The Starry", "Turner, Rain", "Hokusai", "Munch", "Kandinsky", "Delacroix, Liberty", "Gericault", "Goya")
                   - A("Whistler", "Monet, Water", "Friedrich", "Monet, Impression"),
    "temperature": A("Klimt", "Turner, The Fighting", "Van Gogh, Wheatfield", "Seurat", "Delacroix, The Death", "Rembrandt")
                   - A("Whistler", "Hokusai", "Monet, Water", "Van Gogh, The Starry"),
    "value":       A("Monet, Water", "Seurat", "Hokusai", "Klimt") - A("Whistler", "Rembrandt", "Van Gogh, The Starry", "Turner, The Fighting", "Goya", "Gericault"),
    "discord":     A("Munch", "Kandinsky", "Van Gogh, Wheatfield", "Turner, Rain") - A("Monet, Water", "Seurat", "Whistler", "Klimt"),
}
CENTER = ART_M.mean(0, keepdim=True)
MEAN_NORM = float(ART_M.norm(dim=-1).mean())


def art_point(coefs, k=1.0, renorm=True):
    """Library center + sum(coefficient * axis), kept at a typical embedding length."""
    v = CENTER.clone()
    for name, c in coefs.items():
        v = v + k * c * ART_AXES[name]
    return v / v.norm() * MEAN_NORM if renorm else v


def nearest_art(v, k=2):
    sims = (ART_MN @ (v / v.norm()).T).squeeze(1)
    return [ART_NAMES[i].split(" (")[0] for i in torch.topk(sims, k).indices.tolist()]


ART_CN = dict(cn_scale=0.35, cn_end=0.5)


def paint_art(coefs, ip=0.85, seed=7):
    return render2(ip=art_point(coefs), ip_scale=ip, seed=seed, **ART_CN)


# A night of visitors: stand-ins for Claude + mic + webcam.
# (words, arousal 0..1, valence -1..1, laban weight, time, space, flow)
NIGHT_VISITORS = [
    ("Finally submitted my thesis. I could sleep for a week.", .25, .4, -.5, -.7, -.3, .6),
    ("Everyone I love is in this room right now!", .8, .9, -.6, .7, -.5, .8),
    ("I'm so stressed about the job market.", .9, -.7, .8, .9, .7, -.8),
    ("Missing my grandma tonight.", .15, -.6, -.7, -.8, -.6, .6),
    ("WE WON THE GAME!!", 1.0, .9, .8, .9, .6, .7),
    ("First snow of the year on the walk here.", .3, .5, -.6, -.5, -.4, .5),
    ("Honestly no idea what I'm doing with my life.", .4, -.4, -.2, .2, -.8, -.3),
    ("Spring break in nine days!", .75, .8, -.4, .6, -.2, .8),
    ("I want to build something that matters.", .5, .5, .7, -.6, .8, -.2),
    ("Thinking about the people who aren't here.", .2, -.5, -.5, -.7, -.3, .3),
    ("This city is so loud and I love it.", .85, .6, .5, .8, -.3, .6),
    ("I'm angry about how things are going.", .95, -.9, .9, .9, .9, -.9),
    ("Grateful. Just grateful.", .3, .9, -.3, -.6, .2, .5),
    ("Nervous about my presentation tomorrow.", .7, -.4, .2, .6, .4, -.7),
    ("Dancing all night.", .95, .8, .2, .9, -.7, 1.0),
    ("Quiet. Peaceful. Home.", .1, .7, -.8, -.9, -.2, .4),
]
AX3 = ("energy", "temperature", "value")


def visitor_coefs(a, v, w, t, s, f):
    """Voice (arousal, valence) + Laban effort -> art-space coefficients. Hand-set mapping; learnable later."""
    c = lambda x: float(np.clip(x, -1, 1))
    return {"energy": c(0.6 * (2 * a - 1) + 0.6 * t), "temperature": c(v), "value": c(0.7 * v - 0.3 * w)}
