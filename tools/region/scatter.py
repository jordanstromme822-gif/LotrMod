"""Scatter the game's own small props over a whole region's open ground (Isengard's valley floor), 2026-11-25.

python3 tools/region/scatter.py PROPS.pkl MTN_DIR PACK.json CONFIG.json OUT_DIR

The Ring block got its props by hand and by props.py's scatter; the plain round it (north to the hills, the west and
south) stayed bare for long walks, against the region rule 'something every 30-60 s of walking'. This runs after
mountains.py on its output (MTN_DIR/region.pkl: mountain, water and drop spots are key tiles and blocked, so they are
never 'plain') and drops props from PROPS.pkl (tools/region/props_scan.py) with props.py's rules: every spot under a
prop and one spot round it plain, walkable, off the roads, nothing above; spaced from each other; the same prop not
too near itself; and each prop only uses tiles every tile-set zone it shows in already loads (PACK.json 'zones' and
'margin'), so the scatter never costs VRAM. CONFIG: {"skip": [[x0, y0, x1, y1] px, ...] (left alone, e.g. the Ring),
"keep_clear": [[x, y, r] px, ...] (spawns, doors), "groups": [{"ids", "count", "spacing", "same_spacing", "max_each",
"seed"}, ...]}. OUT_DIR gets MTN_DIR's files with the new region.pkl and scatter.json (placed: [[prop, x, y] px top-left, ...]). Pick props that stand out from the ground: many small props are faint ground marks that vanish in play (v268 swapped most of them for stumps, rocks, logs and wrecks).
"""
import collections, json, os, pickle, random, shutil, sys
import numpy as np
props_path, mdir, pack_path, cfg_path, out = sys.argv[1:6]
P = pickle.load(open(props_path, 'rb')); C = json.load(open(cfg_path)); PK = json.load(open(pack_path))
os.makedirs(out, exist_ok=True)
for f in os.listdir(mdir):
    if f not in ('region.pkl', 'region.png'): shutil.copy(os.path.join(mdir, f), os.path.join(out, f))
R = pickle.load(open(os.path.join(mdir, 'region.pkl'), 'rb')); GA, GB, GC, RR = R['GA'], R['GB'], R['GC'], R.get('road')
H8, W8 = len(GA), len(GA[0])
use = collections.defaultdict(collections.Counter)
for ra, rb, rc in zip(GA, GB, GC):
    for a, b, c in zip(ra, rb, rc):
        if b[0] == 0: use[a][(c or 0) & 7] += 1
walk = {k for k, c in use.items() if sum(c.values()) >= 50 and c[0] > 0.95 * sum(c.values())}
skip = np.zeros((H8, W8), bool)
for x0, y0, x1, y1 in C.get('skip', []): skip[max(0, y0 // 8):y1 // 8, max(0, x0 // 8):x1 // 8] = True
for x, y, r in C.get('keep_clear', []) + [[b[0], b[1], 64] for b in PK.get('orc_bands', [])] + [[w[0], w[1], 96] for w in PK.get('wolves', [])]:
    r8 = r // 8; skip[max(0, y // 8 - r8):y // 8 + r8 + 1, max(0, x // 8 - r8):x // 8 + r8 + 1] = True
taken = np.zeros((H8, W8), bool)
def plain(y, x):
    return (0 <= y < H8 and 0 <= x < W8 and not skip[y, x] and not taken[y, x] and not (RR is not None and RR[y][x])
            and GB[y][x][0] == 0 and (GC[y][x] or 0) == 0 and GA[y][x] in walk)
# tile sets per zone (32 px cell rows, with the pack's margin), as pack.py loads them
ZM = PK.get('margin', 8); zsets = []
for a_, b_ in PK['zones']:
    rows = range(max(0, (a_ - ZM) * 4), min(H8, (b_ + ZM) * 4))
    zsets.append((a_ - ZM, b_ + ZM, {GA[y][x][0] for y in rows for x in range(W8) if GA[y][x]}, {GB[y][x][0] for y in rows for x in range(W8)}))
def free(p, y0):
    ta = {t[0] for r in p['A'] for t in r if t}; tb = {t[0] for r in p['B'] for t in r if t[0]}
    c0, c1 = y0 // 4, (y0 + len(p['A']) - 1) // 4
    return all(ta <= za and tb <= zb for lo, hi, za, zb in zsets if c0 < hi and c1 >= lo)
def getp(i): return P[i] if isinstance(i, int) else next(q for q in P if q.get('name') == i)
centres, placed_at, log = [], collections.defaultdict(list), []
for grp in C['groups']:
    rnd = random.Random(grp.get('seed', 1)); d8 = grp['spacing'] / 8; sd = grp.get('same_spacing', 0) / 8; n = 0
    for _ in range(grp['count'] * 300):
        if n >= grp['count']: break
        i = rnd.choice(grp['ids']); p = getp(i); h, w = len(p['A']), len(p['A'][0])
        y0, x0 = rnd.randrange(1, H8 - h - 1), rnd.randrange(1, W8 - w - 1)
        cy, cx = y0 + h // 2, x0 + w // 2
        if any((cy - a) ** 2 + (cx - b) ** 2 < d8 * d8 for a, b in centres): continue
        if len(placed_at[i]) >= grp.get('max_each', 1 << 30) or any((y0 - a) ** 2 + (x0 - b) ** 2 < sd * sd for a, b in placed_at[i]): continue
        if not all(plain(y0 + y, x0 + x) for y in range(-1, h + 1) for x in range(-1, w + 1)): continue
        if not free(p, y0): continue
        for y in range(h):
            for x in range(w):
                if p['A'][y][x] is None and p['B'][y][x][0] == 0: continue
                a = None if p.get('tmask') and p['tmask'][y][x] else p['A'][y][x]
                if a is None: a = GA[y0 + y][x0 + x]   # see-through lower tile: the ground already there shows through
                GA[y0 + y][x0 + x] = a; GB[y0 + y][x0 + x] = p['B'][y][x]; GC[y0 + y][x0 + x] = p['C'][y][x] if p['C'][y][x] is not None else GC[y0 + y][x0 + x]
                taken[y0 + y, x0 + x] = True
        placed_at[i].append((y0, x0)); centres.append((cy, cx)); log.append([i, x0 * 8, y0 * 8]); n += 1
    print('group', grp['ids'][:4], '...', n)
pickle.dump(R, open(os.path.join(out, 'region.pkl'), 'wb'))
json.dump(dict(placed=log), open(os.path.join(out, 'scatter.json'), 'w'))
print('scattered', len(log))
