"""Mountains around a region (Isengard's valley walls), grown from the game's own mountain ridges.

python3 tools/region/mountains.py ROM REGION_DIR CONFIG.json OUT_DIR

The game's mountain levels (6, 8, 9, 10, 12, 13: one tileset) build their ridges from dense rock spires (palette 3) on
cobbles (palette 4). This tool grows new ridges along the region's outline from those tiles, one 8 px spot at a time in
reading order: each spot takes a tile whose neighbours in the source (left, above, and a few more) match what is
already placed, and whose distance to open ground below / right / left / above in the source is close to the spot's distance
to the region's land. So the ridges' feet land on the valley floor, their ends turn where the land turns, and no piece
is a stamped copy (every spot is chosen anew). Thin ground lines every 'terrace' spots inside the band make the rock
read as ridges stacked up the mountain side; farther ridges are a little darker.

The ridges are another tileset, so they are drawn by the page over the game's picture (tools/region/mountain-layer.js),
behind the heroes: every mountain spot in the map gets one 'key' tile (all pixels palette 8 colour 1, a colour no
region tile uses) and is blocked, and the page draws the mountain only where the picture shows the key colour. Sprites
cover the key, so heroes, enemies and effects stay in front of the rock.

Roads keep a pass: where a road meets the land's edge, plain ground runs on straight through the mountains (blocked
for now, past the old edge).

CONFIG: levels, rock_pal, ground_pal (source), band_out (spots past the land edge), border (spots along the map's border that are always mountains), band_in (spots of land edge
covered, hides the old edge lip), terrace [period, first] (spots), shade [start, length, max] (spots, darkening),
road_gap (spots kept clear around roads), block_gap, open [[x0, y0, x1, y1] px rects with no mountains], recolour
{palette index: [r, g, b]} for the source rock palette, seed, key [palette row, index].

OUT_DIR: region.pkl (the map with key tiles), region.png (preview with the mountains drawn), mountains.bin (zlib:
'MTN1', W8, H8, then rock u16[H8*W8], ground u16[H8*W8], shade u8[H8*W8]), mountains.json (rock atlas size, ground
tiles' palette rows, key colour), mountains-rock.png (RGBA, 8x8 rock tiles in rows of 64, tile 0 = none),
mountains-ground.png (palette index 0-15 per pixel, same layout).
"""
import json, os, pickle, random, struct, sys, zlib, collections
import numpy as np
from scipy import ndimage
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'join')); sys.path.insert(0, os.path.join(HERE, '..', 'siege'))
from cells import load
from build import pix

rom, rdir, cfg_path, out = sys.argv[1:5]
CFG = json.load(open(cfg_path))
os.makedirs(out, exist_ok=True)
R = pickle.load(open(os.path.join(rdir, 'region.pkl'), 'rb'))
GA, GB, GC = R['GA'], R['GB'], R['GC']
H8, W8 = len(GA), len(GA[0])
rnd = random.Random(CFG.get('seed', 5))

# ---- source: the mountain levels' ridges ---------------------------------------------------------------------------
LS = CFG.get('levels', [6, 8, 9, 10, 12, 13]); RP, GP = CFG.get('rock_pal', 3), CFG.get('ground_pal', 4)
_, _, srgb, sgrids, spixels = load(rom, LS)
def g8(L, k):
    g = sgrids[L]; return [[g[y // 4][x // 4][k][(y % 4) * 4 + x % 4] for x in range(len(g[0]) * 4)] for y in range(len(g) * 4)]
GID = ('G', 0)
def sym(a, b):
    pa, pb = a[1] >> 12, b[1] >> 12
    if not (a[0] and pa in (RP, GP)): return None              # stairs, statues, webs, void: not used
    if b[0] and pb not in (RP, GP): return None
    return (a if pa == RP else 'G', b if (b[0] and pb == RP) else 0)
ids = {GID: 0}; syms = [GID]
def sid(s):
    if s is None: return -1
    if s not in ids: ids[s] = len(syms); syms.append(s)
    return ids[s]
S = [np.array([[sid(sym(a, b)) for a, b in zip(ra, rb)] for ra, rb in zip(g8(L, 0), g8(L, 1))]) for L in LS]
groundA = np.array([s[0] == 'G' for s in syms])
CAP = 16
def dists(g, ground):
    """spots to the nearest ground below, right, left and above (capped), per spot"""
    h, w = g.shape; dd = np.full((h, w), CAP); dr = np.full((h, w), CAP); dl = np.full((h, w), CAP); du = np.full((h, w), CAP)
    for x in range(w):
        run = CAP
        for y in range(h - 1, -1, -1): run = 0 if ground[y, x] else min(CAP, run + 1); dd[y, x] = run
        run = CAP
        for y in range(h): run = 0 if ground[y, x] else min(CAP, run + 1); du[y, x] = run
    for y in range(h):
        run = CAP
        for x in range(w - 1, -1, -1): run = 0 if ground[y, x] else min(CAP, run + 1); dr[y, x] = run
        run = CAP
        for x in range(w): run = 0 if ground[y, x] else min(CAP, run + 1); dl[y, x] = run
    return dd, dr, dl, du
SD = [dists(g, g == 0) for g in S]
idx = collections.defaultdict(list); allpos = []
for gi, g in enumerate(S):
    h, w = g.shape
    for y in range(1, h):
        for x in range(1, w - 1):
            if g[y, x] < 0 or g[y - 1, x] < 0 or g[y, x - 1] < 0: continue
            idx[(g[y - 1, x], g[y, x - 1])].append((gi, y, x)); allpos.append((gi, y, x))
idxU = collections.defaultdict(list); idxL = collections.defaultdict(list)
for (u, l), v in idx.items(): idxU[u] += v; idxL[l] += v
print('source symbols', len(syms), 'contexts', len(idx))

# ---- where: the band along the land's outline ---------------------------------------------------------------------
void = np.array([[a[0] == 0 for a in row] for row in GA])
land = ~void
excl = np.zeros_like(void)
road = R.get('road')
# passes: where a road meets the edge, a corridor of plain ground runs on through the mountains (straight on from the
# road's last stretch), road_gap spots either side; blocked past the old land edge until the road is built on
passes = np.zeros_like(void)
if road is not None:
    rg = CFG.get('road_gap', 5)
    excl |= ndimage.binary_dilation(road, iterations=rg)
    meet = ndimage.binary_dilation(void, iterations=2) & road
    lab, n = ndimage.label(ndimage.binary_dilation(meet, iterations=4))
    yy0, xx0 = np.mgrid[0:void.shape[0], 0:void.shape[1]]
    for i in range(1, n + 1):
        ey, ex = [v.mean() for v in np.nonzero((lab == i) & meet)]
        near = road & ((yy0 - ey) ** 2 + (xx0 - ex) ** 2 < 30 ** 2)
        ny, nx = [v.mean() for v in np.nonzero(near)]
        dy, dx = ey - ny, ex - nx; L = max(1e-6, (dy * dy + dx * dx) ** 0.5); dy, dx = dy / L, dx / L
        t = (yy0 - ey) * dy + (xx0 - ex) * dx; o = np.abs((yy0 - ey) * dx - (xx0 - ex) * dy)
        passes |= (t > -2) & (t < CFG.get('band_out', 64) + 4) & (o <= rg + 1)
        print('pass at px', int(ex * 8), int(ey * 8), 'heading', round(dx, 2), round(dy, 2))
    excl |= passes
for b in R['blocks']:
    m = CFG.get('block_gap', 2)
    excl[max(0, b['y'] * 4 - m):b['y'] * 4 + b['h'] * 4 + m, max(0, b['x'] * 4 - m):b['x'] * 4 + b['w'] * 4 + m] = True
for x0, y0, x1, y1 in CFG.get('open', []):
    excl[max(0, y0 // 8):max(0, y1 // 8), max(0, x0 // 8):max(0, x1 // 8)] = True
d_land = ndimage.distance_transform_edt(void)          # void spots: distance to land
d_void = ndimage.distance_transform_edt(land)          # land spots: distance to void
# where the land runs close to the map's border there is no room past its edge: the mountains take the land there
yb, xb = np.mgrid[0:H8, 0:W8]
d_border = np.minimum(np.minimum(yb, H8 - 1 - yb), np.minimum(xb, W8 - 1 - xb)).astype(np.float64)
nz = ndimage.gaussian_filter(np.random.default_rng(CFG.get('seed', 5)).standard_normal((H8, W8)), 10)
# the land's own edge wobbles too (long straight stretches of rock read as a ruler line): up to edge_wobble spots more
nz2 = ndimage.gaussian_filter(np.random.default_rng(CFG.get('seed', 5) + 1).standard_normal((H8, W8)), 6)
d_border += nz / nz.std() * CFG.get('border_wobble', 5)      # a wavy line, not a ruler's
M = ((void & (d_land <= CFG.get('band_out', 64))) | (land & (d_void <= CFG.get('band_in', 2) + np.clip(nz2 / nz2.std() * CFG.get('edge_wobble', 4), 0, None))) | (d_border < CFG.get('border', 40))) & ~excl
dM = ndimage.distance_transform_edt(M)                 # how deep into the mountains
per, first = CFG.get('terrace', [12, 7])
yy, xx = np.mgrid[0:H8, 0:W8]
wob = 2.0 * np.sin(xx / 6.1 + yy / 5.3) + 1.5 * np.sin(xx / 3.7 - yy / 4.1)
ter = M & (np.mod(dM + wob, per) < 1.0) & (dM > first)
target = np.where(M & ~ter, 1, 0)
print('mountain spots', int(M.sum()), 'terrace', int(ter.sum()))

# ---- grow -----------------------------------------------------------------------------------------------------------
TD = dists(target, target == 0)
rows = np.where(M.any(1))[0]; y0r, y1r = int(rows.min()), int(rows.max()) + 1
PAD = 6
grid = np.zeros((H8 + PAD + 3, W8 + 4), int)          # padded (G around)
def place(y, x, t):
    Y, X = y + PAD, x + 1
    u, l = grid[Y - 1, X], grid[Y, X - 1]
    cands = idx.get((u, l)) or idxU.get(u) or idxL.get(l) or []
    samp = (cands if len(cands) <= 60 else rnd.sample(cands, 60)) + rnd.sample(allpos, 8)
    tdd, tdr, tdl, tdu = TD[0][y, x], TD[1][y, x], TD[2][y, x], TD[3][y, x]
    best = -1e9; pick = []
    for gi, sy, sx in samp:
        g = S[gi]; s = g[sy, sx]
        hh, ww = g.shape; dd, dr, dl, du = SD[gi]; sc = 0.0
        if s == 0: sc -= 4
        sc -= 1.5 * min(6, abs(int(dd[sy, sx]) - int(tdd))) + 1.5 * min(6, abs(int(dr[sy, sx]) - int(tdr))) + min(6, abs(int(dl[sy, sx]) - int(tdl))) + min(6, abs(int(du[sy, sx]) - int(tdu)))
        for dy, dx in ((-1, -1), (-1, 1), (-2, 0), (0, -2), (-1, 2), (-2, -1), (-2, 1)):
            ys_, xs_ = sy + dy, sx + dx
            if 0 <= ys_ < hh and 0 <= xs_ < ww and g[ys_, xs_] == grid[Y + dy, X + dx]: sc += 1
        if sc > best: best = sc; pick = [s]
        elif sc == best: pick.append(s)
    grid[Y, X] = rnd.choice(pick) if pick else 0
for y in range(max(0, y0r - PAD), y1r):
    xs = np.where(target[y] > 0)[0]
    if not len(xs): continue
    for x in range(max(0, xs.min() - 2), min(W8, xs.max() + 1)):
        if target[y, x]: place(y, x, target[y, x])
        else: grid[y + PAD, x + 1] = 0
rock = grid[PAD:PAD + H8, 1:1 + W8] * M
print('rock spots', int((rock > 0).sum()))

# ---- ground under the mountains: whole cells copied from plain open land ---------------------------------------------
H, W = H8 // 4, W8 // 4
plain = []
for cy in range(H):
    for cx in range(W):
        ok = True
        for k in range(16):
            y, x = cy * 4 + k // 4, cx * 4 + k % 4
            if void[y, x] or excl[y, x] or M[y, x] or GB[y][x][0] or (GC[y][x] & 7) or (road is not None and road[y, x]): ok = False; break
        if ok: plain.append((cy, cx))
print('plain cells', len(plain))
under = {}
cellpick = {}
opn = np.zeros_like(void)
for x0, y0, x1, y1 in CFG.get('open', []): opn[max(0, y0 // 8):max(0, y1 // 8), max(0, x0 // 8):max(0, x1 // 8)] = True
if road is not None: passes |= void & ndimage.binary_dilation(road, iterations=CFG.get('road_gap', 5)) & ~opn
for y, x in zip(*np.nonzero(passes & void)):          # the passes' ground: real map tiles, blocked
    c = (y // 4, x // 4)
    if c not in cellpick: cellpick[c] = plain[rnd.randrange(len(plain))]
    sy, sx = cellpick[c]; GA[y][x] = GA[sy * 4 + y % 4][sx * 4 + x % 4]; GB[y][x] = (0, 0); GC[y][x] = 1
for y, x in zip(*np.nonzero(M)):
    if land[y, x]: under[(y, x)] = GA[y][x]; continue
    c = (y // 4, x // 4)
    if c not in cellpick: cellpick[c] = plain[rnd.randrange(len(plain))]
    sy, sx = cellpick[c]; under[(y, x)] = GA[sy * 4 + y % 4][sx * 4 + x % 4]

# ---- layer data ----------------------------------------------------------------------------------------------------
RC = {int(k): v for k, v in CFG.get('recolour', {}).items()}
rgb = srgb.copy()
for i, c in RC.items(): rgb[RP * 16 + i] = c
def stile(t):
    p = pix(spixels[t[0]])
    if t[1] & 0x400: p = p[:, ::-1]
    if t[1] & 0x800: p = p[::-1]
    return p, t[1] >> 12
rock_ids = {0: 0}; rock_tiles = [np.zeros((8, 8, 4), np.uint8)]
for s in np.unique(rock):
    if s == 0: continue
    a, b = syms[s]; t = np.zeros((8, 8, 4), np.uint8)
    for tt in (a, b):
        if tt in ('G', 0): continue
        p, pal = stile(tt); m = p != 0
        t[m, :3] = rgb[pal * 16 + p][m]; t[m, 3] = 255
    rock_ids[int(s)] = len(rock_tiles); rock_tiles.append(t)
_, _, rrgb, _, rpixels = load(rom, CFG.get('region_levels', [50, 51, 55]))
ground_ids = {None: 0}; ground_tiles = [np.zeros((8, 8), np.uint8)]; ground_rows = [0]
def gtile(t):
    if t not in ground_ids:
        p = pix(rpixels[t[0]])
        if t[1] & 0x400: p = p[:, ::-1]
        if t[1] & 0x800: p = p[::-1]
        ground_ids[t] = len(ground_tiles); ground_tiles.append(p.astype(np.uint8)); ground_rows.append(t[1] >> 12)
    return ground_ids[t]
s0, s1, smax = CFG.get('shade', [8, 40, 0.35])
RK = np.zeros((H8, W8), np.uint16); GR = np.zeros((H8, W8), np.uint16); SH = np.zeros((H8, W8), np.uint8)
for y, x in zip(*np.nonzero(M)):
    RK[y, x] = rock_ids[int(rock[y, x])]; GR[y, x] = gtile(under[(y, x)])
    SH[y, x] = int(round(15 * min(1.0, max(0.0, (dM[y, x] - s0) / s1))))
print('rock tiles', len(rock_tiles) - 1, 'ground tiles', len(ground_tiles) - 1)
def atlas(tiles, mode):
    n = len(tiles); rows_ = (n + 63) // 64
    a = np.zeros((rows_ * 8, 64 * 8) + tiles[0].shape[2:], np.uint8)
    for i, t in enumerate(tiles): a[(i // 64) * 8:(i // 64) * 8 + 8, (i % 64) * 8:(i % 64) * 8 + 8] = t
    return Image.fromarray(a, mode)
atlas(rock_tiles, 'RGBA').save(os.path.join(out, 'mountains-rock.png'), optimize=True)
atlas(ground_tiles, 'L').save(os.path.join(out, 'mountains-ground.png'), optimize=True)
KR, KI = CFG.get('key', [8, 1])
blob = b'MTN1' + struct.pack('<HH', W8, H8) + RK.tobytes() + GR.tobytes() + SH.tobytes()
open(os.path.join(out, 'mountains.bin'), 'wb').write(zlib.compress(blob, 9))
info = dict(W8=W8, H8=H8, rock=len(rock_tiles), ground=len(ground_tiles), ground_rows=ground_rows, key=[KR, KI],
            shade=smax, spots=int(M.sum()))
json.dump(info, open(os.path.join(out, 'mountains.json'), 'w'))

# ---- the map: key tiles, blocked ---------------------------------------------------------------------------------------
KEY = (('key', KI), KR << 12)
for y, x in zip(*np.nonzero(M)):
    GA[y][x] = KEY; GB[y][x] = (0, 0); GC[y][x] = 1
R['GA'], R['GB'], R['GC'] = GA, GB, GC; R['mountains'] = M
pickle.dump(R, open(os.path.join(out, 'region.pkl'), 'wb'))
for f in ('region.json',):
    if os.path.exists(os.path.join(rdir, f)): open(os.path.join(out, f), 'w').write(open(os.path.join(rdir, f)).read())

# ---- preview: the region picture with the mountains drawn (source palette for the ground) ------------------------------
Image.MAX_IMAGE_PIXELS = None
im = np.array(Image.open(os.path.join(rdir, 'region.png')).convert('RGB'))
for y, x in zip(*np.nonzero(M)):
    g = ground_tiles[GR[y, x]]; c = rrgb[ground_rows[GR[y, x]] * 16 + g].astype(np.float32)
    r = rock_tiles[RK[y, x]]; a = r[..., 3:] / 255.0
    c = r[..., :3] * a + c * (1 - a)
    c *= 1 - smax * SH[y, x] / 15.0
    im[y * 8:y * 8 + 8, x * 8:x * 8 + 8] = c.clip(0, 255).astype(np.uint8)
for y, x in zip(*np.nonzero(passes & void)):
    t = GA[y][x]; p = pix(rpixels[t[0]])
    if t[1] & 0x400: p = p[:, ::-1]
    if t[1] & 0x800: p = p[::-1]
    im[y * 8:y * 8 + 8, x * 8:x * 8 + 8] = rrgb[(t[1] >> 12) * 16 + p]
Image.fromarray(im).save(os.path.join(out, 'region.png'))
print('done', out, 'bin', os.path.getsize(os.path.join(out, 'mountains.bin')))
