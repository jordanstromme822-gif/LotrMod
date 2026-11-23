"""Orthanc's top as the book describes it (Jordan 2026-11-23: "It should be drawn like the book describes it").

python3 tools/region/orthanc/book.py SHAPE.png COMP.npz OUT.png

"Four mighty piers of many-sided stone were welded into one, but near the summit they opened into gaping horns, their
pinnacles sharp as the points of spears, keen-edged as knives. Between them was a narrow space, and there upon a floor of
polished stone, written with strange signs, a man might stand five hundred feet above the plain." (The Two Towers)
"black and gleaming hard" (The Road to Isengard).

Keeps the outline of the earlier horns (SHAPE.png alpha: outward-curving horns from one shaft), its ledge along the
bottom (where the layer meets the tower in the map) and the high window cut from the game's own tower tiles (COMP.npz,
as compose.py), and repaints the stone: four round, many-sided piers (8 sides) welded into one shaft and opening into the
horns, smooth black stone in the game tower's own dark greys, light from the upper left, glints on the knife edges, and a
floor of polished stone with carved signs in the space between the inner horns.
"""
import sys
import numpy as np
from PIL import Image
src, comp, out = sys.argv[1:4]
S = np.asarray(Image.open(src)).astype(np.float32)
A = S[..., 3] > 0
H, W = A.shape
rng = np.random.default_rng(11)
RAMP = np.array([[5, 6, 10], [14, 15, 21], [26, 27, 35], [42, 43, 53], [62, 62, 74], [92, 92, 106], [130, 130, 146]], np.float32)
def ramp(t):
    t = np.clip(np.asarray(t, np.float32), 0, 1) * (len(RAMP) - 1); i = np.minimum(t.astype(int), len(RAMP) - 2); f = (t - i)[..., None]
    return RAMP[i] * (1 - f) + RAMP[i + 1] * f
def runs(y):
    xs = np.nonzero(A[y])[0]
    return [(r[0], r[-1] + 1) for r in np.split(xs, np.nonzero(np.diff(xs) != 1)[0] + 1)] if len(xs) else []
# the four piers' axes and half widths, fitted where the horns stand apart
ys, cs, ws = [], [[] for _ in range(4)], [[] for _ in range(4)]
for y in range(H):
    r = runs(y)
    if len(r) == 4:
        ys.append(y)
        for p, (a, b) in enumerate(r): cs[p].append((a + b) / 2); ws[p].append((b - a) / 2)
ys = np.array(ys)
fc = [np.polyfit(ys, c, 2) for c in cs]; fw = [np.polyfit(ys, w, 2) for w in ws]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
C = np.stack([np.polyval(f, yy) for f in fc]); HW = np.stack([np.maximum(3, np.polyval(f, yy)) for f in fw])
D = np.abs(xx[None] - C) / HW
P = np.argmin(D, 0)                                   # which pier each pixel belongs to
u = np.take_along_axis((xx[None] - C) / HW, P[None], 0)[0]
u = np.clip(u, -0.999, 0.999)
SIDES = 8                                              # many-sided: an eight-sided pier shows four faces
th = np.arcsin(u)                                      # angle round the pier, -pi/2 (left) .. pi/2 (right)
k = np.floor((th + np.pi / 2) / (np.pi / (SIDES / 2)))
thq = -np.pi / 2 + (k + 0.5) * (np.pi / (SIDES / 2))
lit = 0.38 - 0.36 * np.sin(thq) + 0.05 * (1 - yy / H)  # light from the upper left, a little sky sheen higher up
# facet seams (a darker hairline where two faces meet) and welds between piers (dark grooves)
fpos = (th + np.pi / 2) / (np.pi / (SIDES / 2)) - k
wpx = HW.min(0) * np.cos(th) * (np.pi / (SIDES / 2))  # facet width in px, for a 1 px seam
seam = (1 - fpos) * np.take_along_axis(HW, P[None], 0)[0] * np.cos(th) * (np.pi / (SIDES / 2)) < 1.0
lit = np.where(seam, lit - 0.14, lit)
Dsort = np.sort(D, 0); weld = (Dsort[1] - Dsort[0]) < 0.06
lit = np.where(weld, 0.06, lit)
col = ramp(lit)
# knife edges: a cold glint along the left (lit) outline of every horn, dark on the right outline
L = A & ~np.roll(A, 1, 1); R = A & ~np.roll(A, -1, 1); T = A & ~np.roll(A, 1, 0)
L2 = A & ~np.roll(A, 2, 1) & ~L
col[L] = ramp(0.95); col[L2] = np.maximum(col[L2], ramp(0.72)); col[R] = ramp(0.04)
col[T & ~L] = ramp(0.8)
img = np.zeros((H, W, 4), np.float32); img[..., :3] = col; img[..., 3] = A * 255
# the floor of polished stone with strange signs: the bottom of the space between the inner horns
gx0, gx1 = int(np.polyval(fc[1], H - 1)), int(np.polyval(fc[2], H - 1))
gap_rows = [y for y in range(H) if any(gx0 < x < gx1 and not A[y, x] for x in range(gx0, gx1))]
yb = max(gap_rows) + 1                                 # where the inner horns meet
# the narrow space: the inner horns part a little more above the floor, so it can be seen between them
OPEN, DEPTH = 36, 90
gc = (np.polyval(fc[1], yb) + np.polyval(fc[2], yb)) / 2
yb += 16                                               # the floor sits a little lower, in the welded shaft's top
for y in range(yb - DEPTH, yb):
    half = OPEN / 2 * (1 - 0.25 * max(0.0, 1 - (y - (yb - DEPTH)) / 40.0))   # a narrow, round-bottomed U
    if yb - y < 6: half -= (6 - (yb - y)) ** 2 / 9.0
    for x in range(int(gc - half), int(gc + half) + 1): A[y, x] = False
img[~A] = 0
L = A & ~np.roll(A, 1, 1); R = A & ~np.roll(A, -1, 1)
img[L & (yy >= yb - DEPTH) & (yy < yb), :3] = ramp(0.04); img[R & (yy >= yb - DEPTH) & (yy < yb), :3] = ramp(0.9)
gx0, gx1 = int(gc - OPEN), int(gc + OPEN)
FH = 14                                                 # the floor shows in the open space just above where they meet
for y in range(yb - FH, yb):
    t = (yb - 1 - y) / FH                                # 0 at the front edge, 1 at the back
    for x in range(gx0, gx1):
        if A[y, x]: continue
        img[y, x, :3] = ramp(0.16 + 0.2 * (1 - t) * (1 - abs(x - (gx0 + gx1) / 2) / ((gx1 - gx0) / 2)))   # polished sheen
        img[y, x, 3] = 255
    row = [x for x in range(gx0, gx1) if not A[y, x]]
    if y == yb - 1 and row: img[y, row[0]:row[-1] + 1, :3] = ramp(0.55)   # the floor's front edge
    if y == yb - FH and row: img[y, row[0]:row[-1] + 1, :3] = ramp(0.08)  # its back edge, in the horns' shadow
GLYPHS = [[(0, 0), (0, 1), (0, 2), (1, 1)], [(0, 0), (1, 1), (2, 2), (0, 2)], [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 0), (2, 1), (1, 2)], [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)], [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)]]
for row in (yb - FH + 3, yb - FH + 8):
    xs = [x for x in range(gx0, gx1) if not A[row, x] and not A[row + 2, x] and not A[row, x - 2] and not A[row, x + 4]]
    if not xs: continue
    x = xs[0] + int(rng.integers(1, 3))
    while x < xs[-1] - 3:
        if all(x + d in xs for d in range(3)):
            for dx, dy in GLYPHS[int(rng.integers(0, len(GLYPHS)))]:
                img[row + dy, x + dx, :3] = ramp(0.5)
        x += 5 + int(rng.integers(0, 3))
# the ledge along the bottom (as on the map) and the high window, both from the earlier picture
img[H - 8:, :, :] = S[H - 8:]
c = np.load(comp); CI, CP, rgb = c['CI'], c['CP'], c['rgb']; P8 = rgb[128:144].astype(np.float32)
arch = CI[50:90, 371:405]; ap = CP[50:90, 371:405]
y_, x_ = np.mgrid[0:40, 0:34]; m = ((x_ - 16.5) / 17.5) ** 2 + ((y_ - 17) / 17.5) ** 2 <= 1; m |= (y_ >= 17) & (y_ < 38)
m &= (ap == 8) & (arch > 0)
cx, cy = (278 - 236) * 8 + 4 - 17, H - 60
img[cy:cy + 40, cx:cx + 34, :3] = np.where(m[..., None], P8[arch], img[cy:cy + 40, cx:cx + 34, :3])
Image.fromarray(img.clip(0, 255).astype(np.uint8), 'RGBA').save(out)
print('ok', out, 'floor row', yb, 'gap', gx0, gx1)
