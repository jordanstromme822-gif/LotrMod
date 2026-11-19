"""Siege map, step 2: the Helm's Deep fort from Jordan's drawing (2026-11-19).

Usage: python3 tools/siege/fort.py ROM.gba OUT_DIR [--base 0x1500000]

Output is the same as build.py (siege.bin, tables.bin, siege.json, preview.png) for level slot 45.

Drawing (uploads/siege/siege-drawing-2026-11-19.jpeg): a walled fort at the bottom middle of the map,
walls all round with towers at the corners, a gatehouse in the north wall (Outer Gate 1200 HP, a short
passage, Inner Gate 1800 HP), a broken-bridge exit in the west wall near the top that heroes jump
across, hero spawn bottom left inside, open land to the north.

The game has art only for one kind of wall (seen from the courtyard side), so the walls, towers,
stairs, gates and bridge are drawn here in Python (own art) with the level's own grey and brown
colours, and turned into extra tiles. Ground (grass, forest) is the game's own Hornburg tiles.
View is the game's: from the south, looking down. Faces that point south are seen; the tops of all
walls are walkways, reached by two staircases against the north wall.
"""
import os, random, struct, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import Rom, OBJECTS  # noqa: E402
from build import (Level, BLANK, pix, render, quantize_tile, draw_gate, write_map)  # noqa: E402

W, H = 160, 160                 # tiles (8 px); 40 x 40 cells
# fort (tile coordinates). Wall tops are T tiles thick: 1 parapet + walkway + 1 parapet.
X0, X1 = 40, 120                # outer edge of the west wall .. outer edge of the east wall
Y0, Y1 = 90, 152                # outer edge of the north wall .. outer (south) edge of the south wall
T = 8
FACE = 10                       # height of the wall faces we see (north wall inside, south wall outside)
TOWER = 14                      # corner towers stick out from the corners by TOWER - T
GATE = (76, 84)                 # gatehouse columns in the north wall (opening 77..82)
STAIRS = [(56, 60), (100, 104)] # staircases against the north wall face
BRIDGE = (112, 118)             # rows of the broken bridge through the west wall
START = (52, 138)               # hero start (tiles), bottom left inside (drawing: "hero spawn")
VENDORS = [(60, 122, 2), (98, 122, 0)]   # spirit shrine (kind 2), forge (kind 0)
TORCHES = [(74, 110), (86, 110)]         # either side of the Inner Gate

# colours (all in the level's palette bank 15 / 10, so they map exactly)
K = {'black': (16, 16, 16), 'd1': (32, 32, 32), 'd2': (56, 56, 56), 'd3': (72, 72, 72), 'm1': (96, 96, 96),
     'm2': (104, 104, 104), 'm3': (112, 112, 112), 'l1': (128, 128, 128), 'l2': (152, 152, 152), 'l3': (176, 176, 176)}
WOOD = [(112, 88, 48), (88, 72, 40), (136, 120, 40), (80, 72, 40), (64, 48, 40), (40, 32, 24)]


def C(n): return np.array(K[n], np.int32)


def tex_walk(h, w, oy=0, ox=0):
    """Walkway flagstones: 16 x 16 slabs, rows staggered by 8 px."""
    img = np.zeros((h, w, 3), np.int32)
    for y in range(h):
        for x in range(w):
            yy = (y + oy) % 32; xx = (x + ox + (8 if yy >= 16 else 0)) % 16; sy = yy % 16
            if sy == 0 or xx == 0: c = 'd3'
            elif sy == 1 or xx == 1: c = 'l2'
            elif sy == 15 or xx == 15: c = 'm1'
            else: c = 'l1' if ((x + ox) // 16 + (y + oy) // 16) % 3 else 'm3'
            img[y, x] = K[c]
    return img


def tex_face(h, w, ox=0):
    """Wall face: 16 x 8 bricks, courses staggered by 8 px; a capstone ledge on top, dark base."""
    img = np.zeros((h, w, 3), np.int32)
    for y in range(h):
        for x in range(w):
            if y < 6:                                   # ledge
                c = 'l3' if y < 2 else ('l2' if y < 5 else 'd1')
            elif y >= h - 3:
                c = 'd2' if y < h - 1 else 'd1'
            else:
                yy = y - 6; course = yy // 8; sy = yy % 8
                xx = (x + ox + (8 if course % 2 else 0)) % 16
                if sy == 7 or xx == 15: c = 'd2'
                elif sy == 0: c = 'l1'
                elif xx == 0: c = 'm3'
                else: c = 'm2' if ((x + ox + (8 if course % 2 else 0)) // 16 + course) % 2 else 'm1'
            img[y, x] = K[c]
    return img


def parapet(img, y0, x0, h, w, side):
    """Battlements along one edge of a walkway, seen from above: side = 'n', 's', 'w' or 'e'
    (which edge of the box y0, x0, h, w they sit on; the box is the 8 px strip)."""
    for y in range(h):
        for x in range(w):
            along = x if side in 'ns' else y
            across = y if side in 'ns' else x
            if side in 'se': across = (h if side == 's' else w) - 1 - across   # 0 = outer edge
            merlon = (along % 16) < 10
            if across == 0: c = 'd1'
            elif merlon:
                c = 'l3' if across in (1, 2) else ('l2' if across < 6 else 'd2')
            else:
                c = 'm1' if across < 4 else ('m2' if across < 7 else 'd2')
            img[y0 + y, x0 + x] = K[c]


def stairs(img, y0, x0, h, w):
    """Straight stairs running up (north) against a wall face: 4 px steps."""
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2: c = 'd2' if x in (0, w - 1) else 'm1'
            else: c = 'l3' if (y % 4) < 2 else 'm1'
            if y >= h - 2 and 2 <= x < w - 2: c = 'm1'
            img[y0 + y, x0 + x] = K[c]


def bridge(img, y0, x0, h, w):
    """Broken wooden bridge across a gap in a wall (planks run east-west, middle missing)."""
    for y in range(h):
        for x in range(w):
            gap = abs(x - w // 2) < 5 + (3 if (y // 4) % 2 else 0) - (2 if (y // 8) % 2 else 0)
            if y < 3 or y >= h - 3:
                c = (24, 24, 24)
            elif gap:
                c = (16, 16, 16) if (x + y) % 7 else (32, 32, 32)
            else:
                plank = (y - 3) // 6; sy = (y - 3) % 6
                c = WOOD[4] if sy == 5 else (WOOD[2] if sy == 0 else WOOD[plank % 2])
                if (x == w // 2 - 6 - (3 if (y // 4) % 2 else 0) or x == w // 2 + 5 + (3 if (y // 4) % 2 else 0)):
                    c = WOOD[5]
            img[y0 + y, x0 + x] = c


def outer_gate(img, y0, x0, h, w):
    """Outer Gate seen from above in the gap of the north parapet: stone posts and both doors
    swung open against the walkway."""
    for y in range(h):
        for x in range(w):
            if x < 8 or x >= w - 8:                       # gate posts
                c = 'l3' if y < 3 else ('l2' if y < 12 else 'd2')
                img[y0 + y, x0 + x] = K[c]
            elif x < 12 or x >= w - 12:                   # open doors, edge on
                c = WOOD[0] if (y // 3) % 2 else WOOD[1]
                if y % 10 == 5: c = (40, 40, 40)
                img[y0 + y, x0 + x] = c


def build(rom_path, out_dir, base=0x1500000, seed=7):
    R = Rom(rom_path)
    a, b = Level(R, 46), Level(R, 47)
    pal = R.rom[a.e[15] - 0x08000000:][:0x200]
    P = np.frombuffer(pal, dtype='<u2')
    rgb = np.stack([(P & 31) << 3, ((P >> 5) & 31) << 3, ((P >> 10) & 31) << 3], 1).astype(np.int32)
    LA, LB, CA = a.tilegrid(0), a.tilegrid(1), a.colgrid()
    MA, MB, MC = b.tilegrid(0), b.tilegrid(1), b.colgrid()
    need = sorted(set(t[0] for g in (LA, MA, LB, MB) for row in g for t in row))
    pixels = dict(zip(need, R.tiles(a.tileset, need)))
    lumP = rgb.sum(1) / 3.0

    def mlum(t):
        p = pix(pixels[t[0]]); return float(np.mean([lumP[(t[1] >> 12) * 16 + v] if v else 0 for v in p.flatten()]))
    # plain light grass cells from the bottom left of Hornburg (as build.py)
    cells = []
    for cy in range(19, 24):
        for cx in range(0, 13):
            blk = [(LA[cy * 4 + k // 4][cx * 4 + k % 4], LB[cy * 4 + k // 4][cx * 4 + k % 4],
                    CA[cy * 4 + k // 4][cx * 4 + k % 4]) for k in range(16)]
            if any(t[1][0] != BLANK or t[2] in (1, 2) for t in blk): continue
            cells.append((np.mean([mlum(t[0]) for t in blk]), blk))
    top = max(c[0] for c in cells)
    grass_cells = [c[1] for c in cells if c[0] > top - 3]
    rnd = random.Random(seed); choice = {}

    def grass_at(x, y):
        k = (x // 4, y // 4)
        if k not in choice: choice[k] = rnd.randrange(len(grass_cells))
        return grass_cells[choice[k]][(y % 4) * 4 + x % 4]
    forest = [(MA[y][x], MB[y][x], MC[y][x]) for y in range(86, 100) for x in range(0, 36)]   # 14 x 36 tree line
    FR = 14

    GA = [[None] * W for _ in range(H)]; GB = [[None] * W for _ in range(H)]; GC = [[0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            ta, tb, _ = grass_at(x, y); GA[y][x] = ta; GB[y][x] = tb
    # forest round the map edge (the drawing's grey edge): a tree line on top, left and right
    for y in range(H):
        for x in range(W):
            if y < FR or x < 10 or x >= W - 10:
                ta, tb, c = forest[(y % FR) * 36 + (x % 36)]
                GA[y][x] = ta; GB[y][x] = tb; GC[y][x] = 1 if c & 7 in (1, 2) or y < FR - 2 or x < 8 or x >= W - 8 else c

    # --- paint the fort -----------------------------------------------------------------
    img = render(GA, GB, pixels, rgb, 0, 0, W, H)
    before = img.copy()
    P8 = lambda v: v * 8                       # noqa: E731
    walk = np.zeros((H, W), bool); block = np.zeros((H, W), bool); stair = np.zeros((H, W), bool)

    def wall_top(x0, y0, x1, y1, edges):
        """Walkway box (tiles) with battlements on the given edges."""
        img[P8(y0):P8(y1), P8(x0):P8(x1)] = tex_walk(P8(y1 - y0), P8(x1 - x0), P8(y0), P8(x0))
        walk[y0:y1, x0:x1] = True
        for e in edges:
            if e == 'n': parapet(img, P8(y0), P8(x0), 8, P8(x1 - x0), 'n'); block[y0, x0:x1] = True
            if e == 's': parapet(img, P8(y1 - 1), P8(x0), 8, P8(x1 - x0), 's'); block[y1 - 1, x0:x1] = True
            if e == 'w': parapet(img, P8(y0), P8(x0), P8(y1 - y0), 8, 'w'); block[y0:y1, x0] = True
            if e == 'e': parapet(img, P8(y0), P8(x1 - 1), P8(y1 - y0), 8, 'e'); block[y0:y1, x1 - 1] = True

    def face(x0, y0, x1, h):
        img[P8(y0):P8(y0 + h), P8(x0):P8(x1)] = tex_face(P8(h), P8(x1 - x0), P8(x0))
        block[y0:y0 + h, x0:x1] = True

    ext = TOWER - T
    # wall tops: north, south, west, east (inner battlements on the courtyard side too)
    wall_top(X0, Y0, X1, Y0 + T, 'ns')
    wall_top(X0, Y1 - T, X1, Y1, 'ns')
    wall_top(X0, Y0, X0 + T, Y1, 'we')
    wall_top(X1 - T, Y0, X1, Y1, 'we')
    # corner towers: bigger platforms sticking out of the corners, battlements on the outside
    for (tx, ty) in ((X0 - ext, Y0 - ext), (X1 - T, Y0 - ext), (X0 - ext, Y1 - T), (X1 - T, Y1 - T)):
        wall_top(tx, ty, tx + TOWER, ty + TOWER, 'nswe')
    # where the wall walkways meet a tower, open its battlements so you can walk on
    for (tx, ty) in ((X0 - ext, Y0 - ext), (X1 - T, Y0 - ext), (X0 - ext, Y1 - T), (X1 - T, Y1 - T)):
        # re-lay the walkway over the joins (one tile in from the tower edge)
        if ty < Y0:      # north towers: joins on the south edge (west/east wall) and on the inner side (north wall)
            jx0, jx1 = (X0 + 1, X0 + T - 1) if tx < X0 else (X1 - T + 1, X1 - 1)
            img[P8(ty + TOWER - 1):P8(ty + TOWER), P8(jx0):P8(jx1)] = tex_walk(8, P8(jx1 - jx0), P8(ty + TOWER - 1), P8(jx0))
            block[ty + TOWER - 1, jx0:jx1] = False
            jx = tx + TOWER - 1 if tx < X0 else tx
            img[P8(Y0 + 1):P8(Y0 + T - 1), P8(jx):P8(jx + 1)] = tex_walk(P8(T - 2), 8, P8(Y0 + 1), P8(jx))
            block[Y0 + 1:Y0 + T - 1, jx] = False
        else:            # south towers: joins on the north edge and the inner side
            jx0, jx1 = (X0 + 1, X0 + T - 1) if tx < X0 else (X1 - T + 1, X1 - 1)
            img[P8(ty):P8(ty + 1), P8(jx0):P8(jx1)] = tex_walk(8, P8(jx1 - jx0), P8(ty), P8(jx0))
            block[ty, jx0:jx1] = False
            jx = tx + TOWER - 1 if tx < X0 else tx
            img[P8(Y1 - T + 1):P8(Y1 - 1), P8(jx):P8(jx + 1)] = tex_walk(P8(T - 2), 8, P8(Y1 - T + 1), P8(jx))
            block[Y1 - T + 1:Y1 - 1, jx] = False
    # wall corners: open the battlements between the joined walkways
    for (cx0, cy0) in ((X0, Y0), (X1 - T, Y0), (X0, Y1 - T), (X1 - T, Y1 - T)):
        img[P8(cy0 + 1):P8(cy0 + T - 1), P8(cx0 + 1):P8(cx0 + T - 1)] = tex_walk(P8(T - 2), P8(T - 2), P8(cy0 + 1), P8(cx0 + 1))
        block[cy0 + 1:cy0 + T - 1, cx0 + 1:cx0 + T - 1] = False
    for (x, y0_, y1_) in ((X0 + T - 1, Y0 + 1, Y0 + T - 1), (X1 - T, Y0 + 1, Y0 + T - 1),
                          (X0 + T - 1, Y1 - T + 1, Y1 - 1), (X1 - T, Y1 - T + 1, Y1 - 1)):
        img[P8(y0_):P8(y1_), P8(x):P8(x + 1)] = tex_walk(P8(y1_ - y0_), 8, P8(y0_), P8(x)); block[y0_:y1_, x] = False
    for (y, x0_, x1_) in ((Y0 + T - 1, X0 + 1, X0 + T - 1), (Y0 + T - 1, X1 - T + 1, X1 - 1),
                          (Y1 - T, X0 + 1, X0 + T - 1), (Y1 - T, X1 - T + 1, X1 - 1)):
        img[P8(y):P8(y + 1), P8(x0_):P8(x1_)] = tex_walk(8, P8(x1_ - x0_), P8(y), P8(x0_)); block[y, x0_:x1_] = False
    # faces we see: north wall from the courtyard, south wall and south towers from outside
    face(X0 + T, Y0 + T, X1 - T, FACE)
    face(X0 - ext, Y1, X1 + ext, H - Y1)
    # staircases up the north wall face (and through its inner battlements)
    for sx0, sx1 in STAIRS:
        stairs(img, P8(Y0 + T - 1), P8(sx0), P8(FACE + 1), P8(sx1 - sx0))
        block[Y0 + T - 1:Y0 + T + FACE, sx0:sx1] = False; stair[Y0 + T - 1:Y0 + T + FACE, sx0:sx1] = True
    # gatehouse: Outer Gate in the north battlements, a passage over the wall top, Inner Gate arch in the face
    g0, g1 = GATE
    img[P8(Y0):P8(Y0 + T - 1), P8(g0):P8(g1)] = tex_walk(P8(T - 1), P8(g1 - g0), P8(Y0), P8(g0))
    outer_gate(img, P8(Y0) - 6, P8(g0), 6 + 20, P8(g1 - g0))
    img[P8(Y0 + T - 1):P8(Y0 + T), P8(g0 + 1):P8(g1 - 1)] = tex_walk(8, P8(g1 - g0 - 2), P8(Y0 + T - 1), P8(g0 + 1))
    gate_img = draw_gate(img[P8(Y0 + T):P8(Y0 + T + FACE), P8(g0):P8(g1)].copy())
    img[P8(Y0 + T):P8(Y0 + T + FACE), P8(g0):P8(g1)] = gate_img
    block[Y0 - 1:Y0 + T + FACE, g0 + 1:g1 - 1] = False
    # broken bridge through the west wall near the top (heroes jump across)
    b0, b1 = BRIDGE
    bridge(img, P8(b0), P8(X0 - 2), P8(b1 - b0), P8(T + 4))
    block[b0:b1, X0 - 2:X0 + T + 2] = False; walk[b0:b1, X0:X0 + T] = False

    # shadows on the ground east of the wall tops and towers (light from the top left) for height
    stone = walk | block | stair
    for y in range(H):
        for x in range(1, W):
            if stone[y, x - 1] and not stone[y, x] and not (b0 <= y < b1):
                sl = img[P8(y):P8(y + 1), P8(x):P8(x) + 6]
                img[P8(y):P8(y + 1), P8(x):P8(x) + 6] = (sl * 0.55).astype(np.int32)
    # --- turn painted areas into tiles ------------------------------------------------------
    n_last = struct.unpack('<H', R.rom[a.tileset - 0x08000000 + 0xE:][:2])[0]
    first = 1024 + n_last
    custom, seen = {}, {}
    for ty in range(H):
        for tx in range(W):
            blk = img[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if np.array_equal(blk, before[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]): continue
            bank, tb = quantize_tile(blk, rgb, (15, 14, 11, 10, 8))
            if (bank, tb) not in seen:
                seen[(bank, tb)] = first + len(custom); custom[seen[(bank, tb)]] = tb; pixels[seen[(bank, tb)]] = tb
            GA[ty][tx] = (seen[(bank, tb)], bank << 12); GB[ty][tx] = (BLANK, 0)

    # --- walking --------------------------------------------------------------------------
    for y in range(H):
        for x in range(W):
            if stair[y, x]: GC[y][x] = 7
            elif block[y, x]: GC[y][x] = 1
            elif walk[y, x]: GC[y][x] = 3
            elif GC[y][x] in (1, 2) and FR <= y and 10 <= x < W - 10: GC[y][x] = 0
    for y in range(H): GC[y][0] = GC[y][W - 1] = 1
    for x in range(W): GC[0][x] = GC[H - 1][x] = 1

    # --- objects ------------------------------------------------------------------------------
    torch_rec = None
    bl = R.u32(OBJECTS + 12 * 46 + 4)
    s_ = struct.unpack('<H', R.rom[bl - 0x08000000:][:2])[0]
    p1o = struct.unpack('<H', R.rom[bl - 0x08000000 + s_ + 0xC + 8:][:2])[0]
    from spawns import parse_groups
    for g in parse_groups(R.decomp(bl + p1o)[8:]):
        for it in g['items']:
            if it[0] == 19 and torch_rec is None: torch_rec = it
    items = [torch_rec[:4] + struct.pack('<HH', tx * 8, ty * 8) + torch_rec[8:] for tx, ty in TORCHES]
    items += [bytes([17, 0, 0, 0]) + struct.pack('<HH', tx * 8, ty * 8) + bytes([kind, 0xFF, 0xFF, 0xFF]) for tx, ty, kind in VENDORS]
    return write_map(R, a, GA, GB, GC, W, H, pixels, rgb, custom, n_last, items, (START[0] * 8, START[1] * 8),
                     out_dir, base, dict(map='fort', torches=len(TORCHES), vendors=len(VENDORS)))


if __name__ == '__main__':
    import json
    args = sys.argv[1:]
    base = 0x1500000
    if '--base' in args: i = args.index('--base'); base = int(args[i + 1], 0); del args[i:i + 2]
    print(json.dumps(build(args[0], args[1], base), indent=1))
