"""Pack the joined Flooded Field + Tower Base ground (fill.py's world.pkl) into level slot 51 for the big-map engine
(tools/bigmap): maps and walking data kept in ROM, two tile sets that the engine swaps as the hero crosses the middle.

python3 tools/join/level.py ROM WORLD_DIR OUT_DIR [BASE]

OUT_DIR gets join.bin (goes at ROM BASE, default 0x1700000 = CPU 0x09700000, starts with the BMAP table the engine
reads), tables.bin (level and object table entries for slot 51), join.json and preview.png.
"""
import json, os, pickle, struct, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'siege'))
from romlib import Rom, LEVELS, OBJECTS
from spawns import parse_groups, build_groups

rom_path, wdir, out_dir = sys.argv[1:4]
BASE = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x1700000
CPU = 0x08000000 + BASE
SLOT, FF, TB = 51, 51, 55
BLANK = 0
R = Rom(rom_path)
w = pickle.load(open(os.path.join(wdir, 'world.pkl'), 'rb'))
GA, GB, GC, W, H, TX, FY = w['GA'], w['GB'], w['GC'], w['W'], w['H'], w['TX'], w['FY']
TBH = FY - w['GAP']                      # Tower Base rows (cells)
SPLIT = (TBH + FY) // 2                  # the hero above this row sees set 0 (Tower Base), below it set 1
MARGIN = 12                              # cells either side of the split that may only use tiles in both sets

# ---- tile sets ----------------------------------------------------------------------------------------------
def zone_tiles(G, y0, y1):
    return {G[y][x][0] for y in range(y0 * 4, y1 * 4) for x in range(W * 4)}
setsA = [zone_tiles(GA, 0, SPLIT), zone_tiles(GA, SPLIT, H)]
setsB = [zone_tiles(GB, 0, SPLIT) | {BLANK}, zone_tiles(GB, SPLIT, H) | {BLANK}]
midA, midB = zone_tiles(GA, SPLIT - MARGIN, SPLIT + MARGIN), zone_tiles(GB, SPLIT - MARGIN, SPLIT + MARGIN)
shA, shB = (setsA[0] & setsA[1]) | midA, (setsB[0] & setsB[1]) | midB   # tiles near the middle are in both sets
onlyA = [sorted(setsA[0] - shA), sorted(setsA[1] - shA)]
onlyB = [sorted(setsB[0] - shB), sorted(setsB[1] - shB)]
shA = sorted(shA); shB = [BLANK] + sorted(shB - {BLANK})
nA = [len(shA) + len(o) for o in onlyA]; nB = [len(shB) + len(o) for o in onlyB]
print('layer A shared', len(shA), 'sets', nA, ' layer B shared', len(shB), 'sets', nB)
assert max(nA) <= 1024 and max(nB) <= 512, (nA, nB)
# custom tileset order: A shared, A set 0, A set 1, B shared, B set 0, B set 1 (each list then ascends)
order = shA + onlyA[0] + onlyA[1] + shB + onlyB[0] + onlyB[1]
tsi = {}
pos = 0
def block(tiles):
    global pos
    r = list(range(pos, pos + len(tiles))); pos += len(tiles); return r
iA_sh, iA0, iA1 = block(shA), block(onlyA[0]), block(onlyA[1])
iB_sh, iB0, iB1 = block(shB), block(onlyB[0]), block(onlyB[1])
listsA = [iA_sh + iA0, iA_sh + iA1]; listsB = [iB_sh + iB0, iB_sh + iB1]
slotA = [dict(), dict()]; slotB = [dict(), dict()]
for s in (0, 1):
    for i, t in enumerate(shA + onlyA[s]): slotA[s][t] = i
    for i, t in enumerate(shB + onlyB[s]): slotB[s][t] = i
uniq = sorted(set(order))                     # R.tiles reads the game's tileset in ascending order
pix_of = dict(zip(uniq, R.tiles(R.entry(FF)[14], uniq)))
pixels = [pix_of[t] for t in order]
tiles_raw = b''.join(pixels)

# ---- metatiles, maps, walking data --------------------------------------------------------------------------------
def metas(G, slots, first):
    table = [first] if first else []; idx = {m: i for i, m in enumerate(table)}; cells = []
    for cy in range(H):
        s = 0 if cy < SPLIT else 1
        for cx in range(W):
            m = tuple(slots[s][G[cy * 4 + k // 4][cx * 4 + k % 4][0]] | G[cy * 4 + k // 4][cx * 4 + k % 4][1] for k in range(16))
            if m not in idx: idx[m] = len(table); table.append(m)
            cells.append(idx[m])
    return table, cells
metaA, cellsA = metas(GA, slotA, None)
metaB, cellsB = metas(GB, slotB, tuple([0] * 16))
defs = [bytes([1] * 16)]; didx = {defs[0]: 0}; cellsC = []
for cy in range(H):
    for cx in range(W):
        d = bytes(GC[cy * 4 + k // 4][cx * 4 + k % 4] for k in range(16))
        if d not in didx: didx[d] = len(defs); defs.append(d)
        cellsC.append(didx[d])
print('metatiles A', len(metaA), 'B', len(metaB), 'walk defs', len(defs))
assert len(defs) <= 1024 and len(metaA) < 65536 and len(metaB) < 65536

# ---- objects: Flooded Field's records moved down, Tower Base's moved right, the door between them gone ----------
def obj_parts(L):
    blob = struct.unpack('<3I', R.rom[OBJECTS - 0x08000000 + 12 * L:][:12])[1]
    b = R.rom[blob - 0x08000000:]; sub, n = struct.unpack('<HH', b[:4])
    ents = [bytes(b[4 + 8 * i:12 + 8 * i]) for i in range(n)]
    np_ = b[sub]; parts = []
    for i in range(np_):
        off = struct.unpack('<H', b[sub + 0xC + 8 * i:][:2])[0]
        parts.append(bytes(R.decomp(blob + off)))
    return bytes(b[sub:sub + 0xC + 8 * np_]), ents, parts
def split_part(d):
    op, osc, cnt, ot = struct.unpack('<HHHH', d[:8])
    return parse_groups(d[8:]), d[op:osc], d[osc:ot], d[ot:], cnt
def move(it, dx, dy):
    it = bytearray(it); x, y = struct.unpack('<HH', it[4:8]); struct.pack_into('<HH', it, 4, x + dx, y + dy); return bytes(it)
fsub, fents, fparts = obj_parts(FF)
tsub, tents, tparts = obj_parts(TB)
FDY, TDX = FY * 32, TX * 32
tgroups = split_part(tparts[1])[0]
KEEP_TB = {0x1A, 0x0B, 0x08, 0x03}          # orc spawns, enemies, ladders/markers, the door to 57
tb_items = [move(it, TDX, 0) for g in tgroups for it in g['items'] if it[0] in KEEP_TB]
def merged(part):
    groups, paths, scripts, tail, cnt = split_part(part)
    out = []
    for g in groups:
        items = []
        for it in g['items']:
            if it[0] == 3 and it[0xB] == TB: continue                     # the door to Tower Base
            if it[0] == 0x12 and struct.unpack('<HH', it[4:8]) == (568, 9): continue   # its marker
            items.append(move(it, 0, FDY))
        out.append(dict(b1=g['b1'], items=items))
    out.append(dict(b1=0, items=tb_items))
    gb_ = build_groups(out)
    p = bytearray(8) + gb_
    o_paths = len(p); p += paths
    o_scripts = len(p); p += scripts
    o_tail = len(p); p += tail
    struct.pack_into('<HHHH', p, 0, o_paths, o_scripts, cnt, o_tail)
    return bytes(p)
newparts = [fparts[0]] + [merged(p) for p in fparts[1:]]
# entry points: Flooded Field's (entry 0) moved down, Tower Base's north entry (its entry 1) becomes entry 1
def shift(e, dx, dy):
    x, y = struct.unpack('<HH', e[:4]); return struct.pack('<HH', x + dx, y + dy) + e[4:]
ents = [shift(e, 0, FDY) for e in fents]                       # Flooded Field's entry 0 (both players)
ents += [shift(e, TDX, 0) for e in tents if e[4] == 1]         # Tower Base's north entry (from 57), now entry 1
# sub table header: part count, entry count, one byte per entry, then the rest as Flooded Field has it
sub = bytes([fsub[0], 2, fsub[2], tsub[3]]) + bytes(fsub[3:8]) + b'\xff\xff\xff'
assert len(sub) == 0xC

# ---- write -------------------------------------------------------------------------------------------------------
out = bytearray(0x40)                        # BMAP table, filled in at the end
def add_raw(payload):
    while len(out) % 4: out.append(0)
    p = CPU + len(out); out.extend(payload); return p
def add_blob(payload, marker=0):
    while len(out) % 4: out.append(0)
    pos = len(out)
    pl = bytes(payload) + b'\0' * (-len(payload) % 4)
    out.extend(struct.pack('<I', (len(pl) << 8) | marker)); out.extend(pl)
    return CPU + pos
def lst(l): return struct.pack('<H', len(l)) + struct.pack('<%dH' % len(l), *l)
pL = [[add_raw(lst(listsA[s])), add_raw(lst(listsB[s]))] for s in (0, 1)]
# tileset: chunks of 1024 plain tiles (storage 0); every chunk but the last holds 1024
th = R.rom[R.entry(FF)[14] - 0x08000000:][:4]
nt = len(order); chunks = [(i, min(1024, nt - i)) for i in range(0, nt, 1024)]
hdr = bytearray(th[:4]); data_off = 4 + 8 * len(chunks)
while (len(hdr) + 8 * len(chunks)) % 4: pass
for i, (s, c) in enumerate(chunks):
    hdr += struct.pack('<HHI', 0, c, data_off + 32 * s)
while len(out) % 4: out.append(0)
pTS = CPU + len(out); out.extend(hdr + tiles_raw)
# initial lists (level table +0x00/+0x04 are compressed blobs): set 1, Flooded Field (the usual way in)
pA0 = add_blob(lst(listsA[1])); pA1 = add_blob(lst(listsB[1]))
pMapA = add_blob(bytes([W, 0, H, 0]) + struct.pack('<%dH' % len(cellsA), *cellsA), 1)
pMetaA = add_blob(struct.pack('<I', len(metaA)) + b''.join(struct.pack('<16H', *m) for m in metaA), 1)
pMapB = add_blob(bytes([W, 0, H, 0]) + struct.pack('<%dH' % len(cellsB), *cellsB), 1)
pMetaB = add_blob(struct.pack('<I', len(metaB)) + b''.join(struct.pack('<16H', *m) for m in metaB), 1)
pDefs = add_blob(b''.join(defs))
pCol = add_blob(struct.pack('<HH', len(defs), 0) + struct.pack('<%dH' % len(cellsC), *cellsC), 1)
# object blob: entries, sub table, parts stored raw
while len(out) % 4: out.append(0)
pBlob = CPU + len(out)
blob = bytearray(struct.pack('<HH', 4 + 8 * len(ents), len(ents)) + b''.join(ents))
sub_at = len(blob); blob += sub[:0xC] + bytes(8 * len(newparts))
while len(blob) % 4: blob.append(0)
for i, p in enumerate(newparts):
    pl = bytes(p) + b'\0' * (-len(p) % 4)
    struct.pack_into('<H', blob, sub_at + 0xC + 8 * i, len(blob))
    blob += struct.pack('<I', len(pl) << 8) + pl
out.extend(blob)
# VRAM halfword that tells the two sets apart (layer A char block from the BG setting at 0x08069904)
cbA = (struct.unpack('<I', R.rom[0x69904:0x69908])[0] >> 2) & 3
chk = None
for k in range(min(len(onlyA[0]), len(onlyA[1]))):
    a, b = pixels[len(shA) + k], pixels[len(shA) + len(onlyA[0]) + k]
    for h in range(16):
        va, vb = struct.unpack('<H', a[2 * h:2 * h + 2])[0], struct.unpack('<H', b[2 * h:2 * h + 2])[0]
        if va != vb: chk = (0x06000000 + cbA * 0x4000 + (len(shA) + k) * 32 + 2 * h, va, vb); break
    if chk: break
assert chk
tab = struct.pack('<4sI', b'BMAP', 1) + struct.pack('<IiIHHIIIII', SLOT, SPLIT * 32, chk[0], chk[1], chk[2], pTS, pL[0][0], pL[0][1], pL[1][0], pL[1][1])
out[0:len(tab)] = tab

entry = R.entry(SLOT)
entry[0], entry[1], entry[2], entry[3] = pA0, pA1, pMapA, pMetaA
entry[4] = entry[5] = 0                       # no extra metatile parts
entry[6], entry[7] = pMapB, pMetaB
entry[8] = entry[9] = 0
entry[10], entry[11] = pDefs, pCol
entry[12] = entry[13] = 0                     # no extra walking data
entry[14] = pTS
obj = list(struct.unpack('<3I', R.rom[OBJECTS - 0x08000000 + 12 * SLOT:][:12])); obj[1] = pBlob
os.makedirs(out_dir, exist_ok=True)
open(os.path.join(out_dir, 'join.bin'), 'wb').write(out)
tables = struct.pack('<I', LEVELS - 0x08000000 + 0x4C * SLOT) + struct.pack('<19I', *entry) + struct.pack('<I', OBJECTS - 0x08000000 + 12 * SLOT) + struct.pack('<3I', *obj)
open(os.path.join(out_dir, 'tables.bin'), 'wb').write(tables)
info = dict(slot=SLOT, base=BASE, size=len(out), cells=[W, H], tower_base_at_cells=[TX, 0], flooded_field_at_cells=[0, FY], split_y_px=SPLIT * 32,
            tilesA=nA, tilesB=nB, sharedA=len(shA), sharedB=len(shB), metasA=len(metaA), metasB=len(metaB), walk_defs=len(defs),
            entries=[struct.unpack('<HH', e[:4]) + (e[4:].hex(),) for e in ents], tb_items=len(tb_items), check=[hex(c) for c in chk],
            level_entry=[hex(x) for x in entry], object_entry=[hex(x) for x in obj])
json.dump(info, open(os.path.join(out_dir, 'join.json'), 'w'), indent=1)
print(json.dumps(info))
