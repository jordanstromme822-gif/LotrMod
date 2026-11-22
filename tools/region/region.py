"""Build a whole region's ground (2026-11-22, Jordan: "connect the regions with a flat traversable space like we did
with the flooded fields, based off each region's terrain and textures, and a map accurate border between regions").

python3 tools/region/region.py ROM CONFIG.json OUT_DIR

CONFIG names the region's land mask (from the border map, picture 19: own.npy on a 100 px grid), the blocks placed in it
(a level, or an already joined world.pkl) at their 3D World cells, and the ground tones. Output: region.pkl (8 px grids
GA/GB/GC + where every block sits), region.png (the whole region), zoom crops.

How the ground is made:
- Outside the land: nothing (blocked, see-through), as past any map edge in the game.
- Next to each block (2 cells): 8 px tiles picked one by one from the tile pairs the game's own maps use (gravel8), so the
  ground grows out of the map with no seam; things the map edge cut through are cleared first (edge cleanup below), and
  water that runs off an edge ends in a real shore (shore8).
- Everywhere else: whole 32 px cells from a pool of ~1,600 ground cells made the same 8 px way, each placed where its
  edge tiles best continue its neighbours' (the same pair statistics), never the same cell twice in a row. The pool keeps
  the number of different cells (and the game file) small while the ground never shows a grid or a repeat pattern.
- Ground tone per area: each block's own gravel near it, blended over a wide, irregular band between tones.
"""
import collections, json, os, pickle, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'join')); sys.path.insert(0, os.path.join(HERE, '..', 'siege'))
from cells import load, cell_img, BLANK, pix
import gravel8, shore8
import build

rom, cfg_path, out = sys.argv[1:4]
CFG = json.load(open(cfg_path))
os.makedirs(out, exist_ok=True)
levels = sorted({b['level'] for b in CFG['blocks'] if 'level' in b} | set(CFG.get('source_levels', [])))
R, lv, rgb, grids, pixels = load(rom, levels)

# ---- land (cells, relative to the region origin) --------------------------------------------------------------------
own = np.load(CFG['own']); G, X0, Y0 = CFG['grid']
RX, RY = CFG['origin_px']                     # layout px of cell (0, 0) before trimming
ys, xs = np.where(own == CFG['index'])
bx0, by0 = (X0 + xs.min() * G - RX) // 32 - 1, (Y0 + ys.min() * G - RY) // 32 - 1
bx1, by1 = (X0 + (xs.max() + 1) * G - RX) // 32 + 2, (Y0 + (ys.max() + 1) * G - RY) // 32 + 2
blocks = []
for b in CFG['blocks']:
    if 'level' in b:
        g = grids[b['level']]; h, w = len(g), len(g[0])
        A8 = [[None] * (w * 4) for _ in range(h * 4)]; B8 = [[None] * (w * 4) for _ in range(h * 4)]; C8 = [[1] * (w * 4) for _ in range(h * 4)]
        for y, row in enumerate(g):
            for x, c in enumerate(row):
                for k in range(16): A8[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]; B8[y * 4 + k // 4][x * 4 + k % 4] = c[1][k]; C8[y * 4 + k // 4][x * 4 + k % 4] = c[2][k]
    else:
        d = pickle.load(open(b['pkl'], 'rb')); A8, B8, C8 = d['GA'], d['GB'], d['GC']; w, h = d['W'], d['H']
    blocks.append(dict(b, A8=A8, B8=B8, C8=C8, w=w, h=h))
    bx0, by0 = min(bx0, b['cell'][0]), min(by0, b['cell'][1]); bx1, by1 = max(bx1, b['cell'][0] + w), max(by1, b['cell'][1] + h)
W, H = bx1 - bx0, by1 - by0
print('region', CFG['name'], 'cells', W, H)
for b in blocks: b['x'], b['y'] = b['cell'][0] - bx0, b['cell'][1] - by0
cx = np.arange(W); cy = np.arange(H)
gx = ((RX + (cx + bx0) * 32 + 16 - X0) // G).clip(0, own.shape[1] - 1); gy = ((RY + (cy + by0) * 32 + 16 - Y0) // G).clip(0, own.shape[0] - 1)
# land: the border map's 100 px grid blurred and sampled per cell, so its outline is a smooth curve, not steps
from scipy import ndimage
soft = ndimage.gaussian_filter((own == CFG['index']).astype(np.float32), 2.0)
fx = (RX + (cx + bx0) * 32 + 16 - X0) / G - 0.5; fy = (RY + (cy + by0) * 32 + 16 - Y0) / G - 0.5
land = ndimage.map_coordinates(soft, np.meshgrid(fy, fx, indexing='ij'), order=1) > 0.5
inblock = np.zeros((H, W), int) - 1
for i, b in enumerate(blocks): inblock[b['y']:b['y'] + b['h'], b['x']:b['x'] + b['w']] = i
land |= inblock >= 0


# ---- 8 px grids ---------------------------------------------------------------------------------------------------
H8, W8 = H * 4, W * 4
VOID = (BLANK, 0)
GA = [[VOID] * W8 for _ in range(H8)]; GB = [[VOID] * W8 for _ in range(H8)]; GC = [[1] * W8 for _ in range(H8)]
fixed8 = np.zeros((H8, W8), bool)
for b in blocks:
    for y in range(b['h'] * 4):
        for x in range(b['w'] * 4):
            GA[b['y'] * 4 + y][b['x'] * 4 + x] = b['A8'][y][x]; GB[b['y'] * 4 + y][b['x'] * 4 + x] = b['B8'][y][x]; GC[b['y'] * 4 + y][b['x'] * 4 + x] = b['C8'][y][x]
    fixed8[b['y'] * 4:(b['y'] + b['h']) * 4, b['x'] * 4:(b['x'] + b['w']) * 4] = True
land8 = np.kron(land, np.ones((4, 4), bool))
# notches (8 px): void beyond a block side span, for things that run off the edge and can't be ended there (Orthanc's
# top): straight on from the span, closing in a half ellipse. A 'water' notch is a pool instead (the flood water of
# Isengard behind Orthanc: the tower's top stands against the water, as its top already shows the backdrop between
# its horns), closed by real shores (shore8).
water_notch = []
for b in blocks:
    for side, a0, a1, depth, *kind in b.get('notch', []):
        if kind and kind[0] == 'water': water_notch.append((b, side, a0, a1, depth)); continue
        a0, a1, dep = a0 * 4, a1 * 4, depth * 4; half = (a1 - a0) / 2.0; mid = (a0 + a1) / 2.0
        straight = dep // 3
        for k in range(dep):
            e = 0 if k < straight else (k - straight) / max(1, dep - straight)
            hw = half * np.sqrt(max(0.0, 1 - e * e))
            lo, hi = int(round(mid - hw)), int(round(mid + hw))
            if hi <= lo: continue
            if side == 'n': land8[b['y'] * 4 - 1 - k, b['x'] * 4 + lo:b['x'] * 4 + hi] = False
            if side == 's': land8[(b['y'] + b['h']) * 4 + k, b['x'] * 4 + lo:b['x'] * 4 + hi] = False
            if side == 'w': land8[b['y'] * 4 + lo:b['y'] * 4 + hi, b['x'] * 4 - 1 - k] = False
            if side == 'e': land8[b['y'] * 4 + lo:b['y'] * 4 + hi, (b['x'] + b['w']) * 4 + k] = False
land8 |= fixed8
open8 = land8 & ~fixed8                        # new ground to draw

# ---- tile statistics per tone ---------------------------------------------------------------------------------------
def src8(L):
    g = grids[L]; A_ = [[None] * (len(g[0]) * 4) for _ in range(len(g) * 4)]
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            for k in range(16): A_[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]
    return A_
col_votes = collections.defaultdict(collections.Counter); src_count = collections.Counter()
for L in levels:
    for row in grids[L]:
        for c in row:
            for k in range(16): col_votes[c[0][k]][c[2][k]] += 1; src_count[c[0][k]] += 1
col_of = {k: v.most_common(1)[0][0] for k, v in col_votes.items()}
def tpx(k): return shore8.tile_px(k, pixels, rgb)
def plain_cell(c):                              # a cell of plain walkable ground: nothing on top, no water, walkable
    if any(t[0] != BLANK for t in c[1]) or any((v & 7) in (1, 2) for v in c[2]): return False
    im, tr = cell_img(c, pixels, rgb)
    if tr.any(): return False
    lum = im.mean(-1); r, g, b_ = im[..., 0], im[..., 1], im[..., 2]
    if (g > r + 10).mean() > 0.01 or ((r > 140) & (g > 130) & (b_ < 120)).mean() > 0.01 or (lum < 40).mean() > 0.06: return False
    if (lum > 130).mean() > 0.03: return False                # light road bricks are not plain ground
    return True
tones = {}
for name, t in CFG['tones'].items():
    cnt = collections.Counter(c for L in t['levels'] for row in grids[L] for c in row)
    top = [c for c, n in cnt.most_common() if plain_cell(c)][:t.get('top', 12)]
    keys = {k for c in top for k in c[0]}
    cols = {tuple(int(u) for u in v) for k in keys for v in tpx(k)[0].reshape(-1, 3)}
    def gk_ok(k, cols=cols):
        im, tr = tpx(k)
        if tr.any() or not all(tuple(int(u) for u in v) in cols for v in im.reshape(-1, 3)): return False
        return (im @ np.array([.3, .59, .11], np.float32) < 70).sum() <= 10
    allk = {k for L in t['levels'] for row in grids[L] for c in row for k in c[0] if src_count[k]}
    allpx = np.concatenate([cell_img(c, pixels, rgb)[0].reshape(-1, 3) for c in top]).astype(np.float32)
    med = np.median(allpx, 0); spread = np.percentile(np.linalg.norm(allpx - med, axis=1), 99)
    def calm(k):                                  # no road-brick bits or odd specks: colours near this ground's own
        im, tr = tpx(k)
        if tr.any() or (np.linalg.norm(im.reshape(-1, 3) - med, axis=1) > spread).sum() > 2: return False
        q = im.reshape(-1, 3).astype(np.float32); warm = (q[:, 0] + q[:, 1]) / 2 - q[:, 2]
        if ((warm > 18) & (q[:, 0] > 110)).any(): return False          # road-brick beige
        medwarm = (med[0] + med[1]) / 2 - med[2]
        return ((-warm > 25).sum() <= 4) and warm.mean() > medwarm - 7   # blue blots (water rim pieces)
    gkeys = sorted(k for k in (allk if t.get('wide') else keys) if (k in keys or gk_ok(k)) and calm(k))
    tones[name] = dict(keys=gkeys, src=[src8(L) for L in t['levels']], cols=cols, levels=t['levels'])
    print('tone', name, 'plain cells', len(top), 'gravel tiles', len(gkeys))

# ---- which tone where: nearest block's tone, with a noisy blend band -------------------------------------------------
dist_b = np.full((len(blocks), H, W), 1e9)
for i, b in enumerate(blocks):
    m = np.ones((H, W), bool); m[b['y']:b['y'] + b['h'], b['x']:b['x'] + b['w']] = False
    dist_b[i] = ndimage.distance_transform_edt(m)
rng = np.random.default_rng(CFG.get('seed', 3))
noise = ndimage.gaussian_filter(rng.normal(0, 1, (H, W)), 6); noise /= noise.std()
tone_names = list(tones)
# the first tone is the region's main ground; any other tone covers the ground within its 'radius' cells of its own
# blocks, with a wobbly (noise) outline
tone_at = np.zeros((H, W), int)
for ti, tn in enumerate(tone_names[1:], 1):
    d_ = np.min([dist_b[i] for i, b in enumerate(blocks) if b['tone'] == tn], axis=0)
    tone_at[d_ + noise * CFG.get('blend', 3) < CFG['tones'][tn].get('radius', 6)] = ti

# ---- edge cleanup: things a block edge cut through (fill.py's rules) -------------------------------------------------
def is_obj(y8, x8, gset):
    if GB[y8][x8][0] != BLANK: return True
    im, tr = tpx(GA[y8][x8])
    if tr.any(): return False
    return GA[y8][x8] not in gset
def a_obj(y8, x8, cols):
    im, tr = tpx(GA[y8][x8])
    return not tr.any() and any(tuple(int(u) for u in v) not in cols for v in im.reshape(-1, 3))
def inb(p): return 0 <= p[0] < H8 and 0 <= p[1] < W8
def flood(cells8, inside, gset):
    st = [p for p in cells8 if inb(p) and is_obj(*p, gset)]; seen = set()
    while st:
        p = st.pop()
        if p in seen or not inb(p) or not inside(p) or not fixed8[p] or not is_obj(*p, gset): continue
        seen.add(p); st += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
    return seen
def edge_objs(edge, d, lo, hi, gset, cols):
    if edge == 'w': rel = lambda p: p[1] - d; along = lambda p: lo <= p[0] < hi
    elif edge == 'e': rel = lambda p: d - p[1]; along = lambda p: lo <= p[0] < hi
    elif edge == 'n': rel = lambda p: p[0] - d; along = lambda p: lo <= p[1] < hi
    else: rel = lambda p: d - p[0]; along = lambda p: lo <= p[1] < hi
    def at(r, a): return {'w': (a, d + r), 'e': (a, d - r), 'n': (d + r, a), 's': (d - r, a)}[edge]
    out_ = set(); done = set()
    for a0 in range(lo, hi):
        o8 = {'w': (a0, d - 1), 'e': (a0, d + 1), 'n': (d - 1, a0), 's': (d + 1, a0)}[edge]
        if not (inb(o8) and open8[o8]): continue            # only where new ground lies beyond the edge
        if at(0, a0) in done: continue
        comp = flood([at(0, a0)], lambda p: along(p) and 0 <= rel(p) < 48, gset); done |= comp
        if not comp: continue
        if max(rel(p) for p in comp) < 47 and len(comp) <= 240: out_ |= comp; continue
        cut = {p for p in comp if rel(p) < 8}; keep = set()
        for a in range(lo, hi):
            r = 8
            while r >= 4 and at(r, a) in comp and (r >= 6 or a_obj(*at(r, a), cols)): keep.add(at(r, a)); r -= 1
        out_ |= cut - keep
    rest = set()
    def grow(q, ok, lim):
        seen = set(); st = [q]
        while st and len(seen) <= lim:
            r_ = st.pop()
            if r_ in seen or not ok(r_): continue
            seen.add(r_); st += [(r_[0] + 1, r_[1]), (r_[0] - 1, r_[1]), (r_[0], r_[1] + 1), (r_[0], r_[1] - 1)]
        return seen if len(seen) <= lim else set()
    for p in list(out_):
        for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if q not in out_ and q not in rest: rest |= grow(q, lambda r_: inb(r_) and r_ not in out_ and fixed8[r_] and is_obj(*r_, gset), 120)
    done_ = out_ | rest
    for p in list(done_):
        for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if q not in rest: rest |= grow(q, lambda r_: inb(r_) and fixed8[r_] and r_ not in done_ and a_obj(*r_, cols) and GB[r_[0]][r_[1]][0] == BLANK, 40)
    done_ = out_ | rest
    for p in list(done_):
        for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if q not in rest: rest |= grow(q, lambda r_: inb(r_) and fixed8[r_] and r_ not in done_ and GB[r_[0]][r_[1]][0] != BLANK and not a_obj(*r_, cols), 40)
    return out_ | rest
cutobj = set()
for b in blocks:
    tn = tones[b['tone']]; gset = set(tn['keys']); cols = tn['cols']
    x8, y8, w8, h8 = b['x'] * 4, b['y'] * 4, b['w'] * 4, b['h'] * 4
    for side in b.get('clean', 'nsew'):
        if side == 'n': cutobj |= edge_objs('n', y8, x8, x8 + w8, gset, cols)
        if side == 's': cutobj |= edge_objs('s', y8 + h8 - 1, x8, x8 + w8, gset, cols)
        if side == 'w': cutobj |= edge_objs('w', x8, y8, y8 + h8, gset, cols)
        if side == 'e': cutobj |= edge_objs('e', x8 + w8 - 1, y8, y8 + h8, gset, cols)
for b, side, a0, a1, depth in water_notch:      # what stands against a water notch stays whole (Orthanc's top)
    x0_, x1_ = b['x'] * 4 + int(a0 * 4) - 2, b['x'] * 4 + int(a1 * 4) + 2
    cutobj = {p for p in cutobj if not (x0_ <= p[1] < x1_ and p[0] < b['y'] * 4 + 16)}
print('cut edge pieces cleared', len(cutobj))
for p in cutobj: fixed8[p] = False; open8[p] = True

# ---- water that runs off a block edge: closes in a shore (shore8), the rest of the new ground stays dry ----------
DW = np.zeros((H8 * 8, W8 * 8), bool)
for y in range(H8):
    for x in range(W8):
        if fixed8[y, x] and GB[y][x][0] == BLANK: DW[y * 8:y * 8 + 8, x * 8:x * 8 + 8] = tpx(GA[y][x])[1]
nrng = np.random.default_rng(5)
def caps(line, edge_pos, outward, along0, horizontal):
    runs, i = [], 0
    while i < len(line):
        if line[i]:
            j = i
            while j < len(line) and line[j]: j += 1
            runs.append((i, j)); i = j
        else: i += 1
    for a, b_ in runs:
        r = (b_ - a) / 2.0; c = (a + b_) / 2.0; depth = max(12.0, min(r * nrng.uniform(0.7, 1.1), 110.0))
        wob = nrng.normal(0, 1, 64).cumsum(); wob = (wob - wob.mean()) * 1.5
        for t in range(int(depth) + 1):
            half = r * np.sqrt(max(0.0, 1 - (t / depth) ** 2)) + wob[min(63, t // 2)]
            lo, hi = int(max(0, c - half)), int(min(len(line), c + half))
            p = edge_pos + outward * (t + 1)
            if horizontal:
                if 0 <= p < H8 * 8: DW[p, along0 + lo:along0 + hi] = True
            else:
                if 0 <= p < W8 * 8: DW[along0 + lo:along0 + hi, p] = True
for b in blocks:
    if not b.get('caps', True): continue
    X, Y, Wp, Hp = b['x'] * 32, b['y'] * 32, b['w'] * 32, b['h'] * 32
    def opn(y8, x8): return 0 <= y8 < H8 and 0 <= x8 < W8 and open8[y8, x8] and not fixed8[y8, x8]
    line = DW[Y, X:X + Wp].copy(); line &= np.repeat([opn(Y // 8 - 1, (X + i * 8) // 8) for i in range(Wp // 8)], 8); caps(line, Y, -1, X, True)
    line = DW[Y + Hp - 1, X:X + Wp].copy(); line &= np.repeat([opn((Y + Hp) // 8, (X + i * 8) // 8) for i in range(Wp // 8)], 8); caps(line, Y + Hp - 1, 1, X, True)
    line = DW[Y:Y + Hp, X].copy(); line &= np.repeat([opn((Y + i * 8) // 8, X // 8 - 1) for i in range(Hp // 8)], 8); caps(line, X, -1, Y, False)
    line = DW[Y:Y + Hp, X + Wp - 1].copy(); line &= np.repeat([opn((Y + i * 8) // 8, (X + Wp) // 8) for i in range(Hp // 8)], 8); caps(line, X + Wp - 1, 1, Y, False)
wrng = np.random.default_rng(11)
for b, side, a0, a1, depth in water_notch:
    assert side == 'n'
    a0p, a1p, dep = int((b['x'] * 4 + a0 * 4) * 8), int((b['x'] * 4 + a1 * 4) * 8), depth * 32
    top = b['y'] * 32
    # an uneven flood pool: flush with the tower's top corners, then spreading wider than deep, each side with its own
    # wobbling shore, the far shore an irregular curve
    wl = ndimage.gaussian_filter1d(wrng.normal(0, 1, dep + 1), 9); wl = wl / (np.abs(wl).max() + 1e-6) * 22
    wr = ndimage.gaussian_filter1d(wrng.normal(0, 1, dep + 1), 9); wr = wr / (np.abs(wr).max() + 1e-6) * 22
    spread_l, spread_r = 150.0, 90.0
    for k in range(dep):
        e = k / dep
        g = np.sin(min(1.0, max(0.0, (k - 6) / (dep * 0.35))) * np.pi / 2)
        f = np.sqrt(max(0.0, 1 - max(0.0, (e - 0.25) / 0.75) ** 2))      # closes over the last three quarters
        lo = a0p - (spread_l * g + (wl[k] if k > 10 else 0))
        hi = a1p + (spread_r * g + (wr[k] if k > 10 else 0))
        mid, hw = (lo + hi) / 2, (hi - lo) / 2 * f
        lo, hi = int(round(mid - hw)), int(round(mid + hw))
        if hi > lo: DW[top - 1 - k, lo:hi] = True
DW &= np.kron(open8 | fixed8, np.ones((8, 8), bool))

# ---- ground next to the blocks: 8 px tiles one by one ---------------------------------------------------------------
near = ndimage.binary_dilation(fixed8, iterations=8) & open8      # 2 cells
tb = np.zeros((H, W), bool)
tb[:, 1:] |= tone_at[:, 1:] != tone_at[:, :-1]; tb[:, :-1] |= tone_at[:, 1:] != tone_at[:, :-1]
tb[1:, :] |= tone_at[1:, :] != tone_at[:-1, :]; tb[:-1, :] |= tone_at[1:, :] != tone_at[:-1, :]
band8 = ndimage.binary_dilation(np.kron(tb, np.ones((4, 4), bool)), iterations=3) & open8 & ~near
near |= ndimage.binary_dilation(np.kron(ndimage.binary_dilation(land, iterations=1) & ~land, np.ones((4, 4), bool)), iterations=1) & False
tone8 = np.kron(tone_at, np.ones((4, 4), int))
for ti, tn in enumerate(tone_names):
    t = tones[tn]
    for k in t['keys']: col_of.setdefault(k, col_votes[k].most_common(1)[0][0] if col_votes[k] else 0)
    spots = [(int(y), int(x)) for y, x in zip(*np.where(near & (tone8 == ti)))]
    gravel8.synth(GA, GB, GC, spots, t['keys'], t['src'], col_of, VOID, seed=5 + ti)
    for y, x in spots: GC[y][x] = col_of[GA[y][x]]

# the band between tones: drawn with the 8 px tiles of both, after the pool cells (below) so both sides are there
# ---- a pool of ground cells per tone, then whole cells for the open land -------------------------------------------
POOL = CFG.get('pool', 40)
pools = []
for ti, tn in enumerate(tone_names):
    t = tones[tn]
    A_ = [[VOID] * (POOL * 4) for _ in range(POOL * 4)]; B_ = [[VOID] * (POOL * 4) for _ in range(POOL * 4)]; C_ = [[1] * (POOL * 4) for _ in range(POOL * 4)]
    gravel8.synth(A_, B_, C_, [(y, x) for y in range(POOL * 4) for x in range(POOL * 4)], t['keys'], t['src'], col_of, VOID, seed=50 + ti)
    cells_ = sorted({tuple(A_[cy_ * 4 + k // 4][cx_ * 4 + k % 4] for k in range(16)) for cy_ in range(POOL) for cx_ in range(POOL)})
    pools.append(cells_); print('pool', tn, len(cells_))
Hc, Vc = collections.Counter(), collections.Counter()
for t in tones.values():
    h_, v_ = gravel8.pair_counts(t['src']); Hc.update(h_); Vc.update(v_)
allk = sorted({k for p in pools for c in p for k in c} | {GA[y][x] for y, x in zip(*np.where(near))})
ki = {k: i for i, k in enumerate(allk)}; nk = len(allk)
def lp(counter):
    M = np.full((nk, nk), 0.0)
    for (a, b_), n in counter.items():
        if a in ki and b_ in ki: M[ki[a], ki[b_]] += n
    M = (M + 0.05) / (M.sum(1, keepdims=True) + 0.05 * nk)
    return -np.log(M)
LH, LV = lp(Hc), lp(Vc)
PL = [np.array([[ki[c[k]] for k in range(16)] for c in p]) for p in pools]
use = [np.zeros(len(p)) for p in pools]
cellopen = open8.reshape(H, 4, W, 4).all((1, 3)) & ~(near | band8).reshape(H, 4, W, 4).any((1, 3))
prng = np.random.default_rng(CFG.get('seed', 3) + 7)
chosen = {}
for y in range(H):
    for x in range(W):
        if not cellopen[y, x]: continue
        ti = tone_at[y, x]; P = PL[ti]; cost = np.zeros(len(P))
        if x > 0 and (cellopen[y, x - 1] or land8[y * 4, x * 4 - 1]):
            for r in range(4): cost += LH[ki.get(GA[y * 4 + r][x * 4 - 1], 0), P[:, r * 4]]
        if y > 0 and (cellopen[y - 1, x] or land8[y * 4 - 1, x * 4]):
            for c in range(4): cost += LV[ki.get(GA[y * 4 - 1][x * 4 + c], 0), P[:, c]]
        if x + 1 < W and not cellopen[y, x + 1] and land8[y * 4, x * 4 + 4]:
            for r in range(4): cost += LH[P[:, r * 4 + 3], ki.get(GA[y * 4 + r][x * 4 + 4], 0)]
        if y + 1 < H and not cellopen[y + 1, x] and land8[y * 4 + 4, x * 4]:
            for c in range(4): cost += LV[P[:, 12 + c], ki.get(GA[y * 4 + 4][x * 4 + c], 0)]
        cost += 0.8 * np.sqrt(use[ti]) + prng.random(len(P)) * 1.5
        for (dy, dx) in ((0, -1), (-1, 0), (-1, -1), (-1, 1), (0, -2), (-2, 0)):
            j = chosen.get((y + dy, x + dx))
            if j is not None and j[0] == ti: cost[j[1]] += 1e6
        j = int(cost.argmin()); use[ti][j] += 1; chosen[(y, x)] = (ti, j)
        c = pools[ti][j]
        for k in range(16):
            yy, xx = y * 4 + k // 4, x * 4 + k % 4
            GA[yy][xx] = c[k]; GB[yy][xx] = VOID; GC[yy][xx] = col_of[c[k]]
# open 8 px spots not covered by a whole cell (land outline): 8 px tiles
rest = [(int(y), int(x)) for y, x in zip(*np.where(open8 & ~near & ~band8)) if not cellopen[y // 4, x // 4]]
for ti, tn in enumerate(tone_names):
    sp = [p for p in rest if tone8[p] == ti]
    gravel8.synth(GA, GB, GC, sp, tones[tn]['keys'], tones[tn]['src'], col_of, VOID, seed=90 + ti)
    for y, x in sp: GC[y][x] = col_of[GA[y][x]]

if band8.any():
    # inside the band the tone line runs at 8 px along a finer wobble; each side is drawn with its own tiles
    n8 = ndimage.gaussian_filter(np.random.default_rng(21).normal(0, 1, (H8, W8)), 2.5); n8 /= n8.std()
    sm = ndimage.gaussian_filter(np.kron(tone_at, np.ones((4, 4))).astype(np.float32), 3.0)
    fine = np.clip(np.round(sm + 0.35 * n8), 0, len(tone_names) - 1).astype(int)
    sp_all = sorted((int(y), int(x)) for y, x in zip(*np.where(band8)))
    for y, x in sp_all: GA[y][x] = VOID
    for ti, tn in enumerate(tone_names):
        sp = [p for p in sp_all if fine[p] == ti]
        gravel8.synth(GA, GB, GC, sp, tones[tn]['keys'], tones[tn]['src'], col_of, VOID, seed=77 + ti)
        for y, x in sp: GC[y][x] = col_of[GA[y][x]]
# ---- shores where water runs off a block ---------------------------------------------------------------------------
skeys = [k for k in src_count if all(tuple(int(u) for u in v) in set().union(*[t['cols'] for t in tones.values()]) | SH for v, tr in [tpx(k)] for v in v[~tr])] if False else None
grav_col = set().union(*[t['cols'] for t in tones.values()])
SHORE_COL = collections.Counter()
for L in levels:
    for row in grids[L]:
        for c in row:
            im, tr = cell_img(c, pixels, rgb)
            if not tr.any() or tr.all(): continue
            nb = ndimage.binary_dilation(tr, iterations=2)
            for v in im[nb & ~tr]: SHORE_COL[tuple(int(u) for u in v)] += 1
OK_COL = grav_col | {k for k, n in SHORE_COL.items() if n >= 40}
def key_ok(k):
    im, tr = tpx(k)
    landpx = im[~tr]
    if any(int(v[1]) > int(v[0]) + 6 for v in landpx): return False
    return all(tuple(int(u) for u in v) in OK_COL for v in landpx)
skeys = [k for k in src_count if key_ok(k)]
for k in skeys: col_of.setdefault(k, col_votes[k].most_common(1)[0][0])
fixed_for_shore = ~open8
n8 = shore8.synth(GA, GB, GC, DW, fixed_for_shore, pixels, rgb, skeys, col_of, grav_col, lip=CFG.get('lip', 1.5), shape=CFG.get('shape', 20.0))
print('shore tiles', n8)

# ---- save + pictures ------------------------------------------------------------------------------------------------
GB = [[(t if t != VOID else (BLANK, 0)) for t in row] for row in GB]
info = dict(name=CFG['name'], W=int(W), H=int(H), origin_cell=[int(bx0), int(by0)], blocks=[dict(name=b['name'], x=int(b['x']), y=int(b['y']), w=int(b['w']), h=int(b['h'])) for b in blocks])
pickle.dump(dict(info, GA=GA, GB=GB, GC=GC, land=land), open(os.path.join(out, 'region.pkl'), 'wb'))
json.dump(info, open(os.path.join(out, 'region.json'), 'w'), indent=1)
build.BLANK = BLANK
rgb_v = rgb.copy(); rgb_v[::16] = (70, 104, 118)
img = build.render(GA, GB, pixels, rgb_v, 0, 0, W8, H8).clip(0, 255).astype(np.uint8)
Image.fromarray(img).save(os.path.join(out, 'region.png'))
print('done', W, H, 'metas A', len({tuple(GA[y * 4 + k // 4][x * 4 + k % 4] for k in range(16)) for y in range(H) for x in range(W)}))
