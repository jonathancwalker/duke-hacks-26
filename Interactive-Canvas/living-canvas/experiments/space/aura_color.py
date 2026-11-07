"""Color math for the color-aura candidate (D): sRGB <-> CIELAB (D65), gamut clipping, CIEDE2000, palette distance.

Palette distance (used by metrics.report_outputs): two 5-color palettes are matched one-to-one with the Hungarian
algorithm on their CIEDE2000 matrix, and the distance is the mean Delta E 2000 of the matched pairs. So the order of
colors in a palette doesn't matter, and a distance of ~2 is "barely visible", ~10 "clearly different", 40+ "unrelated".
"""
import numpy as np
from scipy.optimize import linear_sum_assignment

_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]])
_MI = np.linalg.inv(_M)
_WHITE = np.array([0.95047, 1.0, 1.08883])


def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def rgb_to_hex(rgb):
    r, g, b = (int(round(float(np.clip(x, 0, 1)) * 255)) for x in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_lab(rgb):
    rgb = np.asarray(rgb, float)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = lin @ _M.T / _WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_rgb_unclipped(lab):
    lab = np.asarray(lab, float)
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f > 6 / 29, f ** 3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * _WHITE
    lin = xyz @ _MI.T
    return np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.abs(lin) ** (1 / 2.4) * np.sign(lin) - 0.055)


def in_gamut(lab, tol=1e-4):
    rgb = lab_to_rgb_unclipped(lab)
    return bool(np.all(rgb >= -tol) and np.all(rgb <= 1 + tol))


def lch_to_rgb(L, C, h):
    """LCh(ab) to sRGB; if out of gamut, keep lightness and hue and lower chroma until it fits."""
    L = float(np.clip(L, 0, 100))
    for s in np.linspace(1, 0, 41):
        lab = np.array([L, C * s * np.cos(np.radians(h)), C * s * np.sin(np.radians(h))])
        if in_gamut(lab):
            break
    return np.clip(lab_to_rgb_unclipped(lab), 0, 1)


def ciede2000(lab1, lab2):
    """CIEDE2000 (Sharma, Wu & Dalal 2005), broadcasting over leading axes."""
    L1, a1, b1 = np.moveaxis(np.asarray(lab1, float), -1, 0)
    L2, a2, b2 = np.moveaxis(np.asarray(lab2, float), -1, 0)
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cb7 = ((C1 + C2) / 2) ** 7
    G = 0.5 * (1 - np.sqrt(Cb7 / (Cb7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(C1p * C2p == 0, 0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh / 2))
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hs = h1p + h2p
    hbp = np.where(np.abs(h1p - h2p) > 180, np.where(hs < 360, hs + 360, hs - 360), hs) / 2
    hbp = np.where(C1p * C2p == 0, hs, hbp)
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dtheta = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Cbp7 = Cbp ** 7
    RC = 2 * np.sqrt(Cbp7 / (Cbp7 + 25 ** 7))
    SL = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    SC, SH = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    RT = -np.sin(np.radians(2 * dtheta)) * RC
    return np.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))


def palette_lab(palette_hex):
    return rgb_to_lab(np.array([hex_to_rgb(h) for h in palette_hex]))


def palette_distance(p, q):
    """Mean CIEDE2000 between optimally matched colors of two palettes (Lab arrays, shape (5, 3))."""
    d = ciede2000(p[:, None, :], q[None, :, :])
    r, c = linear_sum_assignment(d)
    return float(d[r, c].mean())


def within_palette_spread(p):
    """Mean CIEDE2000 between the colors of one palette (0 = five copies of one color)."""
    d = ciede2000(p[:, None, :], p[None, :, :])
    n = len(p)
    return float(d[np.triu_indices(n, 1)].mean())


def brightness_saturation(p):
    """Summary 'sense' of a palette: brightness = mean L*/100, saturation = mean chroma / 100 (clipped to 1)."""
    return round(float(p[:, 0].mean() / 100), 3), round(float(min(1, np.hypot(p[:, 1], p[:, 2]).mean() / 100)), 3)


if __name__ == "__main__":
    # Sharma et al. 2005 test pairs (first three rows of their table): expected 2.0425, 2.8615, 3.4412.
    a = np.array([[50, 2.6772, -79.7751], [50, 3.1571, -77.2803], [50, 2.8361, -74.0200]])
    b = np.array([[50, 0, -82.7485], [50, 0, -82.7485], [50, 0, -82.7485]])
    print(np.round(ciede2000(a, b), 4))
    print(rgb_to_hex(lab_to_rgb_unclipped(rgb_to_lab(hex_to_rgb("#3a7bd5")))))
