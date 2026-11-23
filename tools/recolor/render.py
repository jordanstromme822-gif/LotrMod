"""Render a level to a palette-index image (0..255 = bank*16+idx), using the game's own data."""
import sys, numpy as np, pickle, os
sys.path.insert(0, '/home/user/lotrmod/tools/siege')
from romlib import Rom
from build import Level, pix
ROM = '/tmp/claude-0/-home-user/972dab79-8ec0-567e-9dbe-b1d16b78ca89/scratchpad/rom.gba'

def index_image(R, L):
    l = Level(R, L)
    need = set()
    gs = [l.tilegrid(0), l.tilegrid(1)]
    for g in gs:
        for row in g:
            for t in row: need.add(t[0])
    need = sorted(need)
    px = dict(zip(need, R.tiles(l.tileset, need)))
    H, W = l.h * 32, l.w * 32
    img = np.zeros((H, W), np.uint8)
    for layer, g in enumerate(gs):
        for ty, row in enumerate(g):
            for tx, t in enumerate(row):
                p = pix(px[t[0]])
                if t[1] & 0x400: p = p[:, ::-1]
                if t[1] & 0x800: p = p[::-1]
                v = ((t[1] >> 12) * 16 + p).astype(np.uint8)
                s = img[ty*8:ty*8+8, tx*8:tx*8+8]
                if layer == 0: s[:] = v
                else:
                    m = p != 0; s[m] = v[m]
    pal = np.frombuffer(R.rom[l.e[15] - 0x08000000:][:0x200], dtype='<u2').copy()
    return img, pal, l

if __name__ == '__main__':
    R = Rom(ROM)
    os.makedirs('idx', exist_ok=True)
    meta = {}
    for L in range(130):
        try:
            img, pal, l = index_image(R, L)
        except Exception as e:
            print(L, 'ERR', e); continue
        np.save('idx/%d.npy' % L, img)
        meta[L] = dict(pal=pal, palp=l.e[15], ts=l.tileset, w=l.w, h=l.h)
        print(L, l.w, l.h, hex(l.e[15]), hex(l.tileset), flush=True)
    pickle.dump(meta, open('meta.pkl', 'wb'))
