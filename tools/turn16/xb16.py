#!/usr/bin/env python3
"""Frodo's crossbow in 16 directions (Jordan, 2026-11-11: smooth 360-degree turning, like Frodo's walk).
Keeps the 8 hand-drawn facings of tools/orcslots/xbgfx.c (v125) as the even facings and makes each odd one from a neighbour:
the head (rows 0-10) is scaled up 8x with Scale2x, turned 22.5 degrees on the ground (the picture's y is squashed
0.62 for the game's 2:1 view, so it turns in that space), sampled back to 16x16, put on the tripod and outlined
again. The left side is the right side mirrored.
Writes xb16.bin (2048 bytes, ROM 0x94400, freed German text bank): 16 pictures of 4 tiles, the 8 old facings first
(frames 0-7, so the crossbow code's own 8-way pick still shows the right picture), then facings 1, 3, ... 15
(frames 8-15). turn16.c's crossbow anim set points at it. Our own pixel art, so it can live in the repo.
Usage: xb16.py   (PREVIEW=file.png also draws the 16 facings in turning order)"""
import math, os, re, sys
D = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(D, "..", "orcslots", "xbgfx.c")
src = open(PATH).read()
B = bytes(int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{2})", src.split("{", 1)[1]))
assert len(B) == 1024

def unpack(t):
    img = [[0] * 16 for _ in range(16)]
    for ti in range(4):
        tx, ty = (ti % 2) * 8, (ti // 2) * 8
        for r in range(8):
            for c in range(4):
                v = t[ti * 32 + r * 4 + c]; img[ty + r][tx + 2 * c] = v & 15; img[ty + r][tx + 2 * c + 1] = v >> 4
    return img

def pack(img):
    out = bytearray()
    for ti in range(4):
        tx, ty = (ti % 2) * 8, (ti // 2) * 8
        for r in range(8):
            for c in range(4): out.append(img[ty + r][tx + 2 * c] | img[ty + r][tx + 2 * c + 1] << 4)
    return bytes(out)

def scale2x(img):
    h, w = len(img), len(img[0]); o = [[0] * (2 * w) for _ in range(2 * h)]
    g = lambda x, y: img[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]
    for y in range(h):
        for x in range(w):
            P, A, Bb, C, Dd = g(x, y), g(x, y - 1), g(x + 1, y), g(x - 1, y), g(x, y + 1)
            e0 = A if C == A and C != Dd and A != Bb else P
            e1 = Bb if A == Bb and A != C and Bb != Dd else P
            e2 = C if Dd == C and Dd != Bb and C != A else P
            e3 = Dd if Bb == Dd and Bb != A and Dd != C else P
            o[2 * y][2 * x], o[2 * y][2 * x + 1], o[2 * y + 1][2 * x], o[2 * y + 1][2 * x + 1] = e0, e1, e2, e3
    return o

def head(img): return [[img[y][x] if y <= 10 else 0 for x in range(16)] for y in range(16)]

def rotate(img, deg, px=8.0, py=6.0, fs=0.62):
    big = img
    for _ in range(3): big = scale2x(big)
    th = math.radians(deg); c, s = math.cos(th), math.sin(th); out = [[0] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            X, Y = x + 0.5 - px, (y + 0.5 - py) / fs
            sx, sy = c * X + s * Y + px, (-s * X + c * Y) * fs + py
            bx, by = int(math.floor(sx * 8)), int(math.floor(sy * 8))
            if 0 <= bx < 128 and 0 <= by < 128: out[y][x] = big[by][bx]
    return out

def finish(hd, base):
    out = [[base[y][x] if y >= 9 else 0 for x in range(16)] for y in range(16)]
    for y in range(16):
        for x in range(16):
            if hd[y][x]: out[y][x] = hd[y][x]
    o = [r[:] for r in out]
    for y in range(16):          # empty next to a coloured pixel -> outline (colour 4)
        for x in range(16):
            if out[y][x] == 0 and any(0 <= x + dx < 16 and 0 <= y + dy < 16 and out[y + dy][x + dx] not in (0, 4)
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): o[y][x] = 4
    for y in range(16):          # outline pixels touching no colour go
        for x in range(16):
            if o[y][x] == 4 and not any(0 <= x + dx < 16 and 0 <= y + dy < 16 and o[y + dy][x + dx] not in (0, 4)
                                        for dx in (-1, 0, 1) for dy in (-1, 0, 1)): o[y][x] = 0
    return o

fr = [unpack(B[n * 128:(n + 1) * 128]) for n in range(8)]
# which neighbour each in-between is made from (picked by eye: the one that keeps the bolt and bow readable)
odd = {1: finish(rotate(head(fr[1]), -22.5), fr[0]), 3: finish(rotate(head(fr[2]), -22.5), fr[0]),
       5: finish(rotate(head(fr[2]), 22.5), fr[0]), 7: finish(rotate(head(fr[4]), -22.5), fr[0])}
out = [fr[n // 2] if n % 2 == 0 else odd[n] if n < 8 else [r[::-1] for r in odd[16 - n]] for n in range(16)]
order = list(range(0, 16, 2)) + list(range(1, 16, 2))   # frame k shows facing order[k]
data = b"".join(pack(out[f]) for f in order)
assert data[:1024] == B
open(os.path.join(D, "xb16.bin"), "wb").write(data)
if os.environ.get("PREVIEW"):
    from PIL import Image
    pal = {0: (40, 40, 60), 1: (255, 255, 255), 2: (200, 200, 210), 3: (150, 100, 50), 4: (30, 20, 10), 10: (120, 140, 160), 12: (90, 90, 100)}
    im = Image.new("RGB", (16 * 18, 16))
    for n, p in enumerate(out):
        for y in range(16):
            for x in range(16): im.putpixel((n * 18 + x, y), pal[p[y][x]])
    im.resize((im.width * 6, 96), Image.NEAREST).save(os.environ["PREVIEW"])
print("wrote xb16.bin (16 facings)")
