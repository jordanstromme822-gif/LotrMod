import sys, numpy as np
sys.path.insert(0, '../siege')
from romlib import Rom
from build import Level, BLANK, merge_tiles, render, pix
from PIL import Image
S = '/tmp/claude-0/-home-user/92561353-ae0d-5ace-8f1f-fd624dcc7570/scratchpad'
R = Rom(S + '/orig.gba')
a, b = Level(R, 51), Level(R, 55)
P = np.frombuffer(R.rom[a.e[15] - 0x08000000:][:0x200], dtype='<u2')
rgb = np.stack([(P & 31) << 3, ((P >> 5) & 31) << 3, ((P >> 10) & 31) << 3], 1).astype(np.int32)
W, H = 144, 4 * (20 + 40)
GA = [[(BLANK, 0)] * W for _ in range(H)]; GB = [[(BLANK, 0)] * W for _ in range(H)]
for L, ox, oy in ((b, 28, 0), (a, 0, 80)):
    A_, B_ = L.tilegrid(0), L.tilegrid(1)
    for y in range(len(A_)):
        for x in range(len(A_[0])):
            GA[oy + y][ox + x] = A_[y][x]; GB[oy + y][ox + x] = B_[y][x]
need = sorted({t[0] for G in (GA, GB) for r in G for t in r})
pixels = dict(zip(need, R.tiles(a.tileset, need)))
before = render(GA, GB, pixels, rgb, 0, 0, W, H)
mB, eB = merge_tiles(GB, pixels, rgb, 500)
mA, eA = merge_tiles(GA, pixels, rgb, 1020)
print('merged A', len(mA), eA, 'B', len(mB), eB)
for G, m in ((GA, mA), (GB, mB)):
    for y in range(H):
        for x in range(W):
            t = G[y][x]
            if t[0] in m: nt, fb = m[t[0]]; G[y][x] = (nt, t[1] ^ fb)
after = render(GA, GB, pixels, rgb, 0, 0, W, H)
d = np.abs(before - after).sum(2)
print('changed px', (d > 30).mean())
Image.fromarray(np.concatenate([before, after], 1).clip(0, 255).astype(np.uint8)).save(S + '/j_merge.png')
