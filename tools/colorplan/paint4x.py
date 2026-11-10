"""4x colour-theory repaint of an indexed sprite or tile block.

Input: an index image (-1 = transparent) at native size and, per index, (ramp name, value t).
Steps: Scale2x twice (keeps pixel-art edges), soften value inside each material, add form
light from the top-left (rounded volume from the silhouette), selective outline (dark on the
shadow side, lighter on the lit side), then every pixel takes its colour from its material's
ramp, quantised to a fixed number of steps so each material keeps a planned, limited palette.
"""
import numpy as np
from scipy import ndimage
from plan import RAMPS

def scale2x(a):
    p = np.pad(a, 1, mode='edge')
    B, D, E, F, H = p[:-2, 1:-1], p[1:-1, :-2], p[1:-1, 1:-1], p[1:-1, 2:], p[2:, 1:-1]
    o = np.empty((a.shape[0]*2, a.shape[1]*2), a.dtype)
    c = (B != H) & (D != F)
    o[0::2, 0::2] = np.where(c & (D == B), D, E)
    o[0::2, 1::2] = np.where(c & (B == F), F, E)
    o[1::2, 0::2] = np.where(c & (D == H), D, E)
    o[1::2, 1::2] = np.where(c & (H == F), F, E)
    return o

def paint(idx, table, steps=8, sprite=True, light=0.12, soften=0.35, sigma=1.6, norim=()):
    """idx: int array (native), table: {index: (ramp, t)}. Returns RGBA uint8 at 4x."""
    big = scale2x(scale2x(idx))
    opaque = big >= 0
    mats = sorted({table[i][0] for i in np.unique(big) if i >= 0})
    T = np.zeros(big.shape); M = np.full(big.shape, -1)
    for i in np.unique(big):
        if i < 0: continue
        T[big == i] = table[i][1]; M[big == i] = mats.index(table[i][0])
    # soften value inside each material (smooth gradients, edges between materials stay crisp)
    Ts = T.copy()
    for m in range(len(mats)):
        mm = (M == m).astype(float)
        num = ndimage.gaussian_filter(T * mm, sigma); den = ndimage.gaussian_filter(mm, sigma)
        Ts[M == m] = (num / np.maximum(den, 1e-6))[M == m]
    T2 = T * (1 - soften) + Ts * soften
    # form light: height from distance to silhouette (sprite) or to material edge (tiles)
    if sprite: dist = ndimage.distance_transform_edt(opaque)
    else:
        edge = np.zeros(big.shape, bool)
        edge[:-1] |= big[:-1] != big[1:]; edge[:, :-1] |= big[:, :-1] != big[:, 1:]
        dist = ndimage.distance_transform_edt(~edge)
    h = ndimage.gaussian_filter(np.minimum(dist, 10.0) / 10.0, 1.5)
    gy, gx = np.gradient(h)
    n = np.hypot(gx, gy) + 1e-6
    shade = (gx * 0.7071 + gy * 0.7071) / n * np.minimum(n * 8, 1)   # >0 when surface faces top-left
    T2 = T2 + light * shade
    if sprite:
        er = ndimage.binary_erosion(opaque)
        rim = opaque & ~er & ~np.isin(big, list(norim))
        lit = rim & (np.roll(~opaque, 1, 0) | np.roll(~opaque, 1, 1))     # transparent above/left
        T2[rim & ~lit] -= 0.30                                             # shadow-side outline
        T2[lit] += 0.10                                                    # warm rim on lit side
    T2 = np.clip(T2, 0, 1)
    Tq = np.round(T2 * (steps - 1)) / (steps - 1)
    out = np.zeros(big.shape + (4,), np.uint8)
    cache = {}
    for m, name in enumerate(mats):
        for v in np.unique(Tq[M == m]):
            key = (name, v)
            if key not in cache: cache[key] = np.clip(np.round(RAMPS[name](v)), 0, 255)
            sel = (M == m) & (Tq == v)
            out[sel, :3] = cache[key]; out[sel, 3] = 255
    return out
