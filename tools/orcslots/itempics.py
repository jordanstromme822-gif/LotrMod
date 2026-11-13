"""Item pictures for the HD Backpack (2026-11-12): every item's Backpack picture, cut from the game in mGBA.
Usage: itempics.py page.gba runner arag.state workdir out.png
  page.gba = a page ROM (buildGame), runner = tools/run.c built (mGBA headless), arag.state = a state in play (Aragorn).
For each batch of 8 items the script puts them in Aragorn's backpack grid, opens the Backpack and dumps DISPCNT, OAM,
OBJ palettes and OBJ VRAM; grid cell j's picture is the OBJ entries with palette 8 + j (two 32x16 / 32x8 sprites).
The 1-pixel frame and its shadow are cut off (26 x 20 left), each picture is scaled 4x with EPX (pixel-art edges, no
blur) and packed 16 per row into a 1664 x 1040 sheet, in category order (counts from the category table 0x08068F50
+0x24), index = start of the category + item index. The sheet is the game's art: keep it private (Play Room files only,
not in the repo)."""
import os, struct, subprocess, sys
import numpy as np
from PIL import Image

rom, runner, state, work, out = sys.argv[1:6]
os.makedirs(work, exist_ok=True)
r = open(rom, 'rb').read()
u = lambda a: struct.unpack('<I', r[a - 0x08000000:a - 0x08000000 + 4])[0]
items = []
for cat in range(15):
    for i in range(u(0x08068F50 + cat * 0x28 + 0x24)):
        items.append((cat, i, (0xFF0A00F7 | (i << 8)) if cat == 7 else (0xFFFF00F0 | cat | (i << 8))))
L = []
for b in range(0, len(items), 8):
    L.append('load arag')
    for j in range(8):
        L.append('poke %08X %08X' % (0x03003C5C + 4 * j, items[b + j][2] if b + j < len(items) else 0xFFFFFFFF))
    L += ['10 START', '40 -', 'dump 04000000 4', 'dump 07000000 400', 'dump 05000200 200', 'dump 06010000 8000']
open(os.path.join(work, 'cap.txt'), 'w').write('\n'.join(L) + '\n')
if os.path.exists(os.path.join(work, 'dump.bin')): os.remove(os.path.join(work, 'dump.bin'))
st = os.path.join(work, 'arag.state')
if os.path.abspath(state) != os.path.abspath(st): open(st, 'wb').write(open(state, 'rb').read())
subprocess.run([runner, rom, os.path.join(work, 'cap.txt'), work], check=True)
d = open(os.path.join(work, 'dump.bin'), 'rb').read(); S = 4 + 0x400 + 0x200 + 0x8000
SH = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
      (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}

def epx(a):
    h, w, _ = a.shape; P = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
    C = P[1:-1, 1:-1]; A = P[:-2, 1:-1]; B = P[1:-1, 2:]; Cl = P[1:-1, :-2]; D = P[2:, 1:-1]
    eq = lambda x, y: np.all(x == y, axis=2)
    o = np.zeros((h * 2, w * 2, 4), a.dtype)
    o[0::2, 0::2] = np.where((eq(Cl, A) & ~eq(Cl, D) & ~eq(A, B))[..., None], A, C)
    o[0::2, 1::2] = np.where((eq(A, B) & ~eq(A, Cl) & ~eq(B, D))[..., None], B, C)
    o[1::2, 0::2] = np.where((eq(D, Cl) & ~eq(D, B) & ~eq(Cl, A))[..., None], Cl, C)
    o[1::2, 1::2] = np.where((eq(B, D) & ~eq(B, A) & ~eq(D, Cl))[..., None], D, C)
    return o

W, H, COLS = 104, 80, 16
sheet = Image.new('RGBA', (COLS * W, ((len(items) + COLS - 1) // COLS) * H), (0, 0, 0, 0))
for b in range(len(d) // S):
    blk = d[b * S:(b + 1) * S]; oned = bool(struct.unpack('<H', blk[0:2])[0] & 0x40)
    oam, pal, vr = blk[4:0x404], blk[0x404:0x604], blk[0x604:]
    groups = {}
    for k in range(128):
        a0, a1, a2 = struct.unpack('<HHH', oam[k * 8:k * 8 + 6])
        pb = a2 >> 12
        if (a0 >> 8) & 3 == 2 or pb < 8 or b * 8 + pb - 8 >= len(items): continue
        groups.setdefault(pb, []).append((a0, a1, a2))
    for pb, es in groups.items():
        rects = []
        for a0, a1, a2 in es:
            w, h = SH[(a0 >> 14, a1 >> 14)]; x = a1 & 0x1FF; y = a0 & 0xFF
            rects.append((x - 512 if x >= 256 else x, y, w, h, a2 & 0x3FF, (a1 >> 12) & 1, (a1 >> 13) & 1))
        x0 = min(q[0] for q in rects); y0 = min(q[1] for q in rects)
        im = Image.new('RGBA', (max(q[0] + q[2] for q in rects) - x0, max(q[1] + q[3] for q in rects) - y0), (0, 0, 0, 0)); px = im.load()
        cols = [struct.unpack('<H', pal[(pb * 16 + c) * 2:(pb * 16 + c) * 2 + 2])[0] for c in range(16)]
        rgb = [((c & 31) * 255 // 31, ((c >> 5) & 31) * 255 // 31, ((c >> 10) & 31) * 255 // 31) for c in cols]
        for x, y, w, h, tile, hf, vf in rects:
            for ty in range(h // 8):
                for tx in range(w // 8):
                    t = tile + (ty * (w // 8) + tx if oned else ty * 32 + tx)
                    for yy in range(8):
                        for xx in range(8):
                            v = vr[t * 32 + yy * 4 + xx // 2]; v = (v >> 4) if xx & 1 else v & 15
                            if v:
                                X = w - 1 - (tx * 8 + xx) if hf else tx * 8 + xx
                                Y = h - 1 - (ty * 8 + yy) if vf else ty * 8 + yy
                                px[x - x0 + X, y - y0 + Y] = rgb[v] + (255,)
        n = b * 8 + pb - 8
        a = epx(epx(np.asarray(im.crop((2, 2, 28, 22)))))
        sheet.paste(Image.fromarray(a), ((n % COLS) * W, (n // COLS) * H))
sheet.save(out, optimize=True)
cnt = [0] * 15
for c, i, _ in items: cnt[c] += 1
print(len(items), 'items, per category', cnt, '->', out)
