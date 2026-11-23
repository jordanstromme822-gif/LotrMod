"""List the props of the Isengard maps (2026-11-23): every small thing standing on plain ground in levels 50, 51, 55.

python3 tools/region/props_scan.py ROM OUT_DIR [CUTS.json]

A prop = a connected group (8 neighbours) of 8 px spots that are not plain ground (an upper-layer tile, a lower tile
that is not ground, or blocked), small enough to be a thing and not a wall (bbox <= 16 x 16 spots), with plain
ground all round it. Writes props.pkl (each prop: level, x, y, A/B/C grids, None = ground) and sheet.png (every
prop numbered, at 2x, on a dark backdrop) so props can be picked by number.
CUTS.json (optional): {"name": [level, x0, y0, x1, y1], ...} in 8 px spots (end excluded): bigger pieces cut by hand
(a stretch of paved road), kept the same way (only the spots that are not plain ground) and listed after the scanned
props with their name.
"""
import collections, json, os, pickle, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __file__.rsplit('/', 2)[0] + '/join')
from cells import load
from build import pix

rom, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
R_, lv, rgb, grids, pixels = load(rom, [50, 51, 55])

def grid8(L):
    g = grids[L]; h, w = len(g), len(g[0])
    A = [[None] * (w * 4) for _ in range(h * 4)]; B = [[None] * (w * 4) for _ in range(h * 4)]; C = [[0] * (w * 4) for _ in range(h * 4)]
    for y, row in enumerate(g):
        for x, c in enumerate(row):
            for k in range(16): A[y * 4 + k // 4][x * 4 + k % 4] = c[0][k]; B[y * 4 + k // 4][x * 4 + k % 4] = c[1][k]; C[y * 4 + k // 4][x * 4 + k % 4] = c[2][k]
    return A, B, C
G8 = {L: grid8(L) for L in (50, 51, 55)}
gc = collections.Counter()
for L, (a, b, c) in G8.items():
    for y in range(len(a)):
        for x in range(len(a[0])):
            if b[y][x][0] == 0 and c[y][x] == 0: gc[a[y][x]] += 1
GROUND = {k for k, n in gc.items() if n >= 6}

def tile_rgb(t):
    p = pix(pixels[t[0]])
    if t[1] & 0x400: p = p[:, ::-1]
    if t[1] & 0x800: p = p[::-1]
    return rgb[(t[1] >> 12) * 16 + p], p != 0

props = []
for L, (a, b, c) in G8.items():
    h, w = len(a), len(a[0])
    odd = np.array([[b[y][x][0] != 0 or a[y][x] not in GROUND or (c[y][x] & 7) != 0 for x in range(w)] for y in range(h)])
    seen = np.zeros_like(odd)
    for y0 in range(h):
        for x0 in range(w):
            if not odd[y0, x0] or seen[y0, x0]: continue
            st = [(y0, x0)]; seen[y0, x0] = True; comp = []
            while st:
                y, x = st.pop(); comp.append((y, x))
                if len(comp) > 400: break
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        q = (y + dy, x + dx)
                        if 0 <= q[0] < h and 0 <= q[1] < w and odd[q] and not seen[q]: seen[q] = True; st.append(q)
            if len(comp) > 400 or len(comp) < 2: continue
            ys = [p[0] for p in comp]; xs = [p[1] for p in comp]
            y1, y2, x1, x2 = min(ys), max(ys), min(xs), max(xs)
            if y2 - y1 >= 16 or x2 - x1 >= 16 or y1 == 0 or x1 == 0 or y2 >= h - 1 or x2 >= w - 1: continue
            cs = set(comp)
            pa = [[a[y][x] if (y, x) in cs else None for x in range(x1, x2 + 1)] for y in range(y1, y2 + 1)]
            pb = [[b[y][x] if (y, x) in cs else (0, 0) for x in range(x1, x2 + 1)] for y in range(y1, y2 + 1)]
            pc = [[c[y][x] if (y, x) in cs else None for x in range(x1, x2 + 1)] for y in range(y1, y2 + 1)]
            props.append(dict(level=L, x=x1, y=y1, A=pa, B=pb, C=pc, n=len(comp)))
for name, (L, x0, y0, x1, y1, *how) in (json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}).items():
    a, b, c = G8[L]                                   # how 'all': keep every spot (paving counts as ground otherwise)
    odd = (lambda y, x: True) if how == ['all'] else (lambda y, x: b[y][x][0] != 0 or a[y][x] not in GROUND or (c[y][x] & 7) != 0)
    props.append(dict(level=L, x=x0, y=y0, name=name, n=-1,
                      A=[[a[y][x] if odd(y, x) else None for x in range(x0, x1)] for y in range(y0, y1)],
                      B=[[b[y][x] if odd(y, x) else (0, 0) for x in range(x0, x1)] for y in range(y0, y1)],
                      C=[[c[y][x] if odd(y, x) else None for x in range(x0, x1)] for y in range(y0, y1)]))
# a prop whose lower layer has see-through pixels shows the backdrop colour (bright blue) through them off its map
for p in props:
    p['tmask'] = [[a is not None and bool((pix(pixels[a[0]]) == 0).any()) for a in r] for r in p['A']]
    p['transp'] = any(any(r) for r in p['tmask'])
# drop exact duplicates (same tiles), keep the first
uniq, keys = [], set()
for p in props:
    k = (str(p['A']), str(p['B']))
    if k in keys: continue
    keys.add(k); uniq.append(p)
props = uniq
print('props', len(props))
pickle.dump(props, open(os.path.join(out, 'props.pkl'), 'wb'))

# contact sheet
CW = max(17, max(max(len(p['A']), len(p['A'][0])) for p in props)) * 8 * 2; COLS = 10
rows = (len(props) + COLS - 1) // COLS
sheet = Image.new('RGB', (COLS * CW, rows * (CW + 14)), (24, 24, 28))
d = ImageDraw.Draw(sheet)
for i, p in enumerate(props):
    hh, ww = len(p['A']), len(p['A'][0])
    img = np.zeros((hh * 8, ww * 8, 3), np.int32) + (90, 84, 80)
    for y in range(hh):
        for x in range(ww):
            if p['A'][y][x] is not None:
                col, m = tile_rgb(p['A'][y][x]); s = img[y * 8:y * 8 + 8, x * 8:x * 8 + 8]; s[m] = col[m]
            if p['B'][y][x][0] != 0:
                col, m = tile_rgb(p['B'][y][x]); s = img[y * 8:y * 8 + 8, x * 8:x * 8 + 8]; s[m] = col[m]
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((ww * 16, hh * 16), Image.NEAREST)
    X, Y = (i % COLS) * CW, (i // COLS) * (CW + 14)
    sheet.paste(im, (X + 2, Y + 14))
    d.text((X + 2, Y + 1), '%s L%d %dx%d' % (p.get('name', i), p['level'], ww, hh), fill=(240, 220, 150))
sheet.save(os.path.join(out, 'sheet.png'))
