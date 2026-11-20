#!/usr/bin/env python3
"""Frodo's crossbow trap, redrawn (Jordan, 2026-11-20: "Make trap look nicer", reference picture: an ornate bronze
ballista on a pedestal with splayed feet, glowing leaf engravings and a white arrowhead).

A small 3D model drawn in 16 facings (22.5 degrees apart on the ground, 0 = up, clockwise) into 32x32 sprites in the
game's OBJ palette 3 (the same in every level):
  1 tan  2 light wood  3 dark wood  4 outline  5-8 bronze (light to dark)  9 white  10-12 steel greys  13 gold
The base (pedestal, four splayed legs with steel feet, gold leaf on the front) stays still; the head (bronze stock
with a gold inlay, recurve bow, steel lock, string and a bolt with a white head) turns. Drawn at 4x with a depth
buffer, then each pixel takes the colour most of its samples have; outlined in colour 4.
Writes xbbig.bin (16 frames x 512 bytes, frame order: facings 0, 2, .. 14 then 1, 3, .. 15) and xbbig.json (bolt tip
and the two string ends per frame, in sprite pixels) for the page's glow. PREVIEW=file.png draws them in order.
FACINGS=32 (v206, Jordan 2026-11-20: "Give the trap turn 32 steps of animation") draws 32 facings, 11.25 degrees apart,
into xb32.bin (32 x 512 bytes) + xb32.json; frame order: the 8 main ways (facings 0, 4, .. 28), then 2, 6, .. 30, then
the odd ones, so frames 0-7 are still the 8 ways the game's own code picks.
Our own art (no game pixels), so it lives in the repo."""
import json, math, os
D = os.path.dirname(os.path.abspath(__file__))
S = 4                       # supersampling
W = 32 * S
OX, OY = 16, 27             # sprite pixel of the object's ground point
PAL = {0: (0, 0, 0), 1: (232, 184, 104), 2: (192, 152, 88), 3: (128, 104, 48), 4: (64, 40, 24), 5: (248, 168, 40),
       6: (216, 144, 48), 7: (176, 112, 32), 8: (136, 80, 16), 9: (240, 240, 240), 10: (184, 184, 176),
       11: (144, 144, 144), 12: (104, 96, 96), 13: (248, 192, 0)}

def proj(X, Y, Z):          # ground X right, Y away from the viewer, Z up -> sprite pixel, depth (bigger = nearer)
    return OX + X, OY - 0.5 * Y - Z, -0.866 * Y + 0.5 * Z

class Canvas:
    def __init__(self):
        self.c = [[0] * W for _ in range(W)]; self.z = [[-1e9] * W for _ in range(W)]
    def dot(self, X, Y, Z, col, bias=0.0):
        sx, sy, d = proj(X, Y, Z)
        x, y = int(sx * S), int(sy * S)
        if 0 <= x < W and 0 <= y < W and d + bias >= self.z[y][x]:
            self.z[y][x] = d + bias; self.c[y][x] = col
    def box(self, p, u, v, w, a, b, c, col, shade=None, bias=0.0):
        """a box at p spanning a*u, b*v, c*w (u, v, w unit vectors); shade(i, j, k) -> colour for the face point"""
        n = lambda L: max(1, int(abs(L) * S * 1.6))
        na, nb, nc = n(a), n(b), n(c)
        for i in range(na + 1):
            for j in range(nb + 1):
                for k in range(nc + 1):
                    if 0 < i < na and 0 < j < nb and 0 < k < nc: continue      # surface only
                    ta, tb, tc = i / na, j / nb, k / nc
                    q = [p[m] + u[m] * a * ta + v[m] * b * tb + w[m] * c * tc for m in range(3)]
                    self.dot(*q, shade(ta, tb, tc) if shade else col, bias)
    def line(self, p0, p1, r, col, bias=0.0):
        L = math.dist(p0, p1); n = max(2, int(L * S * 2))
        for i in range(n + 1):
            t = i / n; q = [p0[m] + (p1[m] - p0[m]) * t for m in range(3)]
            for dx in (-r, 0, r):
                for dz in (-r, 0, r):
                    self.dot(q[0] + dx, q[1], q[2] + dz, col, bias)

def draw(theta):
    cv = Canvas()
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    # ---- base: pedestal + four splayed legs ----
    def ped_shade(ta, tb, tc, lo=False):
        if tb == 0:                                   # front face: bronze, light from the left, a gold leaf
            lx, lz = ta - 0.5, (tc - 0.5) if not lo else -1
            wl = 0.2 * math.sin(math.pi * min(1, max(0, (lz + 0.45) / 0.9)))
            if abs(lx) < wl and abs(lz) < 0.45: return 13
            return 6 if ta < 0.2 else 8 if ta > 0.85 else 7
        if ta == 0: return 6
        if ta == 1: return 8
        return 5 if tc == 1 else 7
    cv.box((-3.5, -2.8, 0), X, Y, Z, 7, 5.6, 2.2, 7, lambda a, b, c: ped_shade(a, b, c, True))
    cv.box((-2.3, -2, 2.2), X, Y, Z, 4.6, 4, 7.4, 7, ped_shade)
    for fx, fy in ((-9, -4), (9, -4), (-7, 5), (7, 5)):
        top = (fx * 0.2, fy * 0.25, 5.0)
        foot = (fx, fy, 0.6)
        cv.line(top, foot, 0.5, 8 if fx > 0 else 7)
        cv.line((top[0], top[1], top[2] + 0.55), (foot[0], foot[1], foot[2] + 0.55), 0.2, 6 if fx < 0 else 7, 0.01)   # lit edge
        cv.box((foot[0] - 1, foot[1] - 1, 0), X, Y, Z, 2, 2, 1.6, 11, lambda a, b, c: 10 if c == 1 else 12)
        cv.dot(foot[0], foot[1], 2.2, 10)
    # ---- head: turns with theta (0 = away from the viewer, clockwise) ----
    d = (math.sin(theta), math.cos(theta), 0.0); pr = (math.cos(theta), -math.sin(theta), 0.0)
    H = 10.0
    at = lambda a, b, z: (d[0] * a + pr[0] * b, d[1] * a + pr[1] * b, z)
    def stock_shade(ta, tb, tc):
        if tc == 1:                                   # top: bronze with a gold inlay line down the middle
            return 13 if abs(tb - 0.5) < 0.18 and 0.15 < ta < 0.7 else 7
        return 8
    cv.box(at(-7, -1.6, H), d, pr, Z, 15, 3.2, 2.2, 6, stock_shade)
    cv.box(at(-1.5, -2.2, H + 1.5), d, pr, Z, 3.5, 4.4, 2.2, 10, lambda a, b, c: 10 if c == 1 else (11 if b < 0.5 else 12))   # steel lock
    # recurve bow: bends back from the middle, tips curl forward
    pts = []
    for i in range(-24, 25):
        t = i / 24; ax = 5.5 - 3.2 * t * t + (1.4 * max(0, abs(t) - 0.8) / 0.2) ** 2 * 0.6
        pts.append(at(ax, 12.5 * t, H + 1.6))
    for a, b in zip(pts, pts[1:]): cv.line(a, b, 0.45, 6)
    for a, b in zip(pts, pts[1:]): cv.line((a[0], a[1], a[2] + 0.5), (b[0], b[1], b[2] + 0.5), 0.2, 5, 0.02)
    for tip in (pts[0], pts[-1]): cv.line(tip, (tip[0], tip[1], tip[2] + 0.8), 0.4, 13, 0.05)
    s0, s1, nock = pts[2], pts[-3], at(-3.5, 0, H + 2.4)
    cv.line(s0, nock, 0.2, 10, 0.03); cv.line(s1, nock, 0.2, 10, 0.03)
    # bolt + white head
    cv.line(at(-4.5, 0, H + 2.6), at(10.5, 0, H + 2.6), 0.3, 2, 0.04)
    for k in range(5):
        w = 1.4 * (1 - k / 5)
        cv.line(at(10.5 + k * 0.5, -w, H + 2.6), at(10.5 + k * 0.5, w, H + 2.6), 0.25, 9, 0.06)
    tip = proj(*at(13.2, 0, H + 2.6)); a0 = proj(*s0); a1 = proj(*s1); nk = proj(*nock)
    return cv, (tip[0], tip[1]), (a0[0], a0[1], nk[0], nk[1], a1[0], a1[1])

def down(cv):
    img = [[0] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            cnt = {}
            for yy in range(S):
                for xx in range(S):
                    c = cv.c[y * S + yy][x * S + xx]
                    cnt[c] = cnt.get(c, 0) + 1
            filled = S * S - cnt.get(0, 0)
            if filled >= S * S * 0.34:
                cnt.pop(0, None)
                # keep small bright details (gold, white) if they cover a quarter of the pixel
                for hot in (9, 13):
                    if cnt.get(hot, 0) >= S * S * 0.25: img[y][x] = hot; break
                else: img[y][x] = max(cnt, key=cnt.get)
    o = [r[:] for r in img]
    for y in range(32):
        for x in range(32):
            if img[y][x] == 0 and any(0 <= x + dx < 32 and 0 <= y + dy < 32 and img[y + dy][x + dx] not in (0, 4)
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): o[y][x] = 4
    return o

def pack(img):
    out = bytearray()
    for ti in range(16):
        tx, ty = (ti % 4) * 8, (ti // 4) * 8
        for r in range(8):
            for c in range(4): out.append(img[ty + r][tx + 2 * c] | img[ty + r][tx + 2 * c + 1] << 4)
    return bytes(out)

N = int(os.environ.get("FACINGS", "16")); assert N in (16, 32)
st8 = N // 8
order = [f for lv in (st8, st8 // 2, 1) if lv for f in range(N) if f % lv == 0 and (lv == st8 or f % (2 * lv))]
order = list(dict.fromkeys(order)); assert len(order) == N   # frame k shows facing order[k]
pics, tips, strings = {}, {}, {}
for f in range(N):
    cv, tp, st = draw(math.radians(360 / N * f))
    pics[f] = down(cv); tips[f] = [round(tp[0], 2), round(tp[1], 2)]; strings[f] = [round(v, 2) for v in st]
data = b"".join(pack(pics[f]) for f in order)
assert len(data) == 512 * N
OUT = "xbbig" if N == 16 else "xb32"
open(os.path.join(D, OUT + ".bin"), "wb").write(data)
json.dump({"tip": [tips[f] for f in order], "bow": [strings[f] for f in order]}, open(os.path.join(D, OUT + ".json"), "w"))
if os.environ.get("PREVIEW"):
    from PIL import Image
    im = Image.new("RGB", (N * 34, 34), (70, 80, 90))
    for n in range(N):
        for y in range(32):
            for x in range(32):
                c = pics[n][y][x]
                if c: im.putpixel((n * 34 + x + 1, y + 1), PAL[c])
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(os.environ["PREVIEW"])
print("wrote xbbig.bin + xbbig.json (redrawn ballista)")
