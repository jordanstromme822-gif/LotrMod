"""Close open water at a joined map's edges with the levels' own shore cells (32 px), so the water of a map that runs
off its edge goes on a little way and ends in a real shoreline instead of a straight cut.

lake.solve(world, fixed, cands, pixels, rgb, ...) fills a band of empty cells next to wet edges. Every placed cell
must continue its neighbours' water outline along the shared edge (transparent pixels within a few pixels), and the
band's outer side must be dry land so the plain ground fill can take over from there.
"""
import collections
import numpy as np
from cells import cell_img


def edges(img, tr):
    return dict(n=(tr[0], img[0]), s=(tr[31], img[31]), w=(tr[:, 0], img[:, 0]), e=(tr[:, 31], img[:, 31]))


OPP = dict(n='s', s='n', w='e', e='w')
STEP = dict(n=(-1, 0), s=(1, 0), w=(0, -1), e=(0, 1))


def prep(cands, pixels, rgb):
    IM, TR = [], []
    for c in cands:
        i, t = cell_img(c, pixels, rgb); IM.append(i.astype(np.float32)); TR.append(t)
    IM = np.stack(IM); TR = np.stack(TR)
    E = {k: (TR[:, 0], IM[:, 0]) if k == 'n' else (TR[:, 31], IM[:, 31]) if k == 's' else (TR[:, :, 0], IM[:, :, 0]) if k == 'w' else (TR[:, :, 31], IM[:, :, 31]) for k in 'nswe'}
    return IM, TR, E


def solve(world, fixed, H, W, cands, pixels, rgb, depth=6, blocked=frozenset(), tol=3, rng=None, log=print, land_ok=None):
    rng = rng or np.random.default_rng(3)
    IM, TR, E = prep(cands, pixels, rgb)
    wet = TR.reshape(len(cands), -1).mean(1)
    if land_ok is None: land_ok = np.ones(len(cands), bool)
    # seeds: empty cells whose fixed neighbour shows water on the shared edge
    seeds = set()
    for y in range(H):
        for x in range(W):
            if not fixed[y][x] or world[y][x] is None: continue
            img, tr = cell_img(world[y][x], pixels, rgb)
            for k, (dy, dx) in STEP.items():
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and not fixed[yy][xx] and (yy, xx) not in blocked and edges(img, tr)[k][0].any():
                    seeds.add((yy, xx))
    dist = {p: 0 for p in seeds}; q = collections.deque(seeds)
    while q:
        y, x = q.popleft()
        if dist[(y, x)] >= depth - 1: continue
        for dy, dx in STEP.values():
            p = (y + dy, x + dx)
            if 0 <= p[0] < H and 0 <= p[1] < W and not fixed[p[0]][p[1]] and p not in dist and p not in blocked:
                dist[p] = dist[(y, x)] + 1; q.append(p)
    band = sorted(dist, key=lambda p: (dist[p], p))
    # target water amount per band cell: deep near the map, gone at a reach that wobbles smoothly along the edge
    nz = rng.normal(0, 1, (H + 8, W + 8))
    for _ in range(6): nz = (nz + np.roll(nz, 1, 0) + np.roll(nz, -1, 0) + np.roll(nz, 1, 1) + np.roll(nz, -1, 1)) / 5
    nz = (nz - nz.mean()) / (nz.std() + 1e-9)
    target = {p: float(np.clip(1.0 - (dist[p] + 0.5) / max(0.8, 2.2 + 1.6 * nz[p[0] + 4, p[1] + 4]), 0, 1)) for p in dist}
    inband = set(band)
    log('lake band cells', len(band), 'seeds', len(seeds))
    placed = {}
    used = collections.Counter()

    def options(p):
        y, x = p
        cost = np.zeros(len(cands)); ok = land_ok.copy()
        for k, (dy, dx) in STEP.items():
            yy, xx = y + dy, x + dx
            if not (0 <= yy < H and 0 <= xx < W): continue
            nb = placed.get((yy, xx))
            if nb is None and fixed[yy][xx] and world[yy][xx] is not None: nb = world[yy][xx]
            mt, mi = E[k]
            if nb is not None:
                img, tr = cell_img(nb, pixels, rgb)
                ntr, nim = edges(img.astype(np.float32), tr)[OPP[k]]
                ok &= (mt != ntr[None]).sum(1) <= tol
                cost += ((mi - nim[None]) ** 2).mean((1, 2))
            elif (yy, xx) not in inband:
                ok &= ~mt.any(1)                  # facing the plain ground: dry edge
        t = target[p]
        cost += 3000 * np.abs(wet - t)            # follow a smooth, wobbly water shape (organic shoreline)
        cost += 60 * np.array([used[c] for c in cands]) ** 0.5
        cost += rng.random(len(cands)) * 20
        cost[~ok] = np.inf
        return np.argsort(cost)[:6], cost

    stack = []; i = 0; tries = collections.Counter(); fails = 0
    while i < len(band):
        p = band[i]
        if p not in [s[0] for s in stack[-1:]] or True:
            order, cost = options(p)
            order = [j for j in order if np.isfinite(cost[j])]
        k = tries[p]
        if k < len(order):
            j = order[k]; placed[p] = cands[j]; used[cands[j]] += 1; stack.append((p, j)); i += 1
        else:
            # dead end: step back a little (each cell gets a few tries), else leave this cell to the plain fill
            tries[p] = 0
            if stack and fails < 4000:
                fails += 1
                q_, j_ = stack.pop(); used[cands[j_]] -= 1; del placed[q_]; tries[q_] += 1; i -= 1
            else:
                log('lake: no fit at', p); i += 1
    log('lake placed', len(placed), 'backtracks', fails)
    return placed
