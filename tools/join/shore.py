"""Tile-level (8 px) re-solve of the water edges near the joined seams. Each tile is chosen to (a) sit next to tiles it
sits next to somewhere in the game's own maps (a pair never seen there costs a lot, more the worse its pixels meet),
(b) follow the planned pool shapes (DW). Greedy fill, then a few passes that re-pick every tile given all neighbours."""
import collections, numpy as np
from build import pix

def tile_px(t, pixels, rgb):
    p = pix(pixels[t[0]])
    if t[1] & 0x400: p = p[:, ::-1]
    if t[1] & 0x800: p = p[::-1]
    c = rgb[(t[1] >> 12) * 16 + p].astype(np.float32); c[p == 0] = -200.0
    return c, p == 0

def adjacency(grids_A, pixels, rgb):
    F, C = collections.Counter(), {}
    pairsH, pairsV = set(), set()
    for G, Cg in grids_A:
        for y in range(len(G)):
            for x in range(len(G[0])):
                k = G[y][x]; F[k] += 1; C.setdefault(k, collections.Counter())[Cg[y][x]] += 1
                if x + 1 < len(G[0]): pairsH.add((k, G[y][x + 1]))
                if y + 1 < len(G): pairsV.add((k, G[y + 1][x]))
    keys = list(F); ki = {k: i for i, k in enumerate(keys)}; n = len(keys)
    OH = np.zeros((n, n), bool); OV = np.zeros((n, n), bool)
    for a, b in pairsH: OH[ki[a], ki[b]] = True
    for a, b in pairsV: OV[ki[a], ki[b]] = True
    PX = np.stack([tile_px(k, pixels, rgb)[0] for k in keys]); MK = np.stack([tile_px(k, pixels, rgb)[1] for k in keys]).reshape(n, -1)
    col = {k: c.most_common(1)[0][0] for k, c in C.items()}
    return dict(keys=keys, ki=ki, OH=OH, OV=OV, PX=PX, MK=MK, logf=np.log(np.array([F[k] for k in keys], np.float32)), col=col)

def solve(GA, zone, DW, adj, seed=0, passes=4, pixels=None, rgb=None):
    keys, ki, OH, OV, PX, MK, logf = adj['keys'], adj['ki'], adj['OH'], adj['OV'], adj['PX'], adj['MK'], adj['logf']
    n = len(keys); rng = np.random.default_rng(seed)
    H8, W8 = len(GA), len(GA[0])
    extra = {}
    def px_of(v):
        if v in ki: return PX[ki[v]]
        if v not in extra: extra[v] = tile_px(v, pixels, rgb)[0]
        return extra[v]
    val = {}
    def cur(q):
        if q in zone: return val.get(q)
        return GA[q[0]][q[1]]
    def cost_at(p):
        y, x = p; c = np.zeros(n, np.float32)
        want = DW[y * 8:y * 8 + 8, x * 8:x * 8 + 8].reshape(-1)
        c += 1.2 * (MK != want[None]).sum(1)
        c -= 0.4 * logf
        for dy, dx in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            q = (y + dy, x + dx)
            if not (0 <= q[0] < H8 and 0 <= q[1] < W8): continue
            v = cur(q)
            if v is None: continue
            pv = px_of(v)
            if dx == -1: e = np.abs(PX[:, :, 0] - pv[:, 7][None]).mean((1, 2)); ok = OH[ki[v]] if v in ki else None
            elif dx == 1: e = np.abs(PX[:, :, 7] - pv[:, 0][None]).mean((1, 2)); ok = OH[:, ki[v]] if v in ki else None
            elif dy == -1: e = np.abs(PX[:, 0] - pv[7][None]).mean((1, 2)); ok = OV[ki[v]] if v in ki else None
            else: e = np.abs(PX[:, 7] - pv[0][None]).mean((1, 2)); ok = OV[:, ki[v]] if v in ki else None
            pen = 160.0 + e * 1.0
            c += pen if ok is None else np.where(ok, 0.0, pen)
        return c
    order = sorted(zone, key=lambda p: (p[0], p[1]))
    # greedy: grow from the zone's border inwards (tiles with most known neighbours first)
    open_ = set(zone)
    def known(p): return sum(1 for d in ((0, -1), (0, 1), (-1, 0), (1, 0)) if (0 <= p[0] + d[0] < H8 and 0 <= p[1] + d[1] < W8) and cur((p[0] + d[0], p[1] + d[1])) is not None)
    import heapq
    heap = [(-known(p), rng.random(), p) for p in open_]; heapq.heapify(heap)
    while heap:
        kn, _, p = heapq.heappop(heap)
        if p not in open_: continue
        if -kn != known(p): heapq.heappush(heap, (-known(p), rng.random(), p)); continue
        c = cost_at(p) + rng.random(n) * 0.5
        val[p] = keys[int(c.argmin())]; open_.discard(p)
        for d in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            q = (p[0] + d[0], p[1] + d[1])
            if q in open_: heapq.heappush(heap, (-known(q), rng.random(), q))
    for it in range(passes):
        changed = 0
        for p in rng.permutation(len(order)):
            p = order[p]; c = cost_at(p); k = keys[int(c.argmin())]
            if k != val[p]: val[p] = k; changed += 1
        if not changed: break
    bad = 0
    for p in zone:
        y, x = p
        for dy, dx in ((0, 1), (1, 0)):
            q = (y + dy, x + dx)
            if not (0 <= q[0] < H8 and 0 <= q[1] < W8): continue
            a, b = cur(p), cur(q)
            if a in ki and b in ki and not (OH if dx else OV)[ki[a], ki[b]]: bad += 1
    return val, adj['col'], bad
