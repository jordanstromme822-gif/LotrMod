"""Siege map: Hornburg (level 46) and Hornburg Valley (47) joined into one map,
extended north past the Deeping Wall, written into level slot 45.

Usage: python3 tools/siege/build.py ROM.gba OUT_DIR [--base 0x01F00000] [--ext 37]

Writes OUT_DIR/siege.bin (data to place at ROM offset BASE), OUT_DIR/siege.json
(table patches + notes) and OUT_DIR/preview.png. The data holds only layout
(tile numbers, collision, spawn records); every picture comes from the game's
own tileset when the level loads.

Map format (docs/findings.md "Siege map"): 32 px cells, each cell a 4 x 4
block of 8 px tiles (metatile). Layer A (BG3, charbase 0, at most 1024 tiles)
and layer B (BG2, charbase 2, at most 512 tiles), each = tile list (tileset
numbers loaded in order into VRAM) + cell map + metatile table. Collision =
cell map of 16-byte definitions (4 x 4 subcells of 8 px; low 3 bits 1 or 2 =
blocked, bit 3 = raised).
"""
import json, os, random, struct, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import Rom, OBJECTS  # noqa: E402

SLOT = 45                 # level slot used for the Siege map (unused Hornburg slot)
DX, DY = 162, 60          # Hornburg Valley sits at (162, 60) tiles = (1296, 480) px from Hornburg
W = 264                   # 66 cells
MAX_CELLS = 5126          # EWRAM map buffers hold 0x2810 bytes each
BLANK = 47                # tileset tile that is all transparent
A_LIMIT, B_LIMIT = 1020, 500

# The fort (tile coordinates of the full joined map with the default --ext 37, E = 148 rows on top)
FORT_X0 = 104             # map starts here: everything left of the bastion (big tower) goes
FORT_TOP = -40            # rows of dark ground kept above the joined maps' top (relative to E)
GATE_X0, GATE_X1 = 156, 164   # north gateway: stone jambs at 156 and 163, opening 157..162
GATE_FACE = (212, 225)        # wall face rows
GATE_BUSH = (225, 233)        # dark shrubs under the wall
GATE_MERLON = (190, 203)      # merlons and the black edge above the walkway
FORT_START = (159, 240)       # hero start (tiles), just inside the gate
FORT_VENDORS = [(118, 252, 2), (140, 262, 0)]   # (x, y, kind): 2 = spirit shrine, 0 = forge


def u16s(b, n=None):
    n = len(b) // 2 if n is None else n
    return list(struct.unpack('<%dH' % n, b[:2 * n]))


class Level:
    def __init__(self, R, L):
        e = R.entry(L); self.e = e
        a0 = R.decomp(e[0]); a1 = R.decomp(e[1])
        self.a0 = u16s(a0[2:], u16s(a0, 1)[0]); self.a1 = u16s(a1[2:], u16s(a1, 1)[0])
        m = R.decomp(e[2]); self.w, self.h = m[0], m[2]; self.mapA = u16s(m[4:], self.w * self.h)
        self.metaA = R.decomp(e[3])
        self.mapB = u16s(R.decomp(e[6])[4:], self.w * self.h); self.metaB = R.decomp(e[7])
        self.coldef = R.decomp(e[10]); self.colmap = u16s(R.decomp(e[11])[4:], self.w * self.h)
        self.tileset = e[14]

    def tilegrid(self, layer):
        mp, meta, lst = (self.mapA, self.metaA, self.a0) if layer == 0 else (self.mapB, self.metaB, self.a1)
        g = [[None] * (self.w * 4) for _ in range(self.h * 4)]
        for cy in range(self.h):
            for cx in range(self.w):
                m = mp[cy * self.w + cx]
                for k, en in enumerate(struct.unpack('<16H', meta[4 + 32 * m:36 + 32 * m])):
                    g[cy * 4 + k // 4][cx * 4 + k % 4] = (lst[en & 0x3FF], en & 0xFC00)
        return g

    def colgrid(self):
        g = [[1] * (self.w * 4) for _ in range(self.h * 4)]
        for cy in range(self.h):
            for cx in range(self.w):
                d = self.coldef[16 * (self.colmap[cy * self.w + cx] & 0xFFF):][:16]
                for k in range(16): g[cy * 4 + k // 4][cx * 4 + k % 4] = d[k]
        return g


def pix(tb):
    v = np.zeros(64, np.uint8)
    for i, b in enumerate(tb): v[2 * i] = b & 15; v[2 * i + 1] = b >> 4
    return v.reshape(8, 8)


def merge_tiles(grid, pixels, rgb, limit, keep=()):
    """Swap the least visible tiles for their closest look-alike until at most
    `limit` remain. Returns {old: (new, flipbits)} and the mean colour error."""
    from collections import Counter, defaultdict
    uses = defaultdict(Counter)
    for row in grid:
        for t in row:
            if t: uses[t[0]][t[1] >> 12] += 1
    tiles = sorted(uses); n = len(tiles)
    if n <= limit: return {}, 0.0
    X = np.stack([pix(pixels[t]) for t in tiles])
    V = [X, X[:, :, ::-1], X[:, ::-1, :], X[:, ::-1, ::-1]]
    flipbits = [0, 0x400, 0x800, 0xC00]
    cost = np.zeros((n, n, 4))
    for p in sorted(set(p for u in uses.values() for p in u)):
        imgs = [rgb[p * 16 + v].reshape(n, -1).astype(np.int32) for v in V]
        trans = [(v == 0).reshape(n, -1) for v in V]
        w = np.array([uses[t][p] for t in tiles], float)
        for i in np.nonzero(w)[0]:
            for f in range(4):
                d = np.abs(imgs[f] - imgs[0][i]).sum(1) / 64.0 + (trans[f] != trans[0][i]).sum(1) * 40.0
                cost[i, :, f] += d * w[i]
    tot = np.array([sum(uses[t].values()) for t in tiles], float)
    cost /= tot[:, None, None]
    for i in range(n): cost[i, i, :] = 1e9
    for i, t in enumerate(tiles):
        if t in keep: cost[i, :, :] = 1e9      # drawn tiles (fort gate) always stay
    # never swap a textured tile for a (nearly) solid black one: dark ground turned into black bars
    lum = rgb.sum(1) / 3.0
    blk = np.array([float(np.mean([(lum[uses[t].most_common(1)[0][0] * 16 + v] if v else 0) < 12
                                   for v in X[k].flatten()])) for k, t in enumerate(tiles)])
    cost[np.ix_(blk < 0.95, blk >= 0.95)] = 1e9
    best = cost.min(2); bflip = cost.argmin(2)
    import heapq
    removed, kept, out, errs = set(), set(), {}, []
    heap = [(best[i].min(), i) for i in range(n)]; heapq.heapify(heap)
    count = n
    while count > limit and heap:
        c, i = heapq.heappop(heap)
        if i in removed or i in kept: continue
        row = best[i].copy()
        if removed: row[list(removed)] = 1e9
        j = int(row.argmin())
        if row[j] > c + 1e-9:          # target gone: requeue with the new cost
            heapq.heappush(heap, (row[j], i)); continue
        out[tiles[i]] = (tiles[j], [0, 0x400, 0x800, 0xC00][bflip[i, j]])
        removed.add(i); kept.add(j); errs.append(row[j]); count -= 1
    return out, float(np.mean(errs)) if errs else 0.0


def render(GA, GB, pixels, rgb, x0, y0, w, h):
    img = np.zeros((h * 8, w * 8, 3), np.int32)
    for G in (GA, GB):
        for y in range(h):
            for x in range(w):
                t = G[y0 + y][x0 + x]
                if t[0] == BLANK and G is GB: continue
                p_ = pix(pixels[t[0]])
                if t[1] & 0x400: p_ = p_[:, ::-1]
                if t[1] & 0x800: p_ = p_[::-1]
                c_ = rgb[(t[1] >> 12) * 16 + p_]
                m_ = p_ != 0 if G is GB else np.ones((8, 8), bool)
                s_ = img[y * 8:y * 8 + 8, x * 8:x * 8 + 8]; s_[m_] = c_[m_]
    return img


def draw_gate(img):
    """Paint an arched gateway with both wooden doors swung open onto the wall face picture
    (64 x 104 px RGB). Original art, drawn here; colours are mapped to the level palette later."""
    h, w = img.shape[:2]
    cx, top, r_in, r_out = 32, 30, 24, 31
    yy, xx = np.mgrid[0:h, 0:w]
    inside = ((xx >= 8) & (xx < 56) & (yy >= top)) | (((xx - cx + .5) ** 2 + (yy - top) ** 2 < r_in ** 2) & (yy < top))
    ring = (((xx - cx + .5) ** 2 + (yy - top) ** 2 < r_out ** 2) & (yy < top + 1) & ~inside) | \
           (((xx < 8) | (xx >= 56)) & (yy >= top) & ~inside)
    ring &= yy >= 2
    # stone surround: big light blocks with dark joints
    stone = np.array([176, 176, 176]); joint = np.array([56, 56, 56]); mid = np.array([128, 128, 128])
    ang = np.degrees(np.arctan2(yy - top, xx - cx + .5))
    for y in range(h):
        for x in range(w):
            if not ring[y, x]: continue
            if y < top:
                rr = np.hypot(x - cx + .5, y - top)
                c = joint if (abs(rr - r_out) < 1 or int((ang[y, x] + 180) / 15) != int((ang[y, x] + 180 + 1.2) / 15)) else \
                    (mid if rr > r_out - 2.5 else stone)
            else:
                c = joint if ((y - top) % 12 == 0 or x in (0, 63) or (x in (7, 56))) else (mid if x in (1, 62) else stone)
            img[y, x] = c
    # dark passage, a little lighter towards the far end (ground outside)
    for y in range(h):
        for x in range(w):
            if inside[y, x]:
                f = min(1.0, max(0.0, (y - 6) / (h - 6)))
                img[y, x] = (8 + 18 * f, 8 + 22 * f, 8 + 14 * f)
    # open doors, seen edge-on against the jambs (planks, iron bands, studs)
    wood = [(112, 88, 48), (88, 72, 40), (136, 120, 40), (80, 72, 40)]
    for side in (0, 1):
        for y in range(top - 6, h):
            for i in range(11):
                x = 8 + i if side == 0 else 55 - i
                # door top follows the arch a bit lower than the stone
                if (x - cx + .5) ** 2 + (y - top) ** 2 >= (r_in - 2) ** 2 and y < top: continue
                d = i if side == 0 else i
                col = wood[(d // 3) % 2] if d < 9 else (40, 32, 24)
                if d % 3 == 2: col = (64, 48, 40)
                if (y - top) % 26 in (12, 13): col = (32, 32, 32)          # iron bands
                if (y - top) % 26 == 12 and d % 3 == 1: col = (176, 168, 56)  # studs
                img[y, x] = col
    # threshold stone at the bottom of the opening
    img[h - 3:h, 8:56] = (56, 56, 56)
    return img


def quantize_tile(px, rgb, banks):
    """Best palette bank and 4bpp tile bytes for an 8 x 8 RGB block (colour 0 = see-through, unused)."""
    best = None
    for b in banks:
        pal = rgb[b * 16 + 1:b * 16 + 16].astype(np.int32)
        d = ((px.reshape(-1, 1, 3) - pal[None]) ** 2).sum(2)
        idx = d.argmin(1); err = d.min(1).sum()
        if best is None or err < best[0]: best = (err, b, idx + 1)
    v = best[2]
    return best[1], bytes(int(v[2 * i]) | int(v[2 * i + 1]) << 4 for i in range(32))


def fort_gate(GA, GB, GC, src, pixels, rgb, dark_at, grass_at, first_id):
    """Cut the north gateway: drawn arch and doors on the face, shrubs cleared below, merlons
    removed above, walking open through. Returns {tile number: 32 bytes} for the drawn tiles."""
    x0, x1 = GATE_X0, GATE_X1
    f0, f1 = GATE_FACE
    blankB = (BLANK, 0)
    before = render(GA, GB, pixels, rgb, x0, f0, x1 - x0, f1 - f0)
    after = draw_gate(before.copy())
    custom, seen = {}, {}
    for ty in range(f1 - f0):
        for tx in range(x1 - x0):
            a_ = after[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            if np.array_equal(a_, before[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]): continue
            bank, tb = quantize_tile(a_, rgb, (14, 11, 15, 10, 8))
            if (bank, tb) not in seen:
                seen[(bank, tb)] = first_id + len(custom); custom[seen[(bank, tb)]] = tb
                pixels[seen[(bank, tb)]] = tb
            GA[f0 + ty][x0 + tx] = (seen[(bank, tb)], bank << 12); GB[f0 + ty][x0 + tx] = blankB
    # walking: through the opening (inner six columns), shrubs cleared to grass below
    for y in range(GATE_BUSH[0], GATE_BUSH[1]):
        for x in range(x0 + 1, x1 - 1):
            ta, tb_, _ = grass_at(x, y)
            GA[y][x] = ta; GB[y][x] = tb_; src[y][x] = 'grass'
    for y in range(GATE_MERLON[0], GATE_BUSH[1]):
        for x in range(x0 + 1, x1 - 1):
            if y < GATE_MERLON[1] - 4:      # above the merlons: plain dark ground outside
                GA[y][x] = dark_at(x, y); GB[y][x] = blankB; src[y][x] = 'dark'
            elif y < GATE_MERLON[1]:        # merlon row: walkway pictures from further down (same pattern)
                GA[y][x] = GA[y + 8][x]; GB[y][x] = blankB
            if GC[y][x] & 7 in (1, 2) or y >= f0: GC[y][x] = 0
    for y in range(GATE_MERLON[0] - 6, GATE_MERLON[0]):
        for x in range(x0 + 1, x1 - 1): GC[y][x] = 0
    return custom


def write_map(R, a, GA, GB, GC, W, H, pixels_needed, rgb, custom, n_last, items, start, out_dir, base, extra_info=None):
    """Pack a finished map (tile grids, walking grid, drawn tiles, object records, hero start in px)
    into OUT_DIR/siege.bin + tables.bin + siege.json + preview.png, for level slot SLOT."""
    from spawns import build_groups
    # --- tiles: fit the game's tile memory --------------------------------
    pixels = pixels_needed
    mapA, errA = merge_tiles(GA, pixels, rgb, A_LIMIT, keep=set(custom))
    for y in range(H):
        for x in range(W):
            t = GA[y][x]
            if t[0] in mapA:
                nt, fb = mapA[t[0]]; GA[y][x] = (nt, t[1] ^ fb)
    mapB, errB = merge_tiles(GB, pixels, rgb, B_LIMIT)
    for y in range(H):
        for x in range(W):
            t = GB[y][x]
            if t[0] in mapB:
                nt, fb = mapB[t[0]]; GB[y][x] = (nt, t[1] ^ fb)

    listA = sorted(set(t[0] for row in GA for t in row))
    listB = sorted(set(t[0] for row in GB for t in row) | {BLANK})
    assert len(listA) <= 1024 and len(listB) <= 512, (len(listA), len(listB))
    slotA = {t: i for i, t in enumerate(listA)}; slotB = {t: i for i, t in enumerate(listB)}

    def metas(G, slot, first):
        table = [first] if first else []; idx = {m: i for i, m in enumerate(table)}; cells = []
        for cy in range(H // 4):
            for cx in range(W // 4):
                m = tuple(slot[G[cy * 4 + k // 4][cx * 4 + k % 4][0]] | G[cy * 4 + k // 4][cx * 4 + k % 4][1] for k in range(16))
                if m not in idx: idx[m] = len(table); table.append(m)
                cells.append(idx[m])
        return table, cells
    metaA, cellsA = metas(GA, slotA, None)
    metaB, cellsB = metas(GB, slotB, tuple([slotB[BLANK]] * 16))
    defs = [bytes([1] * 16)]; didx = {defs[0]: 0}; cellsC = []
    for cy in range(H // 4):
        for cx in range(W // 4):
            d = bytes(GC[cy * 4 + k // 4][cx * 4 + k % 4] for k in range(16))
            if d not in didx: didx[d] = len(defs); defs.append(d)
            cellsC.append(didx[d])

    # --- object records -------------------------------------------------------
    blob46 = R.u32(OBJECTS + 12 * 46 + 4)
    hdr = R.rom[blob46 - 0x08000000:][:0x30]
    sub = struct.unpack('<H', hdr[0:2])[0]
    parts = [struct.unpack('<H', R.rom[blob46 - 0x08000000 + sub + 0xC + 8 * i:][:2])[0] for i in range(2)]
    part0 = R.decomp(blob46 + parts[0])
    groups = build_groups([dict(b1=0, items=list(items))])
    empty = b'\x00\x00\x00\x00'
    p1 = bytearray(8) + groups
    off_paths = len(p1); p1 += empty
    off_scripts = len(p1); p1 += empty
    off_tail = len(p1); p1 += b'\x00\x00\xff\xff'
    struct.pack_into('<HHHH', p1, 0, off_paths, off_scripts, 1, off_tail)
    # entry points: both at the hero start
    blob = bytearray(hdr)
    e0x, e0y = start
    struct.pack_into('<HH', blob, 4, e0x, e0y)
    struct.pack_into('<HH', blob, 12, e0x + 16, e0y)

    # --- write everything as raw (type 0) data -----------------------------
    out = bytearray()
    def add(payload):
        while len(out) % 4: out.append(0)
        pos = len(out)
        pl = bytes(payload) + b'\x00' * (-len(payload) % 4)
        out.extend(struct.pack('<I', len(pl) << 8)); out.extend(pl)
        return base + 0x08000000 + pos
    def blobpart(b_):
        pl = bytes(b_) + b'\x00' * (-len(b_) % 4)
        return struct.pack('<I', len(pl) << 8) + pl
    pA0 = add(struct.pack('<H', len(listA)) + struct.pack('<%dH' % len(listA), *listA))
    pA1 = add(struct.pack('<H', len(listB)) + struct.pack('<%dH' % len(listB), *listB))
    cw, ch = W // 4, H // 4
    # Layer A metatiles past 1024 don't fit the game's buffer (0x02022D40, 0x8010 bytes).
    # The layer B buffer right after it is mostly free, and the game indexes
    # metatiles as base + 32 * n with no limit, so the extra ones ride inside the
    # layer B data, placed where index n lands (B is loaded after A).
    A_BUF, B_BUF = 0x02022D44, 0x0202AD54
    fitA = metaA[:1024]; extra = metaA[1024:]
    first_extra = 1025 + len(metaB) if extra else 0
    remap = {i: (i if i < 1024 else first_extra + i - 1024) for i in range(len(metaA))}
    cellsA = [remap[c] for c in cellsA]
    pMapA = add(bytes([cw, 0, ch, 0]) + struct.pack('<%dH' % len(cellsA), *cellsA))
    pMetaA = add(struct.pack('<I', len(fitA)) + b''.join(struct.pack('<16H', *m) for m in fitA))
    pMapB = add(bytes([cw, 0, ch, 0]) + struct.pack('<%dH' % len(cellsB), *cellsB))
    bdata = bytearray(b''.join(struct.pack('<16H', *m) for m in metaB))
    for k, m in enumerate(extra):
        off = A_BUF + 32 * (first_extra + k) - B_BUF
        assert off >= len(bdata) or k > 0
        if len(bdata) < off: bdata += bytes(off - len(bdata))
        bdata[off:off + 32] = struct.pack('<16H', *m)
    assert 4 + len(bdata) <= 0x8010, 'layer B buffer overflow'
    pMetaB = add(struct.pack('<I', len(metaB)) + bytes(bdata))
    pDefs = add(b''.join(defs))
    pCol = add(struct.pack('<HH', len(defs), 0) + struct.pack('<%dH' % len(cellsC), *cellsC))
    # object blob: header + sub table from Hornburg, parts stored raw
    while len(out) % 4: out.append(0)
    pBlob = base + 0x08000000 + len(out)
    b0 = blobpart(part0); b1 = blobpart(p1)
    o0 = len(blob); o1 = o0 + len(b0)
    struct.pack_into('<H', blob, sub + 0xC, o0); struct.pack_into('<H', blob, sub + 0xC + 8, o1)
    out.extend(blob + b0 + b1)

    # tileset: the game's own two chunks (1024 + 389 tiles); the second one is stored again as a plain
    # copy with the drawn tiles added at its end (numbers 1413 + k). Loader 0x080324C8: chunk k entry
    # at tileset + 4 + 8k = (u16 storage, u16 count, u32 offset from the tileset start); it expects
    # every chunk but the last to hold 1024 tiles. Decoder 0x08019EDC reads the storage kind from the
    # entry: 0 = plain copy (CpuFastSet) of count * 32 bytes, no header. Chunk 0 is reached with a
    # wrapped offset back into the game's tileset.
    ts_old = a.tileset
    th = R.rom[ts_old - 0x08000000:][:0x14]
    f0, cnt0, off0 = struct.unpack('<HHI', th[4:12])
    assert cnt0 == 1024
    first = 1024 + n_last
    assert sorted(custom) == list(range(first, first + len(custom)))
    chunk1 = b''.join(R.tiles(ts_old, list(range(1024, first)))) + b''.join(custom[t] for t in sorted(custom))
    while len(out) % 4: out.append(0)
    pTS = base + 0x08000000 + len(out)
    tsb = bytearray(th[:4])
    tsb += struct.pack('<HHI', f0, cnt0, (ts_old + off0 - pTS) & 0xFFFFFFFF)
    tsb += struct.pack('<HHI', 0, len(chunk1) // 32, len(tsb) + 8)
    tsb += chunk1
    assert len(chunk1) // 32 <= 1024
    out.extend(tsb)

    entry = a.e[:]
    entry[14] = pTS
    entry[0], entry[1], entry[2], entry[3] = pA0, pA1, pMapA, pMetaA
    entry[6], entry[7] = pMapB, pMetaB
    entry[10], entry[11] = pDefs, pCol
    obj = list(struct.unpack('<3I', R.rom[OBJECTS - 0x08000000 + 12 * 46:][:12])); obj[1] = pBlob

    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, 'siege.bin'), 'wb').write(out)
    info = dict(slot=SLOT, base=base, size=len(out), width_cells=cw, height_cells=ch,
                level_entry_at=LEVELS_ADDR(SLOT), level_entry=[hex(x) for x in entry],
                object_entry_at=hex(OBJECTS + 12 * SLOT), object_entry=[hex(x) for x in obj],
                tilesA=len(listA), tilesB=len(listB), metasA=len(metaA), metasA_in_B_buffer=len(extra), metasB=len(metaB), coldefs=len(defs),
                merged_tilesA=len(mapA), merged_tilesB=len(mapB), merge_errorA=errA, merge_errorB=errB,
                hero_start=[e0x, e0y], items=len(items), drawn_tiles=len(custom),
                tileset=hex(entry[14]), **(extra_info or {}))
    json.dump(info, open(os.path.join(out_dir, 'siege.json'), 'w'), indent=1)
    patch = bytearray()
    patch += struct.pack('<I', LEVELS_ADDR_INT(SLOT) - 0x08000000) + struct.pack('<19I', *entry)
    patch += struct.pack('<I', OBJECTS + 12 * SLOT - 0x08000000) + struct.pack('<3I', *obj)
    open(os.path.join(out_dir, 'tables.bin'), 'wb').write(patch)
    # preview
    try:
        from PIL import Image
        img = np.zeros((H * 8, W * 8, 3), np.uint8)
        cache = {}
        for G in (GA, GB):
            for y in range(H):
                for x in range(W):
                    t = G[y][x]
                    if t[0] == BLANK and G is GB: continue
                    key = t
                    if key not in cache:
                        p_ = pix(pixels[t[0]])
                        if t[1] & 0x400: p_ = p_[:, ::-1]
                        if t[1] & 0x800: p_ = p_[::-1]
                        cache[key] = (p_ != 0, rgb[(t[1] >> 12) * 16 + p_].astype(np.uint8))
                    m_, c_ = cache[key]
                    s_ = img[y * 8:y * 8 + 8, x * 8:x * 8 + 8]; s_[m_] = c_[m_]
        Image.fromarray(img).save(os.path.join(out_dir, 'preview.png'))
        walk = np.array([[0 if (v & 7) in (1, 2) else 1 for v in row] for row in GC], np.uint8)
        ov = img.copy().astype(np.int32)
        wm = np.kron(walk, np.ones((8, 8), np.uint8)).astype(bool)
        ov[wm] = (ov[wm] * 0.55 + np.array([40, 200, 40]) * 0.45)
        Image.fromarray(ov.astype(np.uint8)).save(os.path.join(out_dir, 'walkable.png'))
    except ImportError:
        pass
    return info


def build(rom_path, out_dir, base=0x01F00000, ext=37, seed=7):
    global W
    R = Rom(rom_path)
    a, b = Level(R, 46), Level(R, 47)
    assert a.tileset == b.tileset and a.e[15] == b.e[15]
    H0 = 160
    H = H0 + ext * 4
    assert (W // 4) * (H // 4) <= MAX_CELLS, 'map too big'
    E = ext * 4  # rows added on top

    pal = R.rom[a.e[15] - 0x08000000:][:0x200]  # palette data is raw at +0x3C? (checked below)
    # palette: use the live BG palette dump if the raw one doesn't look right
    P = np.frombuffer(pal, dtype='<u2')
    rgb = np.stack([(P & 31) << 3, ((P >> 5) & 31) << 3, ((P >> 10) & 31) << 3], 1).astype(np.int32)

    LA, LB, CA = a.tilegrid(0), a.tilegrid(1), a.colgrid()
    MA, MB, MC = b.tilegrid(0), b.tilegrid(1), b.colgrid()
    # Hornburg's two wall staircases have collapsed top steps (blocked). The Valley's staircase is the same
    # art, intact: copy its pictures and walking over both (Jordan 2026-11-19: "redraw them and fix them").
    # (Hornburg x0..x1, y0..y1) <- Valley at (x + vx, y + vy); offsets found by matching the intact steps.
    # The rest of each staircase takes the Valley's walking where the pictures already match, so the
    # steps line up with no blocked row where the copied top meets Hornburg's own steps.
    for (x0, x1, y0, y1), (bx0, bx1, by0, by1), vx, vy in (((40, 49, 49, 60), (36, 66, 44, 82), -22, -36),
                                                           ((180, 189, 73, 84), (170, 192, 62, 100), -DX, -DY)):
        for y in range(by0, by1):
            for x in range(bx0, bx1):
                yy, xx = y + vy, x + vx
                if not (0 <= yy < len(MA) and 0 <= xx < len(MA[0])): continue
                if x0 <= x < x1 and y0 <= y < y1:
                    LA[y][x], LB[y][x], CA[y][x] = MA[yy][xx], MB[yy][xx], MC[yy][xx]
                elif LA[y][x] == MA[yy][xx] and LB[y][x] == MB[yy][xx] and LA[y][x][0] != BLANK:
                    CA[y][x] = MC[yy][xx]
    GA = [[None] * W for _ in range(H)]; GB = [[None] * W for _ in range(H)]
    GC = [[1] * W for _ in range(H)]
    src = [[''] * W for _ in range(H)]     # where each tile came from, for fixups

    def put(x, y, ta, tb, c, s):
        GA[y][x] = ta; GB[y][x] = tb; GC[y][x] = c; src[y][x] = s

    for y in range(100):
        for x in range(192): put(x, y + E, LA[y][x], LB[y][x], CA[y][x], '46')
    for y in range(100):
        for x in range(100):
            X, Y = x + DX, y + DY
            if X >= 192 or Y >= 96: put(X, Y + E, MA[y][x], MB[y][x], MC[y][x], '47')

    # --- texture sources -------------------------------------------------
    lumP = rgb.sum(1) / 3.0
    def tlum(t):
        if not t or t[0] == BLANK: return 0
        p = pix(pixels_needed[t[0]]) if t[0] in pixels_needed else None
        return 0 if p is None else max(lumP[(t[1] >> 12) * 16 + v] if v else 0 for v in p.flatten())

    def mlum(t):
        if not t or t[0] == BLANK: return 0
        p = pix(pixels_needed[t[0]]) if t[0] in pixels_needed else None
        return 0 if p is None else float(np.mean([lumP[(t[1] >> 12) * 16 + v] if v else 0 for v in p.flatten()]))

    def black(t, th=0.95):
        if not t or t[0] == BLANK: return False
        p = pix(pixels_needed[t[0]]) if t[0] in pixels_needed else None
        if p is None: return False
        return float(np.mean([(lumP[(t[1] >> 12) * 16 + v] if v else 0) < 12 for v in p.flatten()])) >= th

    need = set()
    for g in (LA, MA):
        for row in g:
            for t in row:
                if t: need.add(t[0])
    need_b = set()
    for g in (LB, MB):
        for row in g:
            for t in row:
                if t: need_b.add(t[0])
    need = sorted(need); need_b = sorted(need_b)
    pixels_needed = dict(zip(need, R.tiles(a.tileset, need)))
    pixels_needed.update(dict(zip(need_b, R.tiles(a.tileset, need_b))))

    # dark ground: Hornburg cells that are fully blocked, dark and torch-free
    dark_cells = []
    for cy in range(2, 25):
        for cx in range(14, 48):
            blk = [(LA[cy * 4 + k // 4][cx * 4 + k % 4]) for k in range(16)]
            if any(t[0] == BLANK for t in blk): continue
            if any(LB[cy * 4 + k // 4][cx * 4 + k % 4][0] != BLANK for k in range(16)): continue
            if any(CA[cy * 4 + k // 4][cx * 4 + k % 4] != 1 for k in range(16)): continue
            if max(tlum(t) for t in blk) > 70: continue
            if any(black(t) for t in blk): continue   # solid black tiles (272/273) read as holes
            # all eight neighbours must also be outside (keeps wall edges and torch light out)
            ok = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = cy + dy, cx + dx
                    if not (0 <= yy < 25 and 0 <= xx < 48): ok = False; continue
                    for k in range(16):
                        if CA[yy * 4 + k // 4][xx * 4 + k % 4] != 1: ok = False
                        t = LA[yy * 4 + k // 4][xx * 4 + k % 4]
                        if t[0] == BLANK or tlum(t) > 90: ok = False
            if ok: dark_cells.append(blk)
    assert dark_cells, 'no dark ground cells found'
    rnd = random.Random(seed)
    dark_choice = {}

    def dark_at(x, y):
        k = (x // 4, y // 4)
        if k not in dark_choice: dark_choice[k] = rnd.randrange(len(dark_cells))
        return dark_cells[dark_choice[k]][(y % 4) * 4 + x % 4]

    blankA = (BLANK, 0); blankB = (BLANK, 0)

    # 1) everything above the old maps and the empty top right: dark ground
    #    (black above the Hornburg tower, as in the original)
    tower_right = 50
    for y in range(H):
        for x in range(W):
            if src[y][x]: continue
            if y < E + 60 and not (y >= E + 100):
                if x < tower_right and y < E:
                    put(x, y, blankA, blankB, 1, 'void')
                else:
                    put(x, y, dark_at(x, y), blankB, 0, 'dark')
    # 2) Hornburg's black sky and the stray tower piece become dark ground too
    for y in range(E, E + 75):
        for x in range(tower_right, W):
            t = GA[y][x]
            if src[y][x] in ('46', '47') and (t[0] == BLANK or (src[y][x] == '46' and 136 <= x < 144 and y < E + 12)):
                put(x, y, dark_at(x, y), blankB, 0, 'dark')
            elif src[y][x] in ('46', '47') and GB[y][x][0] == BLANK and black(t):
                # all-black sky pieces left between the merlons: dark ground, walking unchanged
                put(x, y, dark_at(x, y), blankB, GC[y][x], src[y][x])

    # 3) bottom left (below Hornburg, left of the Valley): grass, forest edge at the bottom
    grass_cells = []
    for cy in range(19, 24):
        for cx in range(0, 13):
            blk = [(LA[cy * 4 + k // 4][cx * 4 + k % 4], LB[cy * 4 + k // 4][cx * 4 + k % 4],
                    CA[cy * 4 + k // 4][cx * 4 + k % 4]) for k in range(16)]
            if any(t[1][0] != BLANK or t[2] in (1, 2) for t in blk): continue
            grass_cells.append((np.mean([mlum(t[0]) for t in blk]), blk))
    # plain light grass only (mean brightness, not the brightest pixel): dark patches make a checkerboard
    lums = sorted(g[0] for g in grass_cells); top = lums[-1]
    grass_cells = [g[1] for g in grass_cells if g[0] > top - 3] or [g[1] for g in grass_cells]
    grass_choice = {}
    def grass_at(x, y):
        k = (x // 4, y // 4)
        if k not in grass_choice: grass_choice[k] = rnd.randrange(len(grass_cells))
        return grass_cells[grass_choice[k]][(y % 4) * 4 + x % 4]
    forest_rows = 14
    fsrc_y0 = 100 - forest_rows
    forest = [(MA[y][x], MB[y][x], MC[y][x]) for y in range(fsrc_y0, 100) for x in range(0, 36)]
    fw = 36
    left_strip = 8  # Valley's own forest strip on its left side goes too
    for y in range(E + 96, H):
        for x in range(0, DX + left_strip):
            if x >= DX and src[y][x] != '47': continue
            if y >= H - forest_rows and x < DX:
                ta, tb, c = forest[(y - (H - forest_rows)) * fw + (x % fw)]
                put(x, y, ta, tb, c, 'forest')
            elif x >= DX and y >= H - forest_rows:
                continue   # keep the Valley's own bottom forest
            else:
                ta, tb, c = grass_at(x, y)
                put(x, y, ta, tb, c, 'grass')

    # anything still empty (the two columns right of the Valley): repeat the edge, solid
    for y in range(H):
        for x in range(W):
            if not src[y][x]:
                put(x, y, GA[y][x - 1], GB[y][x - 1], 1, 'edge')

    # torch spots (spawn type 19) in both maps, in final tile coordinates
    torch_spots = []
    for L, ox, oy in ((46, 0, 0), (47, DX, DY)):
        bl = R.u32(OBJECTS + 12 * L + 4)
        s_ = struct.unpack('<H', R.rom[bl - 0x08000000:][:2])[0]
        p1o = struct.unpack('<H', R.rom[bl - 0x08000000 + s_ + 0xC + 8:][:2])[0]
        from spawns import parse_groups
        for g in parse_groups(R.decomp(bl + p1o)[8:]):
            for it in g['items']:
                if it[0] == 19:
                    x, y = struct.unpack('<HH', it[4:8]); torch_spots.append((x // 8 + ox, y // 8 + oy + E))
    near_torch = set()
    post = set()
    for tx, ty in torch_spots:
        for dy in range(-6, 4):
            for dx in range(-5, 6): near_torch.add((tx + dx, ty + dy))
        for dy in range(-4, 1):
            for dx in (-1, 0): post.add((tx + dx, ty + dy))

    # --- walkability -----------------------------------------------------
    # outside = dark tiles and blocked subcells reachable from the extension
    from collections import deque
    outside = [[False] * W for _ in range(H)]
    def is_dark(x, y):
        if src[y][x] == 'dark': return True
        if src[y][x] not in ('46', '47'): return False
        t = GA[y][x]
        if (x, y) in near_torch:
            return GC[y][x] in (1, 2, 9, 10) and t[0] != BLANK
        return GC[y][x] in (1, 2, 9, 10) and t[0] != BLANK and tlum(t) <= 95 and GB[y][x][0] == BLANK
    q = deque([(W - 4, 4)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < W and 0 <= y < H) or outside[y][x] or not is_dark(x, y): continue
        outside[y][x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    MARGIN = 2
    for y in range(H):
        for x in range(W):
            if not outside[y][x]: continue
            near_wall = any(0 <= x + dx < W and 0 <= y + dy < H and not outside[y + dy][x + dx]
                            and src[y + dy][x + dx] in ('46', '47') and (x + dx, y + dy) not in near_torch
                            for dy in range(-MARGIN, MARGIN + 1) for dx in range(-MARGIN, MARGIN + 1))
            GC[y][x] = 1 if near_wall else 0
    # torch posts stay solid
    for y in range(H):
        for x in range(W):
            if outside[y][x] and (x, y) in post: GC[y][x] = 1

    # the breach in the Deeping Wall: walk up the rubble and out (Valley subcells)
    breach = []
    for y in range(12, 48):
        x0 = 53 if y >= 22 else 55
        x1 = 63 if y >= 22 else 65
        if y >= 34: x0, x1 = 51, 62
        for x in range(x0, x1 + 1): breach.append((x, y))
    for x, y in breach:
        X, Y = x + DX, y + DY + E
        if src[Y][X] == '47' and GC[Y][X] & 7 in (1, 2): GC[Y][X] = 0

    # --- the fort (Jordan 2026-11-19): a smaller Helm's Deep in the bottom-left corner ----------
    # North wall (right of the bastion) gets a drawn gateway with open wooden doors; the breach in
    # the slanted wall is the east gate. Then the map is cropped to the fort and the ground north
    # and east of it.
    ts_hdr = R.rom[a.tileset - 0x08000000:][:0x14]
    n_last = struct.unpack('<H', ts_hdr[0xE:0x10])[0]          # tiles in the game's second chunk
    custom = fort_gate(GA, GB, GC, src, pixels_needed, rgb, dark_at, grass_at, 1024 + n_last)
    FX0, FY0 = FORT_X0, E + FORT_TOP
    GA = [r[FX0:] for r in GA[FY0:]]; GB = [r[FX0:] for r in GB[FY0:]]
    GC = [r[FX0:] for r in GC[FY0:]]; src = [r[FX0:] for r in src[FY0:]]
    W = W - FX0; H = H - FY0
    assert W % 4 == 0 and H % 4 == 0

    # map edges are walls
    for y in range(H):
        GC[y][0] = GC[y][W - 1] = 1
    for x in range(W):
        GC[0][x] = GC[H - 1][x] = 1

    if os.environ.get('SIEGE_DUMP'):
        import pickle; pickle.dump((GA, GB, GC, src, E, H), open(os.environ['SIEGE_DUMP'], 'wb'))
    # --- spawn records: torches only, no enemies -------------------------
    from spawns import parse_groups, build_groups
    torches = []
    for L, ox, oy, keep in ((46, 0, 0, lambda x, y: True),
                            (47, DX * 8, DY * 8, lambda x, y: x >= 192 * 8 or y >= 100 * 8)):
        bl = R.u32(OBJECTS + 12 * L + 4)
        s = struct.unpack('<H', R.rom[bl - 0x08000000:][:2])[0]
        p1o = struct.unpack('<H', R.rom[bl - 0x08000000 + s + 0xC + 8:][:2])[0]
        p1 = R.decomp(bl + p1o)
        for g in parse_groups(p1[8:]):
            for it in g['items']:
                if it[0] != 19: continue
                x, y = struct.unpack('<HH', it[4:8]); X, Y = x + ox, y + oy
                if not keep(X, Y): continue
                X, Y = X - FX0 * 8, Y + E * 8 - FY0 * 8
                if not (0 <= X < W * 8 and 0 <= Y < H * 8): continue
                torches.append(it[:4] + struct.pack('<HH', X, Y) + it[8:])
    # spirit shrine (vendor kind 2) and forge (kind 0) in the courtyard, records as in level 47
    vendors = [bytes([17, 0, 0, 0]) + struct.pack('<HH', (tx - FX0) * 8, (ty - FY0) * 8) + bytes([kind, 0xFF, 0xFF, 0xFF])
               for (tx, ty, kind) in FORT_VENDORS]

    start = ((FORT_START[0] - FX0) * 8, (FORT_START[1] - FY0) * 8)
    return write_map(R, a, GA, GB, GC, W, H, pixels_needed, rgb, custom, n_last, torches + vendors, start,
                     out_dir, base, dict(ext_cells=ext, torches=len(torches), vendors=len(vendors)))


def LEVELS_ADDR_INT(L):
    from romlib import LEVELS
    return LEVELS + 0x4C * L


def LEVELS_ADDR(L): return hex(LEVELS_ADDR_INT(L))


if __name__ == '__main__':
    args = sys.argv[1:]
    base = 0x01F00000; ext = 37
    if '--base' in args: i = args.index('--base'); base = int(args[i + 1], 0); del args[i:i + 2]
    if '--ext' in args: i = args.index('--ext'); ext = int(args[i + 1], 0); del args[i:i + 2]
    print(json.dumps(build(args[0], args[1], base, ext), indent=1))
