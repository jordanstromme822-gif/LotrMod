"""Cell (32 px metatile) data for joining levels: each cell = (16 A entries, 16 B entries, 16 walk bytes)."""
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/', 2)[0] + '/siege')
from romlib import Rom
from build import Level, pix
BLANK = 0   # this tileset (Isengard 0x893b038): tile 0 is the empty tile on both layers

def load(rom_path, levels):
    R = Rom(rom_path)
    lv = {L: Level(R, L) for L in levels}
    a = lv[levels[0]]
    P = np.frombuffer(R.rom[a.e[15] - 0x08000000:][:0x200], dtype='<u2')
    rgb = np.stack([(P & 31) << 3, ((P >> 5) & 31) << 3, ((P >> 10) & 31) << 3], 1).astype(np.int32)
    grids = {}
    for L, l in lv.items():
        A, B, C = l.tilegrid(0), l.tilegrid(1), l.colgrid()
        g = []
        for cy in range(l.h):
            row = []
            for cx in range(l.w):
                ks = [(cy * 4 + k // 4, cx * 4 + k % 4) for k in range(16)]
                row.append((tuple(A[y][x] for y, x in ks), tuple(B[y][x] for y, x in ks), tuple(C[y][x] for y, x in ks)))
            g.append(row)
        grids[L] = g
    need = sorted({t[0] for g in grids.values() for row in g for c in row for t in c[0] + c[1]})
    pixels = dict(zip(need, R.tiles(a.tileset, need)))
    return R, lv, rgb, grids, pixels

_tp = {}
def cell_img(c, pixels, rgb, cache={}):
    if c in cache: return cache[c]
    img = np.zeros((32, 32, 3), np.int32); trans = np.zeros((32, 32), bool)
    for layer in (0, 1):
        for k, t in enumerate(c[layer]):
            if layer == 1 and t[0] == BLANK: continue
            p = pix(pixels[t[0]])
            if t[1] & 0x400: p = p[:, ::-1]
            if t[1] & 0x800: p = p[::-1]
            col = rgb[(t[1] >> 12) * 16 + p]
            y, x = (k // 4) * 8, (k % 4) * 8
            if layer == 0:
                img[y:y + 8, x:x + 8] = col; trans[y:y + 8, x:x + 8] = p == 0
            else:
                m = p != 0; s = img[y:y + 8, x:x + 8]; s[m] = col[m]; tt = trans[y:y + 8, x:x + 8]; tt[m] = False
    cache[c] = (img, trans)
    return cache[c]
