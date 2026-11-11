"""Cut colour-plan hero repaints into skin-atlas tiles (same keys as tools/skin/spritecut.py).

usage: herocut.py out.npz name:capdump [name:capdump ...]
capdump = records of OBJ VRAM 0x06010000 (0x8000) + palette RAM (0x400) + OAM (0x400), as written by
run.c 'dump' lines. Each record: hero pieces = OBJ palette 0 sprites plus palette 2 pieces (weapons)
touching them. The whole hero is repainted at 4x as one picture (paint4x, ramps from heroes.py), then
each piece is un-flipped and cut into 32x32 cells keyed fnv(tile bytes) fnv(palette bank) 8bpp-flag.
Cells are fully opaque wherever the game pixel is, so the skin pass shows only the planned colours."""
import sys, numpy as np
from oklab import from555, to_lch, gba
from plan import RAMPS
from paint4x import paint, scale2x
from heroes import TAGS, SHARED, hero_t
SIZES = {0: [(8,8),(16,16),(32,32),(64,64)], 1: [(16,8),(32,8),(32,16),(64,32)], 2: [(8,16),(8,32),(16,32),(32,64)]}
REC = 0x8800
def fnv(b):
    h = 0x811c9dc5
    for x in b: h = ((h ^ x) * 0x01000193) & 0xffffffff
    return h
def pieces(rec):
    vram, pal, oam = rec[:0x8000], rec[0x8000:0x8400], rec[0x8400:0x8800]
    out = []
    for i in range(128):
        a0, a1, a2 = [int.from_bytes(oam[i*8+k:i*8+k+2], 'little') for k in (0, 2, 4)]
        if a0 & 0x300: continue                        # affine or hidden
        sh, sz = a0 >> 14, a1 >> 14
        if sh == 3: continue
        w, h = SIZES[sh][sz]; y = a0 & 255; x = a1 & 511; t = a2 & 0x3ff; bank = a2 >> 12; c256 = (a0 >> 13) & 1
        if y >= 160: y -= 256
        if x >= 256: x -= 512
        if c256: continue
        pb = pal[0x200 + bank*32: 0x200 + bank*32 + 32]; pk = '%08x' % fnv(pb)
        img = np.zeros((h, w), int); keys = []
        for ty in range(h // 8):
            for tx in range(w // 8):
                off = (t + ty * (w // 8) + tx) * 32 - 0x0                # 1D mapping, OBJ VRAM base
                tb = vram[off:off + 32]
                if len(tb) < 32: break
                a = np.frombuffer(tb, np.uint8)
                img[ty*8:ty*8+8, tx*8:tx*8+8] = np.stack([a & 15, a >> 4], 1).reshape(8, 8)
                keys.append((tx, ty, '%08x%s0' % (fnv(tb), pk)))
        out.append(dict(i=i, x=x, y=y, w=w, h=h, bank=bank, hf=(a1 >> 12) & 1, vf=(a1 >> 13) & 1, img=img, keys=keys,
                        prio=(a2 >> 10) & 3, pal=[from555(int(v)) for v in np.frombuffer(pb, '<u2')]))
    return out
def hero_pieces(ps):
    h0 = [p for p in ps if p['bank'] == 0]
    if not h0: return []
    x0 = min(p['x'] for p in h0) - 16; y0 = min(p['y'] for p in h0) - 16
    x1 = max(p['x'] + p['w'] for p in h0) + 16; y1 = max(p['y'] + p['h'] for p in h0) + 16
    return h0 + [p for p in ps if p['bank'] == 2 and p['x'] < x1 and p['x'] + p['w'] > x0 and p['y'] < y1 and p['y'] + p['h'] > y0]
def cut(name, recs, cells):
    tags = dict(TAGS[name]); seen = set(); n = 0
    for rec in recs:
        hp = hero_pieces(pieces(rec))
        if not hp: continue
        sig = tuple(sorted((p['x'], p['y'], p['hf'], p['vf'], p['bank'], tuple(k for _, _, k in p['keys'])) for p in hp))
        if sig in seen: continue
        seen.add(sig)
        x0 = min(p['x'] for p in hp); y0 = min(p['y'] for p in hp)
        W = max(p['x'] + p['w'] for p in hp) - x0; H = max(p['y'] + p['h'] for p in hp) - y0
        idx = np.full((H, W), -1); cols = {}
        for p in sorted(hp, key=lambda p: -p['i']):             # lower OAM index drawn on top
            im = p['img'][:, ::-1] if p['hf'] else p['img']
            im = im[::-1] if p['vf'] else im
            sub = idx[p['y']-y0:p['y']-y0+p['h'], p['x']-x0:p['x']-x0+p['w']]
            m = im > 0; sub[m] = p['bank']*16 + im[m]
            for c in range(1, 16): cols[p['bank']*16 + c] = p['pal'][c]
        table = {}
        for v in np.unique(idx):
            if v < 0: continue
            m = tags.get(v) if v < 16 else SHARED.get(v - 32, 'steel')
            table[v] = (m or 'steel', hero_t(to_lch(cols[v])[0]))
        shadow = tuple(v for v, (m, _) in table.items() if m == 'shadow')
        pic = paint(idx, table, norim=shadow)
        flat = np.zeros((H, W, 3), np.uint8)
        for v, (m, t) in table.items(): flat[idx == v] = gba(RAMPS[m](t))[0]
        flat4 = flat.repeat(4, 0).repeat(4, 1)
        rgb = np.where(pic[..., 3:4] > 0, pic[..., :3], flat4)
        for p in hp:
            sl = rgb[(p['y']-y0)*4:(p['y']-y0+p['h'])*4, (p['x']-x0)*4:(p['x']-x0+p['w'])*4]
            if p['hf']: sl = sl[:, ::-1]
            if p['vf']: sl = sl[::-1]
            own = (p['img'] > 0).repeat(4, 0).repeat(4, 1)
            for tx, ty, k in p['keys']:
                if k in cells: continue
                m = own[ty*32:ty*32+32, tx*32:tx*32+32]
                if not m.any(): continue
                cell = np.zeros((32, 32, 4), np.uint8)
                cell[..., :3] = sl[ty*32:ty*32+32, tx*32:tx*32+32]; cell[..., 3] = m * 255
                cells[k] = cell
        n += 1
    return n
if __name__ == '__main__':
    out = sys.argv[1]; cells = {}
    for a in sys.argv[2:]:
        name, path = a.split(':', 1); D = open(path, 'rb').read()
        recs = [D[o:o+REC] for o in range(0, len(D) - REC + 1, REC)]
        before = len(cells); n = cut(name, recs, cells)
        print(name, 'poses', n, 'new tiles', len(cells) - before, flush=True)
    np.savez_compressed(out, **cells); print('total tiles', len(cells))
