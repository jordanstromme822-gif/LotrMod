"""Plain ground in the new space between joined maps, redrawn 8 px tile by 8 px tile the way the game's own maps put
their gravel tiles next to each other (2026-11-22). The 32 px gravel cells repeat and mirror in a visible grid when
laid side by side; picking each 8 px tile from the pairs seen in the maps (left neighbour, upper neighbour, and any
fixed map tile on the right or below) gives the same loose, unpatterned look as the maps.
"""
import collections
import numpy as np


def pair_counts(srcA):
    Hc = collections.Counter(); Vc = collections.Counter()
    for A_ in srcA:
        for y in range(len(A_)):
            for x in range(len(A_[0])):
                if x + 1 < len(A_[0]): Hc[(A_[y][x], A_[y][x + 1])] += 1
                if y + 1 < len(A_): Vc[(A_[y][x], A_[y + 1][x])] += 1
    return Hc, Vc


def synth(GA, GB, GC, spots, gkeys, srcA, col_of, blank, seed=5, log=print):
    rng = np.random.default_rng(seed)
    Hc, Vc = pair_counts(srcA)
    gk = list(gkeys); gi = {k: i for i, k in enumerate(gk)}
    base = np.array([sum(Hc[(a, k)] for a in gk) + 1 for k in gk], np.float64)   # how common each tile is
    cacheH, cacheV, cacheHr, cacheVr = {}, {}, {}, {}
    def w(cache, key, f):
        if key not in cache: cache[key] = f()
        return cache[key]
    spots = sorted(spots); sset = set(spots)
    used = collections.Counter()
    for y, x in spots:
        p = np.ones(len(gk))
        terms = 0
        for (dy, dx, cache, mk) in ((0, -1, cacheH, lambda a: np.array([Hc[(a, k)] for k in gk], np.float64)),
                                    (-1, 0, cacheV, lambda a: np.array([Vc[(a, k)] for k in gk], np.float64)),
                                    (0, 1, cacheHr, lambda a: np.array([Hc[(k, a)] for k in gk], np.float64)),
                                    (1, 0, cacheVr, lambda a: np.array([Vc[(k, a)] for k in gk], np.float64))):
            yy, xx = y + dy, x + dx
            if not (0 <= yy < len(GA) and 0 <= xx < len(GA[0])): continue
            if (yy, xx) in sset and (dy > 0 or dx > 0): continue       # not drawn yet
            a = GA[yy][xx]
            v = w(cache, a, lambda: mk(a))
            if v.sum() == 0: continue
            p = p * (v + 0.05 * v.sum() / len(gk)); terms += 1
        if terms == 0: p = base.copy()
        p = p / p.sum()
        j = rng.choice(len(gk), p=p); k = gk[j]
        GA[y][x] = k; GB[y][x] = blank; GC[y][x] = col_of[k]; used[k] += 1
    log('gravel spots', len(spots), 'tiles used', len(used))
