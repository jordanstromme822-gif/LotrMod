"""Siege map, step 3 (Jordan 2026-11-20): the fort from the drawing (fort.py) on the left and Helm's Deep
(build.py: Hornburg + Valley, cropped) as the bottom-right part, joined by a dirt road. The breach in the
Deeping Wall gets a wooden gate (closed; breaking it later puts the rubble back: the rubble tiles are
the map's own, the gate is drawn over them).

Usage: python3 tools/siege/combine.py ROM.gba OUT_DIR [--base 0x1500000]
"""
import os, struct, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as hd_mod  # noqa: E402
import fort as fort_mod  # noqa: E402
from build import BLANK, render, quantize_tile, write_map  # noqa: E402

DOWN = 40                         # fort map is made 40 rows taller (more land north of it)
HDX = 160                         # Helm's Deep crop starts at this column
# dirt road (tile coordinates of the joined map): fort Outer Gate -> north -> east -> Helm's Deep north gate
ROAD_W = 4
ROAD = [((78, 60), (78, 130)), ((78, 60), (215, 60)), ((214, 60), (214, 84))]
# breach gate: a timber gate standing in the rubble (joined-map tiles)
BGATE = (265, 118, 283, 137)      # x0, y0, x1, y1
BGATE_BLOCK = (260, 124, 290, 133)  # rows/cols made solid while the gate stands

WOOD = [(112, 88, 48), (88, 72, 40), (136, 120, 40), (80, 72, 40), (64, 48, 40), (40, 32, 24)]


def noise(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0xFF


def paint_road(img, mask):
    """Dirt inside the mask; its outer 1-tile ring is a ragged dirt/grass verge. Pattern repeats every
    32 px so few tiles are needed."""
    H8, W8 = img.shape[:2]
    dirt = [(112, 80, 48), (112, 88, 48), (80, 72, 40), (136, 120, 40), (64, 48, 40)]
    grass = [(56, 120, 80), (80, 104, 80), (40, 88, 56), (96, 120, 104)]
    m = np.kron(mask, np.ones((8, 8), bool))
    # distance (px) to the outside of the mask, capped at 9
    dist = np.full(m.shape, 9, np.int32)
    for d in range(1, 9):
        sh = np.zeros_like(m)
        sh[d:, :] |= ~m[:-d, :]; sh[:-d, :] |= ~m[d:, :]; sh[:, d:] |= ~m[:, :-d]; sh[:, :-d] |= ~m[:, d:]
        dist[m & sh & (dist == 9)] = d
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        n = noise(x % 32, y % 32)
        edge = 3 + (noise((x // 4) % 8, (y // 4) % 8, 1) % 5)       # ragged verge 3..7 px
        if dist[y, x] <= edge:
            c = grass[n % 4] if n % 7 else dirt[4]
        else:
            c = dirt[0] if n < 150 else dirt[1] if n < 200 else dirt[2] if n < 235 else dirt[3]
        img[y, x] = c


def paint_gate(img, x0, y0, x1, y1):
    """Timber gate filling the breach: two posts, a lintel, double doors with iron bands."""
    w, h = (x1 - x0) * 8, (y1 - y0) * 8
    for y in range(h):
        for x in range(w):
            X, Y = x0 * 8 + x, y0 * 8 + y
            if y >= h - 2: c = (40, 32, 24)
            elif x < 14 or x >= w - 14:                     # posts
                c = WOOD[1] if (x % 14) not in (0, 13) else WOOD[5]
                if y < 4: c = WOOD[2]
            elif y < 16:                                    # lintel
                c = WOOD[0] if y % 8 not in (0, 7) else WOOD[5]
                if 4 <= y % 8 <= 5 and x % 24 == 12: c = (176, 168, 56)
            else:
                xx = x - 14; mid = (w - 28) // 2
                if abs(xx - mid) < 2: c = WOOD[5]           # doors meet
                else:
                    plank = (xx // 8) % 2
                    c = WOOD[0] if plank else WOOD[3]
                    if xx % 8 == 0: c = WOOD[4]
                    band = (y - 16) % 40
                    if band in (10, 11, 12, 13): c = (48, 48, 48)
                    if band in (11, 12) and xx % 8 == 4: c = (176, 168, 56)
            img[Y, X] = c


def build(rom_path, out_dir, base=0x1500000):
    # fort, made taller (everything moved down by DOWN rows)
    f = fort_mod
    f.H = f.H + DOWN
    f.Y0 += DOWN; f.Y1 += DOWN
    f.BRIDGE = (f.BRIDGE[0] + DOWN, f.BRIDGE[1] + DOWN)
    f.START = (f.START[0], f.START[1] + DOWN)
    f.VENDORS = [(x, y + DOWN, k) for x, y, k in f.VENDORS]
    f.TORCHES = [(x, y + DOWN) for x, y in f.TORCHES]
    F = f.build(rom_path, None, base, grids_only=True)
    D = hd_mod.build(rom_path, None, base, grids_only=True)
    assert F['H'] == D['H'] == 200 and F['W'] == 160 and D['W'] == 160
    R, a, rgb = D['R'], D['a'], D['rgb']
    W, H = F['W'] + D['W'], D['H']
    # custom tiles: Helm's Deep keeps its numbers, the fort's move up after them
    pixels = dict(D['pixels']); pixels.update({k: v for k, v in F['pixels'].items() if k < 1024 + D['n_last']})
    custom = dict(D['custom']); byb = {v: k for k, v in custom.items()}
    first = 1024 + D['n_last']
    remap = {}
    for t, tb in sorted(F['custom'].items()):
        if tb not in byb:
            byb[tb] = first + len(custom); custom[byb[tb]] = tb
        remap[t] = byb[tb]
    for t, tb in custom.items(): pixels[t] = tb
    GA = [[None] * W for _ in range(H)]; GB = [[None] * W for _ in range(H)]; GC = [[1] * W for _ in range(H)]
    for y in range(H):
        for x in range(F['W']):
            t = F['GA'][y][x]; GA[y][x] = (remap.get(t[0], t[0]), t[1]); GB[y][x] = F['GB'][y][x]; GC[y][x] = F['GC'][y][x]
        for x in range(D['W']):
            GA[y][HDX + x] = D['GA'][y][x]; GB[y][HDX + x] = D['GB'][y][x]; GC[y][HDX + x] = D['GC'][y][x]

    # --- paint the road and the breach gate, turn them into tiles -------------------------------
    img = render(GA, GB, pixels, rgb, 0, 0, W, H); before = img.copy()
    mask = np.zeros((H, W), bool)
    for (ax, ay), (bx, by) in ROAD:
        x0, x1 = min(ax, bx), max(ax, bx) + ROAD_W; y0, y1 = min(ay, by), max(ay, by) + (ROAD_W if ay == by else 0)
        mask[y0:y1, x0:x1] = True
    paint_road(img, mask)
    paint_gate(img, *BGATE)
    for ty in range(H):
        for tx in range(W):
            blk = img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if np.array_equal(blk, before[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]): continue
            bank, tb = quantize_tile(blk, rgb, (8, 10, 15, 14, 13, 12, 11))
            key = tb
            if key not in byb:
                byb[key] = first + len(custom); custom[byb[key]] = tb; pixels[byb[key]] = tb
            GA[ty][tx] = (byb[key], bank << 12); GB[ty][tx] = (BLANK, 0)
    # walking: the road is open ground (it cuts through the forest strip and the old map edge)
    for y in range(H):
        for x in range(W):
            if mask[y, x]: GC[y][x] = 0
    gx0, gy0, gx1, gy1 = BGATE_BLOCK
    for y in range(gy0, gy1):
        for x in range(gx0, gx1): GC[y][x] = 1
    for y in range(H): GC[y][0] = GC[y][W - 1] = 1
    for x in range(W): GC[0][x] = GC[H - 1][x] = 1

    # --- objects: both maps' records, Helm's Deep ones moved right ---------------------------------
    items = list(F['items'])
    for it in D['items']:
        x, y = struct.unpack('<HH', it[4:8])
        items.append(it[:4] + struct.pack('<HH', x + HDX * 8, y) + it[8:])
    return write_map(R, a, GA, GB, GC, W, H, pixels, rgb, custom, D['n_last'], items, F['start'], out_dir, base,
                     dict(map='fort + helms deep', drawn=len(custom)))


if __name__ == '__main__':
    import json
    args = sys.argv[1:]
    base = 0x1500000
    if '--base' in args: i = args.index('--base'); base = int(args[i + 1], 0); del args[i:i + 2]
    print(json.dumps(build(args[0], args[1], base), indent=1))
