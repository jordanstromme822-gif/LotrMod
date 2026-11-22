"""Draw the water that runs off a joined map's edge on into the new ground, ending in a shoreline made of the levels'
own 8 px tiles (2026-11-22).

A target water shape (pixels) is given: water runs out from each wet stretch of a map edge and closes in a smooth,
wobbly curve. Every 8 px spot in the new ground near that shape gets the game tile (any flip it is used with) whose
see-through pixels best follow the shape and whose edge pixels best continue the tiles already placed around it
(scanned top-left to bottom-right, with the map's own tiles and the plain ground as fixed neighbours).
"""
import collections
import numpy as np
from build import pix


def tile_px(k, pixels, rgb):
    p = pix(pixels[k[0]])
    if k[1] & 0x400: p = p[:, ::-1]
    if k[1] & 0x800: p = p[::-1]
    return rgb[(k[1] >> 12) * 16 + p].astype(np.float32), p == 0


def synth(GA, GB, GC, DW, fixed8, pixels, rgb, cand_keys, col_of, grav_col, reach=2, log=print, seed=9):
    H8, W8 = len(GA), len(GA[0])
    rng = np.random.default_rng(seed)
    keys = list(cand_keys)
    IM = np.stack([tile_px(k, pixels, rgb)[0] for k in keys]); TR = np.stack([tile_px(k, pixels, rgb)[1] for k in keys])
    TRf = TR.reshape(len(keys), 64).astype(np.float32)
    mixed = ((TRf.sum(1) > 0) & (TRf.sum(1) < 64)).astype(np.float32)   # shore pieces (part water, part land)
    # rim pixels: the dark lip a shore has next to the water (any land colour the plain gravel does not use)
    RIM = np.array([[(not t) and tuple(int(u) for u in v) not in grav_col for v, t in zip(im.reshape(64, 3), tr.reshape(64))]
                    for im, tr in zip(IM, TR)], bool)
    # land within 2 px of the target water (looking across tile edges)
    near = DW.copy()
    for _ in range(2):
        g = near.copy(); g[1:] |= near[:-1]; g[:-1] |= near[1:]; g[:, 1:] |= near[:, :-1]; g[:, :-1] |= near[:, 1:]; near = g
    near &= ~DW
    # 8 px spots to draw: new ground whose target has water, and a ring around it
    wet8 = DW.reshape(H8, 8, W8, 8).any((1, 3)) & ~fixed8
    region = wet8.copy()
    for _ in range(reach):
        g = region.copy()
        g[1:] |= region[:-1]; g[:-1] |= region[1:]; g[:, 1:] |= region[:, :-1]; g[:, :-1] |= region[:, 1:]
        region = g & ~fixed8
    ys, xs = np.nonzero(region)
    log('shore spots', len(ys), 'candidate tiles', len(keys))
    cur = {}
    def img_at(y, x):
        if (y, x) in cur: return cur[(y, x)]
        return tile_px(GA[y][x], pixels, rgb)
    used = collections.Counter()
    for y, x in sorted(zip(ys.tolist(), xs.tolist())):
        tgt = DW[y * 8:y * 8 + 8, x * 8:x * 8 + 8].reshape(64).astype(np.float32)
        cost = 20.0 * np.abs(TRf - tgt[None]).sum(1)                          # follow the water shape
        nr = near[y * 8:y * 8 + 8, x * 8:x * 8 + 8].reshape(64)
        cost += 12.0 * (RIM & ~nr[None]).sum(1)                                # the dark lip only right at the water
        cost += 1.5 * (~TR.reshape(len(keys), 64) & ~RIM & nr[None]).sum(1)  # and a lip all along it
        for dy, dx, mine, theirs in ((0, -1, (slice(None), 0), (slice(None), 7)), (-1, 0, (0, slice(None)), (7, slice(None))),
                                     (0, 1, (slice(None), 7), (slice(None), 0)), (1, 0, (7, slice(None)), (0, slice(None)))):
            yy, xx = y + dy, x + dx
            if not (0 <= yy < H8 and 0 <= xx < W8): continue
            if region[yy, xx] and (yy, xx) not in cur: continue                 # not drawn yet
            nim, ntr = img_at(yy, xx)
            a_im = IM[(slice(None),) + mine]; a_tr = TR[(slice(None),) + mine]
            b_im = nim[theirs]; b_tr = ntr[theirs]
            cost += 40.0 * (a_tr != b_tr[None]).sum(1)                        # water outline carries on
            both = ~a_tr & ~b_tr[None]
            cost += (((a_im - b_im[None]) ** 2).sum(2) * both).sum(1) / 300.0   # colours carry on
        cost += mixed * 15.0 * np.array([used[k] for k in keys]) ** 0.5 + rng.random(len(keys)) * 8   # vary the shore pieces
        j = int(cost.argmin()); k = keys[j]
        GA[y][x] = k; GB[y][x] = (0, 0); GC[y][x] = col_of[k]
        cur[(y, x)] = (IM[j], TR[j]); used[k] += 1
    return int(region.sum())
