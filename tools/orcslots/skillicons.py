"""Frodo's skill icons (Jordan, 2026-11-09): Bolt Trap (was Snare) shows a small crossbow, Quick Drop (was
Galadriel's Cloak) three tiny crossbows. Each icon is 32 x 24 pixels (12 raw 4bpp tiles, 4 x 3, BG palette 4 of the
Skills page) in Frodo's icon records (pointer table 0x0828773C, 4-byte header + 0x180 bytes; Sam has his own copies).
The game's frame is kept: the inside of the circle (flood fill from the centre over the picture's colours) is cleared
and the crossbows are drawn into it with the icons' own greens."""
import hashlib

ICONS = {0x785DB0: "5b88f3ca", 0x785F34: "0da32060"}   # Snare, Galadriel's Cloak: offset -> sha1 prefix of the original
C = {'W': 1, 'L': 8, 'M': 9, 'N': 10, 'D': 11, 'E': 12, 'K': 13}
BIG = [
    ".........W.........",
    "........WLW........",
    ".........L.........",
    ".......MNLNM.......",
    "...MMNNNNLNNNNMM...",
    ".MNNDDDDDLDDDDDNNM.",
    "MND.....NLN.....DNM",
    "MD.W....NLN....W.DM",
    "D...W...NLN...W...D",
    ".....W..NLN..W.....",
    "......W.NLN.W......",
    ".......WMLMW.......",
    "........MLM........",
    ".......DNMND.......",
    "......DNNMNND......",
    "......DNNMNND......",
    ".......DNMND.......",
    ".......DNMND.......",
    "........DND........",
]
TINY = [
    "...W...",
    "..WLW..",
    ".MNLNM.",
    "MNDLDNM",
    "D.WLW.D",
    "...M...",
    "..DND..",
    "..DND..",
    "...D...",
]
SPRITES = {0x785DB0: [(BIG, 7, 3)], 0x785F34: [(TINY, 6, 5), (TINY, 19, 5), (TINY, 12, 13)]}


def grid(b):
    return [[(b[((y // 8) * 4 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2] >> (4 * (x & 1))) & 15 for x in range(32)]
            for y in range(24)]


def pack(g):
    out = bytearray(0x180)
    for y in range(24):
        for x in range(32):
            out[((y // 8) * 4 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2] |= g[y][x] << (4 * (x & 1))
    return bytes(out)


def interior(g):
    ok, seen, st = {0, 1, 8, 9, 10, 11, 12, 13}, set(), [(16, 12)]
    while st:
        x, y = st.pop()
        if (x, y) in seen or not (0 <= x < 32 and 0 <= y < 24) or g[y][x] not in ok:
            continue
        seen.add((x, y))
        st += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return seen


def icons(rom):
    """[(offset, new bytes)]; the original icons are recognised by their hash (already patched: kept)"""
    out = []
    for off, h in ICONS.items():
        old = bytes(rom[off:off + 0x180])
        if hashlib.sha1(old).hexdigest()[:8] != h:
            continue
        g = grid(old)
        m = interior(g)
        for x, y in m:
            g[y][x] = 0
        for spr, x0, y0 in SPRITES[off]:
            for dy, row in enumerate(spr):
                for dx, ch in enumerate(row):
                    if ch != '.' and (x0 + dx, y0 + dy) in m:
                        g[y0 + dy][x0 + dx] = C[ch]
        out.append((off, pack(g)))
    return out
