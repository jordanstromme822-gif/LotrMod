"""Hero palettes: each hero's game palette tagged by material, recoloured with the ramps.
usage: heroes.py capdir_prefix out.png     (captures capdir_prefix0..5 from heroes_cap order)
Each hero keeps a 60/30/10 split: one dominant material, one secondary, a small accent;
all heroes share the same light (warm) and the same darkest shadow colour (violet)."""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
from heroes_cap import hero, NAMES
from oklab import to_lch, gba
from plan import recolor, RAMPS
from paint4x import paint

def T(s):  # "123:steel 7:ranger" -> {1:'steel',...}
    out = {}
    for part in s.split():
        keys, m = part.split(':')
        for c in keys: out[int(c, 16)] = m
    return out
TAGS = {
    'aragorn': T('123456:steel 78:ranger 9:steel abcd:skin ef:leather'),
    'gandalf': T('12:skin 345678:white-robe 9:shadow abcde:silver f:shadow'),
    'eowyn':   T('123:blonde 45:linen 678:skin 9:leather ade:wine bc:rohan-green f:shadow'),
    'gimli':   T('12:gold 34567:rust 89:skin abc:leather de:steel f:shadow'),
    'frodo':   T('123:skin 4:leather 567:rust 8ab:leather 9:leather c:shadow def:elf-cloak'),
    'legolas': T('1:skin 234:blonde 5678:elf-green 9a:silver be:elf-green cd:elf-cloak f:shadow'),
}
SHARED = T('123:elf-green 456:gold 789:ranger abc:rust def:steel')   # OBJ palette 2: weapons/effects
hero_t = lambda L: min(1, max(0, (L - 0.08) / (0.92 - 0.08)))

def build(D, name):
    idx, pal = hero(D)
    tags = {i: m for i, m in TAGS[name].items()}
    tags.update({32 + i: m for i, m in SHARED.items()})
    used = [v for v in np.unique(idx) if v >= 0]
    table = {v: (tags.get(v % 16 if v < 16 else v, 'steel'), hero_t(to_lch(pal[v])[0])) for v in used}
    new = {v: gba(RAMPS[table[v][0]](table[v][1]))[0] for v in used}
    return idx, pal, table, new

def flat(idx, colors, scale=6):
    H, W = idx.shape; im = np.zeros((H, W, 4), np.uint8)
    for v, c in colors.items(): im[idx == v, :3] = c; im[idx == v, 3] = 255
    return Image.fromarray(im).resize((W*scale, H*scale), Image.NEAREST)

if __name__ == '__main__':
    pre, outp = sys.argv[1], sys.argv[2]
    F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
    f1, f2, f3 = ImageFont.truetype(F % '-Bold', 30), ImageFont.truetype(F % '-Bold', 20), ImageFont.truetype(F % '', 15)
    rows = []
    for k, n in enumerate(NAMES):
        D = open(f'{pre}{k}/dump.bin', 'rb').read()
        idx, pal, table, new = build(D, n)
        shadow_ids = tuple(v for v, (m, _) in table.items() if m == 'shadow')
        a = flat(idx, {v: pal[v] for v in table}); b = flat(idx, new)
        c = Image.fromarray(paint(idx, table, norim=shadow_ids)); c = c.resize((c.width*3//2, c.height*3//2), Image.NEAREST)
        mats = []
        for v, (m, _) in sorted(table.items()):
            if m not in mats and m != 'shadow' and v < 16: mats.append(m)
        rows.append((n, a, b, c, mats))
    cw = max(r[1].width for r in rows) + 30
    W = 40 + cw * 3 + 470; H = 110 + sum(max(r[1].height + 30, 200) + 30 for r in rows)
    bgc = tuple(int(x) for x in RAMPS['stone'](0.45))
    im = Image.new('RGB', (W, H), (34, 30, 38)); d = ImageDraw.Draw(im)
    d.text((30, 20), 'Heroes: original  |  new palette  |  4x repaint', (236, 230, 220), f1)
    d.text((30, 62), 'Shared warm light and one violet shadow for everyone; each hero gets a dominant colour, a second one and a small accent.', (170, 160, 170), f3)
    y = 100
    for n, a, b, c, mats in rows:
        rh = max(a.height + 30, 200)
        d.rectangle((30, y, 30 + cw*3, y + rh), fill=bgc)
        for j, p in enumerate((a, b, c)): im.paste(p, (30 + j*cw + 15, y + 15), p)
        x = 60 + cw*3
        d.text((x, y + 8), n.capitalize(), (236, 230, 220), f2)
        for j, m in enumerate(mats):
            yy = y + 40 + j*24
            for s in range(7): d.rectangle((x + s*30, yy, x + s*30 + 27, yy + 20), fill=tuple(int(v) for v in RAMPS[m](s/6)))
            d.text((x + 220, yy + 2), m, (170, 160, 170), f3)
        y += rh + 30
    im.save(outp, optimize=True); print(im.size)
