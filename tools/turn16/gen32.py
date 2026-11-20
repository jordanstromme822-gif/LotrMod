#!/usr/bin/env python3
"""32-facing in-between pictures for every hero and enemy (v209, Jordan 2026-11-20: "give all characters and enemies
360 points of motion instead of 16 like you did to the traps").

  python3 -I gen32.py <original ROM .gba> <out turn32.bin> [workers]

The game draws 5 directions (up, up-right, right, down-right, down; the left side is mirrored). v176/v177 added one
in-between picture per gap (16 facings). This makes three per gap, at 1/4, 1/2 and 3/4 of the way (32 facings, 11.25
degrees on the ground, like the v208 Bolt Trap). The 1/2 picture is made exactly as before (morph1(A, B, 0.5)); 1/4 is
A moved a quarter of the way toward B, 3/4 is B moved a quarter of the way back toward A, so each is one body.

ROM layout (CPU addresses; the page puts the chunks into the built game past 16 MB):
  0x09000000  heroes: 8 x {game's anim table, ours for 1/4, ours for 1/2, ours for 3/4} (16 bytes each);
              each of ours is a copy of the game's table whose kinds 4 (stand) and 6 (walk) point at 4 entries
              (one per gap), so 0x08000D58 is called with a direction 0-3 exactly as in v176.
  0x09000080  u32: address of SP[82][2] (enemy species s, walk / stand -> our 12 entries, entry 3 * gap + sub; 0 = none)
  then hero and enemy pictures, filling 0x09000000-0x09500000 and then 0x09610000-0x0A000000 (0x09500000-0x09610000
  holds the Siege map and Gandalf's table copy).
Output file: b'T32\\0', u32 chunk count, then per chunk {u32 file offset, u32 length, bytes}.
Made from the game's own art: keep it out of the repository.
"""
import struct, sys, os, numpy as np
from multiprocessing import Pool
ROMPATH, OUT = sys.argv[1], sys.argv[2]
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else os.cpu_count()
sys.argv = [sys.argv[0], ROMPATH]
G = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gen16all.py')
exec(open(G).read().split("if __name__")[0])

REGIONS = [(0x09000000, 0x09500000), (0x09610000, 0x0A000000)]
ET = 0x08056820
SUBS = (0.25, 0.5, 0.75)

def inbetween(A, B, C, t):
    if t <= 0.5: q = clean(morph1(A, B, C, t))
    else: q = clean(morph1(B, A, C, 1 - t))
    return q

def setframes(p, d):
    tiles, hdr, _ = struct.unpack_from('<III', ROM, p - 0x8000000 + 16 * d); n = u8(hdr + 6); out = []
    for f in range(n):
        rec = hdr + 0xC + u16(hdr + 0xC + 2 * f)
        fl = u8(rec); np_ = fl & 0x1f; w, h = u8(rec + 2), u8(rec + 3); toff = u16(rec + 4); nb = u16(rec + 6)
        po = rec + 8 + 6 * u8(hdr + 0xB) + 2 * u8(hdr + 0xA); parts = []
        for k in range(np_):
            v = struct.unpack_from('<I', ROM, po + 4 * k - 0x8000000)[0]
            x = v & 0x1ff; x -= 0x200 if x & 0x100 else 0
            y = (v >> 9) & 0x1ff; y -= 0x200 if y & 0x100 else 0
            parts.append((x, y, (v >> 20) & 3, (v >> 18) & 3, v >> 22))
        out.append(dict(rec=rec, fl=fl, w=w, h=h, toff=toff, nb=nb, parts=parts, src=tiles + toff))
    return out

EIDX = np.arange(16)
ECOST = np.where(abs(EIDX[:, None] - EIDX[None, :]) <= 2, 1.0 + abs(EIDX[:, None] - EIDX[None, :]) * 0.8, np.inf)
np.fill_diagonal(ECOST, 0.0)

def set_pics(p, F, C):
    """pictures[gap][sub] = list of frames, for the 5-entry set at p (frames F[d])."""
    R = [[render(f, decode(f)) for f in F[d]] for d in range(5)]
    out = []
    for j in range(4):
        n = min(len(F[j]), len(F[j + 1])); g = []
        for t in SUBS:
            pics = [inbetween(R[j][i], R[j + 1][i], C, t) for i in range(n)]
            g.append([q if q else (R[j][i] if t <= 0.5 else R[j + 1][i]) for i, q in enumerate(pics)])
        out.append(g)
    return out

def entry_block(out, base, ent_off, p, F, pics, j, sub_i, hold_bytes):
    """append one entry's tiles + frame header at the end of out (absolute addresses from base), write the entry."""
    def here(): return base + len(out)
    def align():
        while len(out) % 4: out.append(0)
    tiles_, hdr_src, _ = struct.unpack_from('<III', ROM, p - 0x8000000 + 16 * j)
    frames_ = pics[j][sub_i]; n = len(frames_)
    packed = [pack(q) for q in frames_]
    align(); tile_addr = here(); toffs = []
    for (tl, enc, w, hh) in packed: toffs.append(here() - tile_addr); out.extend(tl)
    align(); hdr_addr = here()
    hd = bytearray(ROM[hdr_src - 0x8000000:hdr_src - 0x8000000 + 12]); nb_ = u8(hdr_src + 0xB)
    hd[6] = n; hd[0xA] = 0; hd[0xB] = 1
    hd[8:10] = struct.pack('<H', max(len(q[0]) for q in packed))
    recs = []
    for i, (tl, enc, w, hh) in enumerate(packed):
        src = F[j][i]['rec']; hb = ROM[src + 8 - 0x8000000:src + 14 - 0x8000000] if nb_ >= 1 else b'\0' * 6
        assert toffs[i] < 0x10000
        recs.append(bytes([len(enc), 0, w, hh]) + struct.pack('<HH', toffs[i], len(tl)) + hb + b''.join(enc))
    offs = []; body = b''
    for r in recs:
        offs.append(2 * n + len(body)); body += r
        while len(body) % 2: body += b'\0'
    out.extend(bytes(hd) + b''.join(struct.pack('<H', o) for o in offs) + body)
    out[ent_off:ent_off + 16] = struct.pack('<III', tile_addr, hdr_addr, 0) + hold_bytes

# ---- heroes ----
def hero_job(h):
    T = u32(HEROTBL + 4 * h); C = colcost(palette(h)); res = {}
    for k in KINDS:
        p = u32(T + 4 * k)
        F = [frames(T, k, d) for d in range(5)]
        res[k] = (p, F, set_pics(p, F, C))
    return h, T, res

def hero_block(base, T, res):
    out = bytearray(); nk = 0
    while 0x08000000 <= u32(T + 4 * nk) < 0x09000000 and nk < 64: nk += 1
    tbl = []; ents = {}
    for s in range(3):
        tbl.append(len(out)); out += b'\0' * (4 * nk)
    for s in range(3):
        for k in KINDS: ents[(s, k)] = len(out); out += b'\0' * 64
    for s in range(3):
        for k in KINDS:
            p, F, pics = res[k]
            for j in range(4):
                entry_block(out, base, ents[(s, k)] + 16 * j, p, F, pics, j, s, bytes([u8(p + 16 * j + 12), 0, 0, 0]))
    for s in range(3):
        for k in range(nk):
            a = base + ents[(s, k)] if k in KINDS else u32(T + 4 * k)
            out[tbl[s] + 4 * k:tbl[s] + 4 * k + 4] = struct.pack('<I', a)
    while len(out) % 4: out.append(0)
    return out, [base + t for t in tbl]

# ---- enemies ----
def enemy_job(p):
    F = [setframes(p, d) for d in range(5)]
    return p, F, set_pics(p, F, ECOST)

def enemy_block(base, p, F, pics):
    out = bytearray(b'\0' * 192)
    for j in range(4):
        for s in range(3):
            entry_block(out, base, 16 * (3 * j + s), p, F, pics, j, s, ROM[p - 0x8000000 + 16 * j + 12:p - 0x8000000 + 16 * j + 16])
    while len(out) % 4: out.append(0)
    return out

class Space:
    def __init__(self): self.r = 0; self.at = REGIONS[0][0]; self.data = {REGIONS[0][0]: bytearray(), REGIONS[1][0]: bytearray()}
    def place(self, make):
        blk = make(self.at)
        if self.at + len(blk[0] if isinstance(blk, tuple) else blk) > REGIONS[self.r][1]:
            assert self.r == 0, 'out of ROM space'
            self.r = 1; self.at = REGIONS[1][0]; blk = make(self.at)
            assert self.at + len(blk[0] if isinstance(blk, tuple) else blk) <= REGIONS[1][1], 'out of ROM space'
        b = blk[0] if isinstance(blk, tuple) else blk
        self.data[REGIONS[self.r][0]] += b; at = self.at; self.at += len(b)
        return at, blk

if __name__ == '__main__':
    sets = []
    for s in range(82):
        for k in (0, 1):
            p = u32(ET + 24 * s + 4 * k)
            if 0x08000000 <= p < 0x09000000 and p not in sets: sets.append(p)
    sp = Space()
    head = bytearray(0x84); sp.data[REGIONS[0][0]] += head; sp.at += len(head)
    with Pool(WORKERS) as pool:
        heroes = sorted(pool.map(hero_job, range(8)))
        print('hero pictures done', flush=True)
        enemies = pool.map(enemy_job, sets)
        print('enemy pictures done', len(enemies), flush=True)
    idx = bytearray()
    for h, T, res in heroes:
        at, (blk, tbls) = sp.place(lambda base: hero_block(base, T, res))
        idx += struct.pack('<IIII', T, *tbls); print('hero', h, hex(at), len(blk), flush=True)
    M = {}
    for p, F, pics in enemies:
        at, blk = sp.place(lambda base: enemy_block(base, p, F, pics)); M[p] = at
    print('enemies end', hex(sp.at), flush=True)
    sptab = bytearray()
    for s in range(82):
        for k in range(2): sptab += struct.pack('<I', M.get(u32(ET + 24 * s + 4 * k), 0))
    at, _ = sp.place(lambda base: sptab)
    a0 = sp.data[REGIONS[0][0]]
    a0[0:0x80] = idx; a0[0x80:0x84] = struct.pack('<I', at)
    chunks = [(b - 0x08000000, d) for b, d in sp.data.items() if d]
    with open(OUT, 'wb') as f:
        f.write(b'T32\0' + struct.pack('<I', len(chunks)))
        for off, d in chunks: f.write(struct.pack('<II', off, len(d)) + bytes(d))
    print('chunks', [(hex(o), len(d)) for o, d in chunks])
