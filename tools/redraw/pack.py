"""Pack 2x hand redraws into the crisp-skin atlas.

Each game tile is authored at 16x16 (two pixels for each GBA pixel). This file
nearest-doubles that to the 32x32 cell the Play Room already samples (cell 36,
2 px edge pad, same map.json as tools/skin/cut.py). No filtered scale.

Keys are the strings in map.json. A real pack uses the FNV-1a key cut.py writes
(`%08x%08x%d` of tile bytes, palette-bank bytes, and the 8bpp flag). Stand-in
keys start with "standin:" and do not match the game until they are replaced.
"""
import json, os
from .png import write_rgba
from .gba import limit, nearest, rgb555

CELL, PAD, BODY = 36, 2, 32

def grid_rgba(rows, palette):
    if not rows or any(len(r) != len(rows[0]) for r in rows):
        raise ValueError("grid is not rectangular")
    pal = {k: rgb555(v) for k, v in palette.items() if v is not None}
    used = []
    for row in rows:
        for ch in row:
            if ch == "." or ch not in palette or palette[ch] is None:
                continue
            c = rgb555(palette[ch])
            if c not in used:
                used.append(c)
    kept = limit(used, 15)
    h, w = len(rows), len(rows[0])
    out = bytearray(w * h * 4)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "." or ch not in palette or palette[ch] is None:
                continue
            r, g, b = nearest(palette[ch], kept)
            i = (y * w + x) * 4
            out[i:i + 4] = bytes((r, g, b, 255))
    return w, h, out, kept

def _nn2(w, h, rgba):
    out = bytearray(w * 2 * h * 2 * 4)
    W = w * 2
    for y in range(h):
        for x in range(w):
            px = rgba[(y * w + x) * 4:(y * w + x) * 4 + 4]
            for dy in (0, 1):
                for dx in (0, 1):
                    i = ((y * 2 + dy) * W + (x * 2 + dx)) * 4
                    out[i:i + 4] = px
    return out

def _fit32(w, h, rgba):
    if (w, h) == (16, 16):
        return _nn2(w, h, rgba)
    if (w, h) == (32, 32):
        return rgba
    raise ValueError("tile must be 16x16 (2x) or 32x32")

def _normals(body):
    """Edge normals, +Y up, packed 0.5 = 0. Empty texels stay alpha 0 so lighting falls back."""
    w = h = BODY
    out = bytearray(w * h * 4)
    def A(x, y):
        if x < 0 or y < 0 or x >= w or y >= h:
            return 0
        return 1 if body[(y * w + x) * 4 + 3] >= 128 else 0
    for y in range(h):
        for x in range(w):
            if not A(x, y):
                continue
            dhx = A(x + 1, y) - A(x - 1, y)
            dhy_up = A(x, y - 1) - A(x, y + 1)
            nx, ny = -dhx * 0.45, -dhy_up * 0.45
            nz = 1.0
            L = (nx * nx + ny * ny + nz * nz) ** 0.5
            nx, ny, nz = nx / L, ny / L, nz / L
            i = (y * w + x) * 4
            out[i] = int((nx * 0.5 + 0.5) * 255 + 0.5)
            out[i + 1] = int((ny * 0.5 + 0.5) * 255 + 0.5)
            out[i + 2] = int((nz * 0.5 + 0.5) * 255 + 0.5)
            out[i + 3] = 255
    return out

def _cell(body):
    """32x32 content plus a 2 px edge pad. Pad copies the edge texel (nearest), not a blur."""
    s = CELL
    out = bytearray(s * s * 4)
    def at(buf, x, y):
        x = 0 if x < 0 else BODY - 1 if x >= BODY else x
        y = 0 if y < 0 else BODY - 1 if y >= BODY else y
        i = (y * BODY + x) * 4
        return buf[i:i + 4]
    for y in range(s):
        for x in range(s):
            out[(y * s + x) * 4:(y * s + x) * 4 + 4] = at(body, x - PAD, y - PAD)
    return out

def pack(tiles, outdir, per=16):
    """tiles: list of dicts key, rgba (w,h,bytes), name, frame. Writes atlas, normals, map, catalog."""
    tiles = sorted(tiles, key=lambda t: t["key"])
    keys = [t["key"] for t in tiles]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate key")
    rows = (len(tiles) + per - 1) // per
    W, H = per * CELL, rows * CELL
    atlas = bytearray(W * H * 4)
    norms = bytearray(W * H * 4)
    catalog = []
    for i, t in enumerate(tiles):
        body = _fit32(t["w"], t["h"], t["rgba"])
        nrm = _normals(body)
        cell, ncell = _cell(body), _cell(nrm)
        r, c = divmod(i, per)
        for y in range(CELL):
            dst = ((r * CELL + y) * W + c * CELL) * 4
            src = y * CELL * 4
            atlas[dst:dst + CELL * 4] = cell[src:src + CELL * 4]
            norms[dst:dst + CELL * 4] = ncell[src:src + CELL * 4]
        catalog.append({"key": t["key"], "name": t["name"], "frame": t.get("frame", ""), "standin": t["key"].startswith("standin:")})
    os.makedirs(outdir, exist_ok=True)
    write_rgba(os.path.join(outdir, "atlas.png"), W, H, atlas)
    write_rgba(os.path.join(outdir, "normals.png"), W, H, norms)
    with open(os.path.join(outdir, "map.json"), "w") as f:
        json.dump({"cell": CELL, "per": per, "keys": keys}, f, indent=1)
    with open(os.path.join(outdir, "catalog.json"), "w") as f:
        json.dump({"standin": any(c["standin"] for c in catalog), "tiles": catalog,
                   "dropIn": "Replace standin: keys with the cut.py FNV key (%08x%08x%d of tile bytes, palette bytes, 8bpp flag). Author tiles at 16x16. Copy atlas.png, map.json and normals.png to the Play Room skin/ folder. Crisp skin stays off until rotk-crisp is on."}, f, indent=1)
    return {"tiles": len(tiles), "atlas": (W, H), "colours": "rgb555"}
