#!/usr/bin/env python3
"""Bigger crossbow trap pictures (Jordan, 2026-11-20: "Make trap image a little larger").
Takes the 16 facings of tools/turn16/xb16.bin (16x16) and makes them 1.5x (24x24) with Scale3x then every second
pixel, inside a 32x32 sprite (16 tiles, 512 bytes a frame, same frame order). Also finds, per frame, the bolt tip
(palette colour 10) and the bow (colour 12) so the page can put a glow on them.
Writes xbbig.bin (8192 bytes) and xbbig.json ({tip: [[x, y]...], bow: [[x0, y0, x1, y1]...]} in sprite pixels,
origin = the 32x32 sprite's top left)."""
import json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
B = open(os.path.join(D, "..", "turn16", "xb16.bin"), "rb").read()
assert len(B) == 2048

def unpack(t, cells=2):
    n = cells * 8; img = [[0] * n for _ in range(n)]
    for ti in range(cells * cells):
        tx, ty = (ti % cells) * 8, (ti // cells) * 8
        for r in range(8):
            for c in range(4):
                v = t[ti * 32 + r * 4 + c]; img[ty + r][tx + 2 * c] = v & 15; img[ty + r][tx + 2 * c + 1] = v >> 4
    return img

def pack(img, cells=4):
    out = bytearray()
    for ti in range(cells * cells):
        tx, ty = (ti % cells) * 8, (ti // cells) * 8
        for r in range(8):
            for c in range(4): out.append(img[ty + r][tx + 2 * c] | img[ty + r][tx + 2 * c + 1] << 4)
    return bytes(out)

def scale3x(img):
    h, w = len(img), len(img[0]); o = [[0] * (3 * w) for _ in range(3 * h)]
    g = lambda x, y: img[y][x] if 0 <= x < w and 0 <= y < h else 0
    for y in range(h):
        for x in range(w):
            A, Bb, C = g(x - 1, y - 1), g(x, y - 1), g(x + 1, y - 1)
            Dd, E, F = g(x - 1, y), g(x, y), g(x + 1, y)
            G, H, I = g(x - 1, y + 1), g(x, y + 1), g(x + 1, y + 1)
            if Bb != H and Dd != F:
                e = [Dd if Dd == Bb else E,
                     Bb if (Dd == Bb and E != C) or (Bb == F and E != A) else E,
                     F if Bb == F else E,
                     Dd if (Dd == Bb and E != G) or (Dd == H and E != A) else E,
                     E,
                     F if (Bb == F and E != I) or (H == F and E != C) else E,
                     Dd if Dd == H else E,
                     H if (Dd == H and E != I) or (H == F and E != G) else E,
                     F if H == F else E]
            else:
                e = [E] * 9
            for k in range(9): o[3 * y + k // 3][3 * x + k % 3] = e[k]
    return o

frames, tips, bows = [], [], []
for n in range(16):
    src = unpack(B[n * 128:(n + 1) * 128])
    big = scale3x(src)                                   # 48x48
    small = [[big[2 * y + 1][2 * x + 1] for x in range(24)] for y in range(24)]
    # keep the outline whole: a colour pixel never touches the empty outside without an outline (colour 4) between
    out = [[0] * 32 for _ in range(32)]
    for y in range(24):
        for x in range(24): out[y + 8][x + 4] = small[y][x]
    o = [r[:] for r in out]
    for y in range(32):
        for x in range(32):
            if out[y][x] == 0 and any(0 <= x + dx < 32 and 0 <= y + dy < 32 and out[y + dy][x + dx] not in (0, 4)
                                      for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): o[y][x] = 4
    frames.append(o)
    tp = [(x, y) for y in range(32) for x in range(32) if o[y][x] == 10]
    bp = [(x, y) for y in range(32) for x in range(32) if o[y][x] == 12]
    tips.append([round(sum(p[0] for p in tp) / len(tp) + 0.5, 2), round(sum(p[1] for p in tp) / len(tp) + 0.5, 2)] if tp else None)
    if bp:
        a = max(((p, q) for p in bp for q in bp), key=lambda pq: (pq[0][0] - pq[1][0]) ** 2 + (pq[0][1] - pq[1][1]) ** 2)
        bows.append([a[0][0] + 0.5, a[0][1] + 0.5, a[1][0] + 0.5, a[1][1] + 0.5])
    else: bows.append(None)

data = b"".join(pack(f) for f in frames)
assert len(data) == 8192
open(os.path.join(D, "xbbig.bin"), "wb").write(data)
json.dump({"tip": tips, "bow": bows}, open(os.path.join(D, "xbbig.json"), "w"))
if os.environ.get("PREVIEW"):
    from PIL import Image, ImageDraw
    pal = {0: (40, 40, 60), 1: (255, 255, 255), 2: (200, 200, 210), 3: (150, 100, 50), 4: (30, 20, 10), 10: (120, 140, 160), 12: (90, 90, 100)}
    im = Image.new("RGB", (16 * 34, 32))
    for n, p in enumerate(frames):
        for y in range(32):
            for x in range(32): im.putpixel((n * 34 + x, y), pal.get(p[y][x], (255, 0, 255)))
    im = im.resize((im.width * 4, 128), Image.NEAREST); d = ImageDraw.Draw(im)
    for n in range(16):
        if bows[n]: b = bows[n]; d.line([(n * 136 + b[0] * 4, b[1] * 4), (n * 136 + b[2] * 4, b[3] * 4)], fill=(80, 160, 255))
        if tips[n]: t = tips[n]; d.ellipse([n * 136 + t[0] * 4 - 4, t[1] * 4 - 4, n * 136 + t[0] * 4 + 4, t[1] * 4 + 4], outline=(255, 255, 0))
    im.save(os.environ["PREVIEW"])
print("wrote xbbig.bin + xbbig.json")
