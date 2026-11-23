"""Place the game's own props (tools/region/props_scan.py) in a region block (2026-11-23).

python3 tools/region/props.py PROPS.pkl PLACE.json OUT.pkl

PLACE.json: {"w": cells, "h": cells, "centre8": [x8, y8], "props": [[index or cut name, dx, dy, "note"], ...]} with dx, dy the
prop's top-left in px from centre8 (snapped to 8 px). Each prop keeps its own tiles and collision; the spots around
it stay open (None), so the region tool grows its ground up to it. Props must not overlap (checked).
Optional "scatter": [{"ids": [...], "count": n, "spacing": px, "seed": s}, ...] with "region": a region.pkl built
without these props, "cell": this block's region cell and "radius": px from centre8: small things dropped at random
on plain ground only (every spot under them and one spot round them plain, walkable, nothing above), at least
"spacing" px from each other and from every placed prop, so the game's small props break up open ground.
"""
import json, pickle, random, sys
props_path, place_path, out = sys.argv[1:4]
P = pickle.load(open(props_path, 'rb')); C = json.load(open(place_path))
W, H = C['w'], C['h']; cx8, cy8 = C['centre8']
BL = (0, 0)
GA = [[None] * (W * 4) for _ in range(H * 4)]; GB = [[BL] * (W * 4) for _ in range(H * 4)]; GC = [[None] * (W * 4) for _ in range(H * 4)]
used = {}
for i, dx, dy, *note in C['props']:
    p = P[i] if isinstance(i, int) else next(q for q in P if q.get('name') == i); x0, y0 = cx8 + round(dx / 8), cy8 + round(dy / 8)
    for y, row in enumerate(p['A']):
        for x, a in enumerate(row):
            if a is None and p['B'][y][x][0] == 0: continue
            yy, xx = y0 + y, x0 + x
            assert 0 <= yy < H * 4 and 0 <= xx < W * 4, (i, 'off the block')
            assert (yy, xx) not in used, ('overlap', i, used.get((yy, xx)))
            used[(yy, xx)] = i
            if p.get('tmask') and p['tmask'][y][x]: a = None    # see-through lower tile: let the ground grow there instead
            GA[yy][xx] = a; GB[yy][xx] = p['B'][y][x]; GC[yy][xx] = p['C'][y][x] if a is not None or p['B'][y][x][0] else None
def getp(i): return P[i] if isinstance(i, int) else next(q for q in P if q.get('name') == i)
if C.get('scatter'):
    R = pickle.load(open(C['region'], 'rb')); RA, RB, RC = R['GA'], R['GB'], R['GC']
    bx, by = C['cell'][0] * 4, C['cell'][1] * 4
    import collections
    use = collections.defaultdict(collections.Counter)
    for row_a, row_b, row_c in zip(RA, RB, RC):
        for a, b, c in zip(row_a, row_b, row_c):
            if b[0] == 0: use[a][c & 7] += 1
    walk = {k for k, c in use.items() if sum(c.values()) >= 50 and c[0] > 0.95 * sum(c.values())}
    def plain(yy, xx):
        y, x = by + yy, bx + xx
        return 0 <= y < len(RA) and 0 <= x < len(RA[0]) and RB[y][x][0] == 0 and RC[y][x] == 0 and RA[y][x] in walk and (yy, xx) not in used
    centres = [(y, x) for (y, x) in used]
    # "zones" (+ "zone_margin", "zone_region": a region.pkl built WITH the hand-placed props): a scattered prop may only
    # use tiles each tile-set zone it shows in already loads, so scatter never costs VRAM (pack.py's per-zone budget)
    zsets = []
    if C.get('zones'):
        ZR = pickle.load(open(C['zone_region'], 'rb')); ZM = C.get('zone_margin', 8)
        for a_, b_ in C['zones']:
            rows = range(max(0, (a_ - ZM) * 4), min(len(ZR['GA']), (b_ + ZM) * 4))
            zsets.append((a_ - ZM, b_ + ZM, {ZR['GA'][y][x][0] for y in rows for x in range(len(ZR['GA'][0]))},
                          {ZR['GB'][y][x][0] for y in rows for x in range(len(ZR['GA'][0]))}))
    def free(p, y0):
        ta = {t[0] for r in p['A'] for t in r if t}; tb = {t[0] for r in p['B'] for t in r if t[0]}
        c0, c1 = (by + y0) // 4, (by + y0 + len(p['A']) - 1) // 4
        return all(ta <= za and tb <= zb for lo, hi, za, zb in zsets if c0 < hi and c1 >= lo)
    placed_at = collections.defaultdict(list)
    def far(y, x, d8): return all((y - a) ** 2 + (x - b) ** 2 >= d8 * d8 for a, b in centres)
    for grp in C['scatter']:
        rnd = random.Random(grp.get('seed', 1)); d8 = grp['spacing'] / 8; r8 = C['radius'] / 8; n = 0
        for _ in range(grp['count'] * 400):
            if n >= grp['count']: break
            i = rnd.choice(grp['ids']); p = getp(i); h, w = len(p['A']), len(p['A'][0])
            y0, x0 = cy8 + rnd.randint(-int(r8), int(r8)), cx8 + rnd.randint(-int(r8), int(r8))
            if (y0 + h / 2 - cy8) ** 2 + (x0 + w / 2 - cx8) ** 2 > r8 * r8: continue
            if not far(y0 + h // 2, x0 + w // 2, d8): continue
            if not all(plain(y0 + y, x0 + x) for y in range(-1, h + 1) for x in range(-1, w + 1)): continue
            if zsets and not free(p, y0): continue
            sd = grp.get('same_spacing', 0) / 8                  # the same prop no nearer than this to itself
            if any((y0 - a) ** 2 + (x0 - b) ** 2 < sd * sd for a, b in placed_at[i]): continue
            if len(placed_at[i]) >= grp.get('max_each', 1 << 30): continue
            placed_at[i].append((y0, x0))
            for y in range(h):
                for x in range(w):
                    if p['A'][y][x] is None and p['B'][y][x][0] == 0: continue
                    a = None if p.get('tmask') and p['tmask'][y][x] else p['A'][y][x]
                    GA[y0 + y][x0 + x] = a; GB[y0 + y][x0 + x] = p['B'][y][x]; GC[y0 + y][x0 + x] = p['C'][y][x] if a is not None or p['B'][y][x][0] else None; used[(y0 + y, x0 + x)] = i
            centres.append((y0 + h // 2, x0 + w // 2)); n += 1
        print('scatter', grp['ids'], n)
print('props placed', len(C['props']), 'spots', len(used))
pickle.dump(dict(GA=GA, GB=GB, GC=GC, W=W, H=H), open(out, 'wb'))
