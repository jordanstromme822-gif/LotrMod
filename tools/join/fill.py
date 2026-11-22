"""Join Flooded Field (51) and Tower Base (55) into one map at Jordan's 3D World layout (Tower Base 58 cells right
of Flooded Field's left edge, 69 cells of new ground between them; 2026-11-22 JOIN group [51, 55]), the ground
between them filled with the levels' own cells (plain gravel away from the maps; near each map's edge, cells that
were seen next to that edge's cells in the game's own maps, so water and shores close the way the game draws them).

python3 tools/join/fill.py ROM OUT_DIR
"""
import sys, os, pickle, collections, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cells import load, cell_img, BLANK, pix
from PIL import Image

rom, out = sys.argv[1], sys.argv[2]
GAP = 69   # 2244 px in Jordan's layout, rounded to whole 32 px cells
TOP, BOT = 55, 51
NTOP = 12
R, lv, rgb, grids, pixels = load(rom, [BOT, TOP])
gt, gb = grids[TOP], grids[BOT]
TX = 58                                    # Tower Base 1848 px right of Flooded Field's left edge (58 cells = 1856 px)
W = max(len(gb[0]), TX + len(gt[0]))
H = len(gt) + GAP + len(gb)
FY = len(gt) + GAP
world = [[None] * W for _ in range(H)]; fixed = np.zeros((H, W), bool)
for y, row in enumerate(gt):
    for x, c in enumerate(row): world[y][TX + x] = c; fixed[y, TX + x] = True
for y, row in enumerate(gb):
    for x, c in enumerate(row): world[FY + y][x] = c; fixed[FY + y, x] = True
# the path: from Flooded Field's north door (columns 17-18) up, across, and up to Tower Base's south path (its columns 10-11)
FROAD, TROAD = 17, TX + 10
MIDY = (len(gt) + FY) // 2
ROADC = set()
def road_seg(x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / max(n, 1)); y = round(y0 + (y1 - y0) * i / max(n, 1))
        for dx in (0, 1):
            for dy in (0, 1): ROADC.add((y + dy, x + dx))
pts = [(FROAD, FY - 1), (FROAD, MIDY + 8), (FROAD + 6, MIDY + 2), (TROAD - 6, MIDY - 2), (TROAD, MIDY - 8), (TROAD, len(gt))]
for a, b in zip(pts, pts[1:]): road_seg(*a, *b)
ROADC = {(y, x) for y, x in ROADC if 0 <= y < H and 0 <= x < W}

def unfix_cut(y_edge, rows, x0, ncols):
    # 8 px top-layer tiles touching the edge row, grown through touching non-empty top-layer tiles: whole cut objects
    seen = set(); st = []
    for cx in range(ncols):
        c = world[y_edge][x0 + cx]
        for k, t in enumerate(c[1]):
            ky = k // 4
            if t[0] != BLANK and ((y_edge == rows[0] and ky == 0) or (y_edge == rows[-1] and ky == 3)):
                st.append((y_edge * 4 + ky, (x0 + cx) * 4 + k % 4))
    while st:
        p = st.pop()
        if p in seen: continue
        y8, x8 = p; cy, cx = y8 // 4, x8 // 4
        if not (rows[0] <= cy <= rows[-1]) or not fixed[cy, cx]: continue
        t = world[cy][cx][1][(y8 % 4) * 4 + x8 % 4]
        if t[0] == BLANK: continue
        seen.add(p)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1): st.append((y8 + dy, x8 + dx))
    cells = {(y8 // 4, x8 // 4) for y8, x8 in seen}
    for cy, cx in cells: fixed[cy, cx] = False; world[cy][cx] = None
    return cells
cut = unfix_cut(len(gt) - 1, list(range(len(gt))), TX, len(gt[0])) | unfix_cut(FY, list(range(FY, FY + len(gb))), 0, len(gb[0]))
print('cut object cells refilled', sorted(cut))
def open_edge(c, side):
    i, t = cell_img(c, pixels, rgb)
    return {'n': t[0], 's': t[31], 'w': t[:, 0], 'e': t[:, 31]}[side].any()
wet = set()
for x in range(len(gt[0])):                        # Tower Base bottom row
    if open_edge(world[len(gt) - 1][TX + x] or gt[-1][x], 's'): wet |= {(len(gt) - 1, TX + x), (len(gt) - 2, TX + x)}
for y in range(len(gt)):                           # Tower Base left and right edges
    if open_edge(gt[y][0], 'w'): wet |= {(y, TX), (y, TX + 1)}
    if open_edge(gt[y][-1], 'e'): wet |= {(y, TX + len(gt[0]) - 1), (y, TX + len(gt[0]) - 2)}
for x in range(len(gb[0])):                        # Flooded Field top row
    if open_edge(gb[0][x], 'n'): wet |= {(FY, x), (FY + 1, x)}
pass  # open water on the edges is closed later by cap.py with real shorelines
print('open-water edge cells refilled', len(wet))
# candidate cells: every cell of both maps with an empty top layer (objects never get cut)
cnt = collections.Counter(c for g in (gt, gb) for row in g for c in row)
cands = [c for c in cnt if all(t[0] == BLANK for t in c[1])]
def _odd(c):
    im = cell_img(c, pixels, rgb)[0]
    return ((im[..., 0] > 200) & (im[..., 1] > 200) & (im[..., 2] < 90)).any() or ((im[..., 0] > 200) & (im[..., 2] > 200) & (im[..., 1] < 120)).any()
cands = [c for c in cands if not _odd(c)]
idx = {c: i for i, c in enumerate(cands)}
IM = np.stack([cell_img(c, pixels, rgb)[0] for c in cands]).astype(np.float32)
TR = np.stack([cell_img(c, pixels, rgb)[1] for c in cands])
IM[TR] = -200.0                              # see-through (water) pixels only match see-through pixels
def is_pure(c, img, tr):
    if tr.any() or any((v & 7) in (1, 2) for v in c[2]): return False
    r, g, b = img[..., 0], img[..., 1], img[..., 2]; lum = img.mean(-1)
    if (b > r + 12).mean() > 0.01: return False
    return (g > r + 10).mean() < 0.01 and ((r > 140) & (g > 130) & (b < 120)).mean() < 0.01 and (lum < 40).mean() < 0.06
PURE0 = np.array([is_pure(c, IM[i], TR[i]) for i, c in enumerate(cands)])
top_plain = sorted([c for i, c in enumerate(cands) if PURE0[i]], key=lambda c: -cnt[c])[:NTOP]
GT = {t[0] for c in top_plain for t in c[0]}
PURE = np.array([PURE0[i] and all(t[0] in GT for t in c[0]) for i, c in enumerate(cands)])
ROADY = np.array([((IM[i][..., 0] > 140) & (IM[i][..., 1] > 130) & (IM[i][..., 2] < 130)).mean() for i in range(len(cands))])
ROAD = (ROADY > 0.04) & ~TR.reshape(len(cands), -1).any(1) & np.array([not any((v & 7) in (1, 2) for v in c[2]) for c in cands])
print('road cells', ROAD.sum())
print('candidates', len(cands), 'pure gravel', PURE.sum())
# observed neighbours (in the game's own maps)
above, below, left, right = (collections.defaultdict(set) for _ in range(4))
for g in (gt, gb):
    for y in range(len(g)):
        for x in range(len(g[0])):
            c = g[y][x]
            if y + 1 < len(g): below[c].add(g[y + 1][x]); above[g[y + 1][x]].add(c)
            if x + 1 < len(g[0]): right[c].add(g[y][x + 1]); left[g[y][x + 1]].add(c)
top_e, bot_e, lef_e, rig_e = IM[:, 0], IM[:, 31], IM[:, :, 0], IM[:, :, 31]
TRN, TRS, TRW, TRE = TR[:, 0].any(1), TR[:, 31].any(1), TR[:, :, 0].any(1), TR[:, :, 31].any(1)
def edge_img(c):
    i, t = cell_img(c, pixels, rgb); i = i.astype(np.float32).copy(); i[t] = -200.0; return i
# distance from the maps (cells)
dist = np.full((H, W), 999)
from collections import deque
q = deque()
for y in range(H):
    for x in range(W):
        if fixed[y, x]: dist[y, x] = 0; q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yy, xx = y + dy, x + dx
        if 0 <= yy < H and 0 <= xx < W and dist[yy, xx] > dist[y, x] + 1: dist[yy, xx] = dist[y, x] + 1; q.append((yy, xx))
# the path runs only a few cells out of each map and fades into the open ground (a long staircase of path cells across
# the new ground looked blocky; a proper road between the two maps is detail work for later)
ROADC = {p for p in ROADC if dist[p] <= 3}
rng = np.random.default_rng(11); used = collections.Counter()
todo = {(y, x) for y in range(H) for x in range(W) if not fixed[y, x]}
def nbrs(y, x):
    for dy, dx, k in ((-1, 0, 'n'), (1, 0, 's'), (0, -1, 'w'), (0, 1, 'e')):
        yy, xx = y + dy, x + dx
        if 0 <= yy < H and 0 <= xx < W and world[yy][xx] is not None: yield k, world[yy][xx]
DW = np.zeros((H * 32, W * 32), bool)
for g, ox, oy in ((gt, TX, 0), (gb, 0, FY)):
    for y, row in enumerate(g):
        for x, c in enumerate(row): DW[(oy + y) * 32:(oy + y) * 32 + 32, (ox + x) * 32:(ox + x) * 32 + 32] = cell_img(c, pixels, rgb)[1]
nrng = np.random.default_rng(5)
def caps(line, edge_pos, outward, along0, horizontal):
    # line: bool water along the map edge (pixels); draw caps outward from edge_pos
    runs, i = [], 0
    while i < len(line):
        if line[i]:
            j = i
            while j < len(line) and line[j]: j += 1
            runs.append((i, j)); i = j
        else: i += 1
    for a, b in runs:
        r = (b - a) / 2.0; c = (a + b) / 2.0; depth = max(12.0, min(r * nrng.uniform(0.7, 1.1), 110.0))
        wob = nrng.normal(0, 1, 64).cumsum(); wob = (wob - wob.mean()) * 1.5
        for t in range(int(depth) + 1):
            half = r * np.sqrt(max(0.0, 1 - (t / depth) ** 2)) + wob[min(63, t // 2)]
            lo, hi = int(max(0, c - half)), int(min(len(line), c + half))
            p = edge_pos + outward * (t + 1)
            if horizontal:
                if 0 <= p < H * 32: DW[p, along0 + lo:along0 + hi] = True
            else:
                if 0 <= p < W * 32: DW[along0 + lo:along0 + hi, p] = True
tb_y1 = len(gt) * 32
caps(DW[tb_y1 - 1, TX * 32:(TX + len(gt[0])) * 32], tb_y1 - 1, 1, TX * 32, True)                    # Tower Base south
caps(DW[0:tb_y1, TX * 32], TX * 32, -1, 0, False)                                                  # west
caps(DW[0:tb_y1, (TX + len(gt[0])) * 32 - 1], (TX + len(gt[0])) * 32 - 1, 1, 0, False)             # east
caps(DW[FY * 32, :], FY * 32, -1, 0, True)                                                          # Flooded Field north
FFW = len(gb[0])
caps(DW[FY * 32:H * 32, FFW * 32 - 1], FFW * 32 - 1, 1, FY * 32, False)                             # Flooded Field east
for (ry, rx) in ROADC:
    if not fixed[ry, rx]: DW[ry * 32:ry * 32 + 32, rx * 32:rx * 32 + 32] = False                   # the path stays dry
TRF = TR.reshape(len(cands), -1)
# ---- water that runs off a map edge goes on and ends in a real shore (lake.py) ----
import lake
lk_cands = [c for c in cnt if all(t[0] == BLANK for t in c[1]) and not _odd(c)]
# colours a lake cell's dry part may use: the plain gravel's, plus the shore outline's (pixels next to water in the maps)
GRAV_COL = set()
for c in top_plain:
    im, tr = cell_img(c, pixels, rgb); GRAV_COL |= {tuple(v) for v in im.reshape(-1, 3)}
SHORE_COL = collections.Counter()
for g in (gt, gb):
    for row in g:
        for c in row:
            im, tr = cell_img(c, pixels, rgb)
            if not tr.any() or tr.all(): continue
            near = np.zeros_like(tr)
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2): near |= np.roll(np.roll(tr, dy, 0), dx, 1)
            for v in im[near & ~tr]: SHORE_COL[tuple(v)] += 1
OK_COL = GRAV_COL | {k for k, n in SHORE_COL.items() if n >= 40}
print('lake colours', len(GRAV_COL), len(OK_COL))
def land_fine(c):
    im, tr = cell_img(c, pixels, rgb)
    land = ~tr
    if any((v & 7) in (1, 2) for v, t in zip(c[2], tr.reshape(4, 8, 4, 8).swapaxes(1, 2).reshape(16, 64).all(1)) if not t): return False
    cols = im[land]
    return all(tuple(v) in OK_COL for v in cols)
lk_ok = np.array([land_fine(c) for c in lk_cands])
print('lake candidates', len(lk_cands), 'usable', lk_ok.sum())
fixed_l = [[bool(fixed[y, x]) for x in range(W)] for y in range(H)]
placed = {}   # lake.py (32 px shore cells) looked blocky; shore8.py draws the shore with 8 px tiles below
for (y, x), c in placed.items(): world[y][x] = c; fixed[y, x] = True; todo.discard((y, x))
order = sorted(todo, key=lambda p: (dist[p], p[0], p[1]))
for (y, x) in order:
    cost = np.zeros(len(cands)); allowed = None
    for k, c in nbrs(y, x):
        e = edge_img(c)
        if k == 'n': cost += ((top_e - e[31][None]) ** 2).mean((1, 2)); ok = below.get(c)
        elif k == 's': cost += ((bot_e - e[0][None]) ** 2).mean((1, 2)); ok = above.get(c)
        elif k == 'w': cost += ((lef_e - e[:, 31][None]) ** 2).mean((1, 2)); ok = right.get(c)
        else: cost += ((rig_e - e[:, 0][None]) ** 2).mean((1, 2)); ok = left.get(c)
        if ok and dist[y, x] <= 3:
            bonus = np.zeros(len(cands)); bonus[[idx[o] for o in ok if o in idx]] = 1
            cost -= 300 * bonus                         # seen next to this cell in the game's own maps
        cost += np.where(np.arange(len(cands)) == idx.get(c, -1), 400, 0)   # never the same cell twice side by side
    d = dist[y, x]
    want = np.zeros(1024, bool)
    cost += np.where(TRF.any(1), 1e6, 0)                  # no water in the new ground
    # water and shores never run away from the maps: an edge facing ground further out must be solid
    for dy, dx, flag in ((-1, 0, TRN), (1, 0, TRS), (0, -1, TRW), (0, 1, TRE)):
        yy, xx = y + dy, x + dx
        if 0 <= yy < H and 0 <= xx < W and world[yy][xx] is None and dist[yy, xx] > d and d >= 5: cost += np.where(flag, 1e6, 0)
    inroad = (y, x) in ROADC and not fixed[y, x]
    if inroad: cost += np.where(ROAD, 0, 1e5)            # the path, all the way between the two maps
    else: cost += np.where(PURE, 0, 1e5)                 # only plain gravel in the new ground (water: cap.py)                 # plain gravel away from the maps
    cost += 40.0 * np.array([used[c] for c in cands]) ** 0.5  # spread the gravel variants
    cost += rng.random(len(cands)) * 25
    j = int(cost.argmin()); world[y][x] = cands[j]; used[cands[j]] += 1
# ---- 8 px grids, then the water edges re-solved tile by tile ----
GA = [[None] * (W * 4) for _ in range(H * 4)]; GB = [[None] * (W * 4) for _ in range(H * 4)]; GC = [[1] * (W * 4) for _ in range(H * 4)]
for y in range(H):
    for x in range(W):
        c = world[y][x]
        for k in range(16):
            GA[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]; GB[y * 4 + k // 4][x * 4 + k % 4] = c[1][k]; GC[y * 4 + k // 4][x * 4 + k % 4] = c[2][k]
import shore8
fixed8 = np.kron(fixed, np.ones((4, 4), bool))
src_keys = collections.Counter(); col_votes = collections.defaultdict(collections.Counter)
for g in (gt, gb):
    for row in g:
        for c in row:
            for k in range(16): src_keys[c[0][k]] += 1; col_votes[c[0][k]][c[2][k]] += 1
def key_ok(k):
    im, tr = shore8.tile_px(k, pixels, rgb)
    land = im[~tr]
    if any(int(v[1]) > int(v[0]) + 6 for v in land): return False          # no moss or weed pieces in the shore
    return all(tuple(int(u) for u in v) in OK_COL for v in land)
skeys = [k for k in src_keys if key_ok(k)]
col_of = {k: col_votes[k].most_common(1)[0][0] for k in skeys}
GT_ALL = {t for c in top_plain for t in c[0]} | {t for i, c in enumerate(cands) if PURE[i] for t in c[0]}
import gravel8
srcA8 = []
for g in (gt, gb):
    A_ = [[None] * (len(g[0]) * 4) for _ in range(len(g) * 4)]
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            for k in range(16): A_[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]
    srcA8.append(A_)
def gravel_key(k):
    im, tr = shore8.tile_px(k, pixels, rgb)
    if tr.any() or not all(tuple(int(u) for u in v) in GRAV_COL for v in im.reshape(-1, 3)): return False
    return (im.astype(np.float32) @ np.array([.3, .59, .11]) < 70).sum() <= 10   # no lone dark scorch squares
gkeys = [k for k in src_keys if k in GT_ALL and gravel_key(k)]   # tiles of the plain gravel cells only (wall stones share its colours)
print('gravel tiles', len(gkeys))
for k in gkeys: col_of.setdefault(k, col_votes[k].most_common(1)[0][0])
roadset = set(ROADC); gset = set(gkeys) | GT_ALL
gspots = [(y, x) for y in range(H * 4) for x in range(W * 4)
          if not fixed8[y, x] and (y // 4, x // 4) not in roadset and GA[y][x] in gset]
# things drawn on the ground layer (rocks, cliffs, moss) that the old map edge cut straight through: take the 8 px tiles
# connected to the edge, up to 2 cells in, back to plain ground so nothing ends in a straight cut
GSET = set(gkeys)
def is_obj(y8, x8):
    if GB[y8][x8] is not None and GB[y8][x8][0] != BLANK: return True
    im, tr = shore8.tile_px(GA[y8][x8], pixels, rgb)
    if tr.any(): return False                     # shore pieces stay (shore8 redraws the shore)
    return GA[y8][x8] not in GSET
def a_obj(y8, x8):                                # the ground layer itself shows something (not a loose top piece)
    im, tr = shore8.tile_px(GA[y8][x8], pixels, rgb)
    return not tr.any() and any(tuple(int(u) for u in v) not in GRAV_COL for v in im.reshape(-1, 3))
def flood(cells8, inside):
    st = [p for p in cells8 if 0 <= p[0] < H * 4 and 0 <= p[1] < W * 4 and is_obj(*p)]; seen = set()
    while st:
        p = st.pop()
        if p in seen or not (0 <= p[0] < H * 4 and 0 <= p[1] < W * 4) or not inside(p) or not fixed8[p] or not is_obj(*p): continue
        seen.add(p)
        st += [(p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)]
    return seen
def edge_objs(edge, d, lo, hi):
    """edge: 'w'/'s'/'n'/'e' map side facing new ground at 8 px line d (the map's own outermost tile line), along lo..hi.
    Clears objects within 2 cells of that side, but not the parts of bigger things standing further in (each line
    of them is kept from 2 cells in back to 1 cell in)."""
    if edge == 'w': rel = lambda p: p[1] - d; along = lambda p: lo <= p[0] < hi
    elif edge == 'e': rel = lambda p: d - p[1]; along = lambda p: lo <= p[0] < hi
    elif edge == 'n': rel = lambda p: p[0] - d; along = lambda p: lo <= p[1] < hi
    else: rel = lambda p: d - p[0]; along = lambda p: lo <= p[1] < hi
    def at(r, a): return {'w': (a, d + r), 'e': (a, d - r), 'n': (d + r, a), 's': (d - r, a)}[edge]
    out = set(); done = set()
    for a0 in range(lo, hi):
        if at(0, a0) in done: continue
        comp = flood([at(0, a0)], lambda p: along(p) and 0 <= rel(p) < 48)
        done |= comp
        if not comp: continue
        if max(rel(p) for p in comp) < 47 and len(comp) <= 240:
            out |= comp                           # a small thing the edge cut: take all of it away
            continue
        cut = {p for p in comp if rel(p) < 8}     # part of something big: clear 2 cells, keep what stands just inside
        keep = set()
        for a in range(lo, hi):
            r = 8
            while r >= 4 and at(r, a) in comp and (r >= 6 or a_obj(*at(r, a))):   # loose top pieces only right next to it
                keep.add(at(r, a)); r -= 1
        out |= cut - keep
    # whatever the cut left standing that is only a small piece on its own goes too (no half ruins)
    rest = set()
    for p in list(out):
        for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if q in out or q in rest or not (0 <= q[0] < H * 4 and 0 <= q[1] < W * 4) or not fixed8[q] or not is_obj(*q): continue
            seen = set(); st = [q]
            while st and len(seen) <= 120:
                r_ = st.pop()
                if r_ in seen or r_ in out or not (0 <= r_[0] < H * 4 and 0 <= r_[1] < W * 4) or not fixed8[r_] or not is_obj(*r_): continue
                seen.add(r_); st += [(r_[0] + 1, r_[1]), (r_[0] - 1, r_[1]), (r_[0], r_[1] + 1), (r_[0], r_[1] - 1)]
            if len(seen) <= 120: rest |= seen
    # ground-layer pieces left touching the cut that belong to no big ground-layer shape (a ruin sliver next to a tower
    # drawn on the top layer): looked at on the ground layer alone
    done_ = out | rest
    def bare(q): return (0 <= q[0] < H * 4 and 0 <= q[1] < W * 4) and fixed8[q] and q not in done_ and a_obj(*q) and (GB[q[0]][q[1]] is None or GB[q[0]][q[1]][0] == BLANK)
    for p in list(done_):
        for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if q in rest or not bare(q): continue
            seen = set(); st = [q]
            while st and len(seen) <= 40:
                r_ = st.pop()
                if r_ in seen or not bare(r_): continue
                seen.add(r_); st += [(r_[0] + 1, r_[1]), (r_[0] - 1, r_[1]), (r_[0], r_[1] + 1), (r_[0], r_[1] - 1)]
            if len(seen) <= 40: rest |= seen
    # and the same for loose top-layer pieces (a stump sitting on plain ground) cut by the edge
    done_ = out | rest
    def loose(q): return (0 <= q[0] < H * 4 and 0 <= q[1] < W * 4) and fixed8[q] and q not in done_ and GB[q[0]][q[1]] is not None and GB[q[0]][q[1]][0] != BLANK and not a_obj(*q)
    for p in list(done_):
        for q in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
            if q in rest or not loose(q): continue
            seen = set(); st = [q]
            while st and len(seen) <= 40:
                r_ = st.pop()
                if r_ in seen or not loose(r_): continue
                seen.add(r_); st += [(r_[0] + 1, r_[1]), (r_[0] - 1, r_[1]), (r_[0], r_[1] + 1), (r_[0], r_[1] - 1)]
            if len(seen) <= 40: rest |= seen
    return out | rest
tbh8, tx8, ffy8 = len(gt) * 4, TX * 4, FY * 4
ffw8, tbw8 = len(gb[0]) * 4, len(gt[0]) * 4
cutobj = edge_objs('w', tx8, 0, tbh8) | edge_objs('s', tbh8 - 1, tx8, tx8 + tbw8) | edge_objs('n', ffy8, 0, ffw8) | edge_objs('e', ffw8 - 1, ffy8, H * 4)
# a wall the east edge cut gets a real end: the columns where the same wall ends at a gap inside the map are copied in
# just before the cut (same rows, so the stones line up)
def end_caps(cutobj, W_=3):
    rows = {}
    for (y, x) in cutobj:
        if y >= ffy8 and x >= ffw8 - 8: rows[y] = min(rows.get(y, 99999), x)
    band = sorted(y for y, xs in rows.items() if xs > 3 and any(is_obj(y, xs - i) and fixed8[y, xs - i] for i in (1, 2, 3)))
    groups = []
    for y in band:
        if groups and y == groups[-1][-1] + 1: groups[-1].append(y)
        else: groups.append([y])
    def end_near(y, x):                           # the row's wall end close to column x (object, then 2 plain tiles)
        for e in range(x + W_, x - W_ - 1, -1):
            if is_obj(y, e) and not is_obj(y, e + 1) and not is_obj(y, e + 2): return e
        return None
    for g in groups:
        if len(g) < 6: continue
        xs_b = min(rows[y] for y in g)
        cands_ = [(sum(end_near(y, x) is not None for y in g), x) for x in range(8, xs_b - 24)]
        best, xc = max(cands_)
        if best < 6: print('no wall end found for rows', g[0], g[-1]); continue
        xR = xc + W_                               # a whole block of the map around that end (wall end and ground beyond)
        shift = ((xs_b - 1) - xR) // 4 * 4         # whole 32 px steps so the stones line up with the wall it joins
        xL = xR - 11
        for y in g:
            last = xL + shift - 1
            for sx in range(xL, xR + 1):           # this row's own part of the wall, up to where it ends
                if not is_obj(y, sx) or sx > xc + 1: break
                dx = sx + shift
                GA[y][dx], GB[y][dx], GC[y][dx] = GA[y][sx], GB[y][sx], GC[y][sx]
                cutobj.discard((y, dx)); fixed8[y, dx] = True; last = dx
            for x in range(last + 1, ffw8): cutobj.add((y, x))
        print('wall end for rows', g[0], g[-1], 'from column', xc, 'rows with an end', best, 'of', len(g))
end_caps(cutobj)
print('cut edge pieces cleared', len(cutobj))
for p in cutobj: fixed8[p] = False
gspots = sorted(set(gspots) | cutobj)
gravel8.synth(GA, GB, GC, gspots, gkeys, srcA8, col_of, (0, 0))
n8 = shore8.synth(GA, GB, GC, DW, fixed8, pixels, rgb, skeys, col_of, GRAV_COL)
print('shore tiles drawn', n8)
import shore
srcA = []
for g in (gt, gb):
    A_ = [[None] * (len(g[0]) * 4) for _ in range(len(g) * 4)]; C_ = [[0] * (len(g[0]) * 4) for _ in range(len(g) * 4)]
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            for k in range(16): A_[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]; C_[y * 4 + k // 4][x * 4 + k % 4] = c[2][k]
    srcA.append((A_, C_))
adj = shore.adjacency(srcA, pixels, rgb)
import cap
R2, lv2, rgb2, grids2, pixels2 = load(rom, [50])
pixels.update(pixels2)
srcs = [(A_, C_) for A_, C_ in srcA]
g50 = grids2[50]; A_ = [[None] * (len(g50[0]) * 4) for _ in range(len(g50) * 4)]; C_ = [[0] * (len(g50[0]) * 4) for _ in range(len(g50) * 4)]
for y, row in enumerate(g50):
    for x, c in enumerate(row):
        for k in range(16): A_[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]; C_[y * 4 + k // 4][x * 4 + k % 4] = c[2][k]
srcs.append((A_, C_))
log = []
GRAVEL_T = {t for c in top_plain for t in c[0]} | {t for i, c in enumerate(cands) if PURE[i] for t in c[0]}
def plain_tile(k):
    p = pix(pixels[k[0]]); c = rgb[(k[1] >> 12) * 16 + p]
    return 'shore' if (((c[..., 1] > 180) & (c[..., 2] > 180) & (c[..., 0] < 120)) & (p != 0)).any() else k in GRAVEL_T
for l in log: print(*l)
os.makedirs(out, exist_ok=True)
pickle.dump(dict(world=world, W=W, H=H, TX=TX, FY=FY, GAP=GAP, GA=GA, GB=GB, GC=GC), open(out + '/world.pkl', 'wb'))
import build; build.BLANK = BLANK
rgb_v = rgb.copy(); rgb_v[::16] = 0               # see-through pixels (the water layer below) drawn black
img = build.render(GA, GB, pixels, rgb_v, 0, 0, W * 4, H * 4)
Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(out + '/joined.png')
print('done', W, H)
