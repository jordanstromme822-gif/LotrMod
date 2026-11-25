"""Pack a region's ground (region.py's region.pkl) into one level slot for the big-map engine (tools/bigmap).

python3 tools/region/pack.py ROM REGION_DIR PACK.json OUT_DIR

The region is split into horizontal zones (PACK.json "zones", in 32 px cell rows). Each zone gets its own VRAM tile
set; the engine (bm_frame, 'BMP2' table) loads the set of the zone the local hero stands in. A zone's set holds every
tile within "margin" cells above and below it, so the screen never shows a tile the set lacks. Every tile keeps one
VRAM slot in all sets (slots are shared between tiles that never meet in one set), so one map works for all zones.

Objects: the joined Flooded Field + Tower Base block keeps what tools/join/level.py kept (Flooded Field's parts, Tower
Base's orcs, enemies, ladders and door to the tower levels) plus Tower Base's tunnel door (to the Orthanc Tunnel); the
Campsite block adds its own props and doors; PACK.json 'orc_bands' adds orc spawns along the roads.

OUT_DIR gets region.bin (for ROM BASE = 0x1C80000, CPU 0x09C80000, past the 32-facing pictures that end at 0x1C22FBC, starts with the BMP2 table), tables.bin (level and
object table entries for the slot) and region.json.
"""
import json, os, pickle, struct, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'siege')); sys.path.insert(0, os.path.join(HERE, '..', 'join'))
from romlib import Rom, LEVELS, OBJECTS
from spawns import parse_groups, build_groups

rom_path, rdir, cfg_path, out_dir = sys.argv[1:5]
P = json.load(open(cfg_path))
BASE = int(P.get('base', '0x1C80000'), 16)
CPU = 0x08000000 + BASE
SLOT, FF, TB, CAMP = P['slot'], P['flooded_field'], P['tower_base'], P['campsite']
BLANK = 0
R = Rom(rom_path)
reg = pickle.load(open(os.path.join(rdir, 'region.pkl'), 'rb'))
GA, GB, GC, W, H = reg['GA'], reg['GB'], reg['GC'], reg['W'], reg['H']
blocks = {b['name']: b for b in reg['blocks']}
jb, cb = blocks[P['join_block']], blocks[P['campsite_block']]
TBX, TBY = (jb['x'] + P['join_TX']) * 32, jb['y'] * 32            # Tower Base's (0,0) in region px
FFX, FFY = jb['x'] * 32, (jb['y'] + P['join_FY']) * 32            # Flooded Field's
CPX, CPY = cb['x'] * 32, cb['y'] * 32                             # Campsite's
ZONES, M = P['zones'], P['margin']
assert ZONES[0][0] == 0 and ZONES[-1][1] == H and all(a[1] == b[0] for a, b in zip(ZONES, ZONES[1:]))

# ---- tile sets and shared slots -------------------------------------------------------------------------------
def rows_tiles(G, y0, y1):
    y0, y1 = max(0, y0), min(H, y1)
    return {t for r in G[y0 * 4:y1 * 4] for t, f in r}
setsA = [rows_tiles(GA, a - M, b + M) for a, b in ZONES]
setsB = [rows_tiles(GB, a - M, b + M) | {BLANK} for a, b in ZONES]

def colour(sets, first=None):
    """one slot per tile; tiles that share a set get different slots (greedy, smallest free slot)"""
    member = collections.defaultdict(set)
    for s, ts in enumerate(sets):
        for t in ts: member[t].add(s)
    used = [dict() for _ in sets]            # set -> {slot: tile}
    slot = {}
    order = sorted(member, key=lambda t: (t != first, min(member[t]), -len(member[t]), (0, t, '') if isinstance(t, int) else (1, 0, str(t))))
    for t in order:
        k = 0
        while any(k in used[s] for s in member[t]): k += 1
        slot[t] = k
        for s in member[t]: used[s][k] = t
    return slot, used
slotA, usedA = colour(setsA)
slotB, usedB = colour(setsB, BLANK)
assert slotB[BLANK] == 0
nA = [max(u) + 1 for u in usedA]; nB = [max(u) + 1 for u in usedB]
print('zones', ZONES, 'tiles A', [len(s) for s in setsA], 'slots', nA, ' B', [len(s) for s in setsB], 'slots', nB)
assert max(nA) <= P.get('max_a', 944) and max(nB) <= 512, (nA, nB)
# zone markers: when some zone has no layer A tile whose VRAM halfword tells it apart from every other zone (a zone
# whose tiles all also sit in its neighbours), every zone gets one extra A slot past the last, holding a tile drawn
# only for this: all pixels = zone number + 1. The map never shows it; bm_frame checks it.
NZ = len(ZONES)
def natural_check(s):
    for k in range(min(nA)):
        ts = [usedA[t].get(k) for t in range(NZ)]
        if ts[s] is not None and all(ts[t] is not None and ts[t] != ts[s] for t in range(NZ) if t != s): return True
    return False
MARK = None
if not all(natural_check(s) for s in range(NZ)):
    MARK = max(nA)
    assert MARK + 1 <= P.get('max_a', 944), 'no room for zone markers'
    for s in range(NZ):
        slotA[('mark', s)] = MARK; usedA[s][MARK] = ('mark', s)
    nA = [MARK + 1] * NZ
    print('zone markers at A slot', MARK)
# custom tileset: A tiles by slot, then B tiles by slot, so every set's list ascends
skey = lambda t: (0, t, 0) if isinstance(t, int) else (1, t[1], 0)
ordA = sorted(slotA, key=lambda t: (slotA[t], skey(t))); ordB = sorted(slotB, key=lambda t: (slotB[t], t))
idxA = {t: i for i, t in enumerate(ordA)}; idxB = {t: len(ordA) + i for i, t in enumerate(ordB)}
firstA = {}; firstB = {}
for t in ordA: firstA.setdefault(slotA[t], idxA[t])
for t in ordB: firstB.setdefault(slotB[t], idxB[t])
def lists(used, n, idx, first):
    return [[idx[u[k]] if k in u else first[k] for k in range(n[s])] for s, u in enumerate(used)]
listsA = lists(usedA, nA, idxA, firstA); listsB = lists(usedB, nB, idxB, firstB)
for l in listsA + listsB: assert all(a < b for a, b in zip(l, l[1:]))
uniq = sorted(t for t in set(ordA) | set(ordB) if isinstance(t, int))
pix_of = dict(zip(uniq, R.tiles(R.entry(FF)[14], uniq)))
for s_ in range(NZ): pix_of[('mark', s_)] = bytes([((s_ + 1) & 15) * 0x11]) * 32
for t in ordA:                                # tools/region/mountains.py's key tile: every pixel one colour index
    if isinstance(t, tuple) and t[0] == 'key': pix_of[t] = bytes([(t[1] & 15) * 0x11]) * 32
order = ordA + ordB
pixels = [pix_of[t] for t in order]

# ---- metatiles, maps, walking data --------------------------------------------------------------------------------
def metas(G, slot, first):
    table = [first] if first else []; idx = {m: i for i, m in enumerate(table)}; cells = []
    for cy in range(H):
        for cx in range(W):
            m = tuple(slot[G[cy * 4 + k // 4][cx * 4 + k % 4][0]] | G[cy * 4 + k // 4][cx * 4 + k % 4][1] for k in range(16))
            if m not in idx: idx[m] = len(table); table.append(m)
            cells.append(idx[m])
    return table, cells
metaA, cellsA = metas(GA, slotA, None)
metaB, cellsB = metas(GB, slotB, tuple([0] * 16))
cdefs = []
for cy in range(H):
    for cx in range(W):
        cdefs.append(bytes(GC[cy * 4 + k // 4][cx * 4 + k % 4] for k in range(16)))
use = collections.Counter(cdefs)
# walking defs over the engine's 1024: the rarest ones take their closest common def (walkable vs blocked weighs most)
MAXD = P.get('max_defs', 1000)
def dist(a, b):
    return sum((4 if (x == 0) != (y == 0) else 1) for x, y in zip(a, b) if x != y)
remap = {}
keep = sorted(use, key=lambda d: -use[d])
if len(keep) > MAXD:
    common, rare = keep[:MAXD], keep[MAXD:]
    full = bytes([1] * 16)
    if full not in common: common = [full] + common[:-1]; rare = [d for d in keep if d not in set(common)]
    for d in rare: remap[d] = min(common, key=lambda c: (dist(d, c), -use[c]))
changed = sum(use[d] * sum(x != y for x, y in zip(d, remap[d])) for d in remap)
cdefs = [remap.get(d, d) for d in cdefs]
defs = [bytes([1] * 16)]; didx = {defs[0]: 0}; cellsC = []
for d in cdefs:
    if d not in didx: didx[d] = len(defs); defs.append(d)
    cellsC.append(didx[d])
print('metatiles A', len(metaA), 'B', len(metaB), 'walk defs', len(defs), 'remapped', len(remap), 'defs,', changed, '8px spots changed')
assert len(defs) <= 1024 and len(metaA) < 65536 and len(metaB) < 65536

# ---- objects -----------------------------------------------------------------------------------------------------
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
csub, cents, cparts = obj_parts(CAMP)
KEEP_TB = {0x1A, 0x0B, 0x08, 0x03}           # orc spawns, enemies, ladders/markers, the door to 57 (+ its 0x12 trigger below)
tb_items = [move(it, TBX, TBY) for g in split_part(tparts[1])[0] for it in g['items'] if it[0] in KEEP_TB]
tb_items += [move(it, TBX, TBY) for g in split_part(tparts[1])[0] for it in g['items'] if it[0] in (0x12, 0x02)]   # the door's trigger marker and frame
tun = [it for g in split_part(tparts[2])[0] for it in g['items'] if it[0] == 3 and it[0xB] == P['tunnel']]
def near(it, d, r=40):
    (x, y), (a, b) = struct.unpack('<HH', it[4:8]), struct.unpack('<HH', d[4:8]); return abs(x - a) <= r and abs(y - b) <= r
tb_items += [move(it, TBX, TBY) for it in tun]
tb_items += [move(it, TBX, TBY) for g in split_part(tparts[2])[0] for it in g['items'] if it[0] == 0x12 and any(near(it, d) for d in tun)]
KEEP_CAMP = set(P.get('campsite_types', [0x0B, 0x0C, 0x11, 0x12, 0x03]))
camp_groups = [dict(b1=g['b1'], items=[move(it, CPX, CPY) for it in g['items'] if it[0] in KEEP_CAMP]) for g in split_part(cparts[1])[0]]
camp_groups = [g for g in camp_groups if g['items']]
# orc bands placed for the story (PACK.json 'orc_bands': [[x, y, orcs], ...] region px): the game's own Isengard orc
# spawn record (type 0x1A, as Flooded Field's and Tower Base's: +8 orcs, +9 = 4), each moved to the nearest open,
# walkable spot off the roads within 96 px
road8 = reg.get('road')
def open_spot(x, y):
    best = None
    for dy in range(-12, 13):
        for dx in range(-12, 13):
            sx, sy = x // 8 + dx, y // 8 + dy
            if not (0 <= sy < len(GA) and 0 <= sx < len(GA[0])): continue
            if any(not GA[sy + j][sx + i][0] or (GC[sy + j][sx + i] & 7) or GB[sy + j][sx + i][0] or (road8 is not None and road8[sy + j, sx + i])
                   for j in (-1, 0, 1) for i in (-1, 0, 1) if 0 <= sy + j < len(GA) and 0 <= sx + i < len(GA[0])): continue
            d = dx * dx + dy * dy
            if best is None or d < best[0]: best = (d, sx * 8 + 4, sy * 8 + 4)
    assert best, ('no open spot near', x, y)
    return best[1:]
orc_bands = []
for x, y, n in P.get('orc_bands', []):
    bx, by = open_spot(x, y); orc_bands.append(struct.pack('<4sHHBBH', b'\x1a\0\0\0', bx, by, n, 4, 0))
# wolf packs (PACK.json 'wolves': [[x, y, n, mode], ...] region px): the game's own warg spawn record (type 0x22, as
# Anduin's and Dimholt's: +8 species 0 = warg (kind 48), +9 mode), n wargs spread round the nearest open spot. Only
# plain wargs: the great warg (+8 = 1, kind 49) draws with OBJ palette 11, which Isengard fills with the Uruk palette.
wolves = []
for x, y, n, mode in P.get('wolves', []):
    for k in range(n):
        dx, dy = [(0, 0), (40, 18), (-36, 24), (14, -34), (-20, -30), (44, -12)][k % 6]
        bx, by = open_spot(x + dx, y + dy); wolves.append(struct.pack('<4sHHBBH', b'\x22\0\0\0', bx, by, 0, mode, 0))
def merged(part):
    groups, paths, scripts, tail, cnt = split_part(part)
    out = []
    for g in groups:
        items = []
        for it in g['items']:
            if it[0] == 3 and it[0xB] == TB: continue                     # the door to Tower Base
            if it[0] == 0x12 and struct.unpack('<HH', it[4:8]) == (568, 9): continue   # its marker
            items.append(move(it, FFX, FFY))
        out.append(dict(b1=g['b1'], items=items))
    # into the first group (always live; later groups are switched on by the part's scripts)
    out[0]['items'] += tb_items + [it for g in camp_groups for it in g['items']] + orc_bands + wolves
    p = bytearray(8) + build_groups(out)
    o_paths = len(p); p += paths
    o_scripts = len(p); p += scripts
    o_tail = len(p); p += tail
    struct.pack_into('<HHHH', p, 0, o_paths, o_scripts, cnt, o_tail)
    return bytes(p)
newparts = [fparts[0]] + [merged(p) for p in fparts[1:]]
def shift(e, dx, dy):
    x, y = struct.unpack('<HH', e[:4]); return struct.pack('<HH', x + dx, y + dy) + e[4:]
ents = [shift(e, FFX, FFY) for e in fents]                     # entry 0: Flooded Field's (both players)
ents += [shift(e, TBX, TBY) for e in tents if e[4] == 1]       # entry 1: Tower Base's north entry
sub = bytes([fsub[0], 2, fsub[2], tsub[3]]) + bytes(fsub[3:8]) + b'\xff\xff\xff'    # as tools/join/level.py
assert len(sub) == 0xC

# ---- write -------------------------------------------------------------------------------------------------------
NZ = len(ZONES)
out = bytearray(8 + 0x20 * NZ)
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
pL = [(add_raw(lst(listsA[s])), add_raw(lst(listsB[s]))) for s in range(NZ)]
th = R.rom[R.entry(FF)[14] - 0x08000000:][:4]
nt = len(order); chunks = [(i, min(1024, nt - i)) for i in range(0, nt, 1024)]
hdr = bytearray(th[:4]); data_off = 4 + 8 * len(chunks)
for s, c in chunks: hdr += struct.pack('<HHI', 0, c, data_off + 32 * s)
while len(out) % 4: out.append(0)
pTS = CPU + len(out); out.extend(hdr + b''.join(pixels))
Z0 = P['first_zone']                          # the set the level loads with (the usual way in)
pA0 = add_blob(lst(listsA[Z0])); pA1 = add_blob(lst(listsB[Z0]))
pMapA = add_blob(struct.pack('<HH', W, H) + struct.pack('<%dH' % len(cellsA), *cellsA), 1)
pMetaA = add_blob(struct.pack('<I', len(metaA)) + b''.join(struct.pack('<16H', *m) for m in metaA), 1)
pMapB = add_blob(struct.pack('<HH', W, H) + struct.pack('<%dH' % len(cellsB), *cellsB), 1)
pMetaB = add_blob(struct.pack('<I', len(metaB)) + b''.join(struct.pack('<16H', *m) for m in metaB), 1)
pDefs = add_blob(b''.join(defs))
pCol = add_blob(struct.pack('<HH', len(defs), 0) + struct.pack('<%dH' % len(cellsC), *cellsC), 1)
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
# per zone: a layer A VRAM halfword whose value under this zone's set differs from its value under every other set
cbA = (struct.unpack('<I', R.rom[0x69904:0x69908])[0] >> 2) & 3
nmin = min(nA)
def hw(i, h): return struct.unpack('<H', pixels[i][2 * h:2 * h + 2])[0]
checks = []
for s in range(NZ):
    chk = None
    for k in range(nmin):
        for h in range(16):
            v = hw(listsA[s][k], h)
            if all(hw(listsA[t][k], h) != v for t in range(NZ) if t != s):
                chk = (0x06000000 + cbA * 0x4000 + k * 32 + 2 * h, v); break
        if chk: break
    if MARK is not None:                      # the marker slot: halfword 0 of zone s's marker tile
        chk = (0x06000000 + cbA * 0x4000 + MARK * 32, hw(listsA[s][MARK], 0))
    assert chk, s
    checks.append(chk)
tab = bytearray(b'BMP2' + struct.pack('<I', NZ))
for s, (a, b) in enumerate(ZONES):
    tab += struct.pack('<IiiIHHIII', SLOT, -0x8000 if s == 0 else a * 32, 0x7FFF if s == NZ - 1 else b * 32,
                       checks[s][0], checks[s][1], 0, pTS, pL[s][0], pL[s][1])
out[0:len(tab)] = tab

entry = R.entry(SLOT)
entry[0], entry[1], entry[2], entry[3] = pA0, pA1, pMapA, pMetaA
entry[4] = entry[5] = 0
entry[6], entry[7] = pMapB, pMetaB
entry[8] = entry[9] = 0
entry[10], entry[11] = pDefs, pCol
entry[12] = entry[13] = 0
entry[14] = pTS
obj = list(struct.unpack('<3I', R.rom[OBJECTS - 0x08000000 + 12 * SLOT:][:12])); obj[1] = pBlob
os.makedirs(out_dir, exist_ok=True)
open(os.path.join(out_dir, 'region.bin'), 'wb').write(out)
tables = struct.pack('<I', LEVELS - 0x08000000 + 0x4C * SLOT) + struct.pack('<19I', *entry) + struct.pack('<I', OBJECTS - 0x08000000 + 12 * SLOT) + struct.pack('<3I', *obj)
open(os.path.join(out_dir, 'tables.bin'), 'wb').write(tables)
info = dict(slot=SLOT, base=BASE, size=len(out), cells=[W, H], zones=ZONES, slotsA=nA, slotsB=nB, tilesA=len(ordA), tilesB=len(ordB),
            metasA=len(metaA), metasB=len(metaB), walk_defs=len(defs), defs_remapped=len(remap), spots_changed=changed,
            tower_base_px=[TBX, TBY], flooded_field_px=[FFX, FFY], campsite_px=[CPX, CPY],
            entries=[struct.unpack('<HH', e[:4]) + (e[4:].hex(),) for e in ents], tb_items=len(tb_items),
            camp_items=sum(len(g['items']) for g in camp_groups), orc_bands=[list(struct.unpack('<HHB', b[4:9])) for b in orc_bands], wolves=[list(struct.unpack('<HHB', b[4:9])) for b in wolves], checks=[[hex(a), hex(v)] for a, v in checks],
            doors=[[i, struct.unpack('<HH', it[4:8]), it[0xB], it[0xA]] for i, part in enumerate(newparts[1:], 1) for g in split_part(part)[0] for it in g['items'] if it[0] == 3],
            triggers=[[i, struct.unpack('<HH', it[4:8])] for i, part in enumerate(newparts[1:], 1) for g in split_part(part)[0] for it in g['items'] if it[0] == 0x12],
            level_entry=[hex(x) for x in entry], object_entry=[hex(x) for x in obj])
json.dump(info, open(os.path.join(out_dir, 'region.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in info.items() if k not in ('level_entry',)}))
