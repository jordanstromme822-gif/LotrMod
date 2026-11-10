"""Make the colour-plan sample board. usage: board.py capdir hero.png tile.png out.png"""
import sys
from PIL import Image, ImageDraw, ImageFont
from plan import RAMPS
cap, herop, tilep, outp = sys.argv[1:5]
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'
f1, f2, f3 = ImageFont.truetype(F % '-Bold', 30), ImageFont.truetype(F % '-Bold', 19), ImageFont.truetype(F % '', 16)
BG, FG, MUT = (34, 30, 38), (236, 230, 220), (170, 160, 170)
W = 1500
before = Image.open(cap + '/before.png').convert('RGB').crop((0, 0, 240, 136)).resize((720, 408), Image.NEAREST)
after = Image.open(cap + '/after.png').convert('RGB').crop((0, 0, 240, 136)).resize((720, 408), Image.NEAREST)
hero = Image.open(herop); tile = Image.open(tilep)
hero = hero.resize((hero.width * 2, hero.height * 2), Image.NEAREST)
rows = [n for n in RAMPS]
H = 120 + 450 + 60 + hero.height + 60 + tile.height + 60 + 40 * ((len(rows) + 1) // 2) + 60
im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
d.text((30, 24), 'Colour plan: first samples (Helm\'s Deep + Aragorn)', FG, f1)
d.text((30, 66), 'Same game pixels, new colours. Warm light, cool violet shadows, heroes brighter and more saturated than the walls.', MUT, f3)
y = 110
d.text((30, y), 'Before', FG, f2); d.text((770, y), 'After: palette pass (works on every frame at once)', FG, f2); y += 30
im.paste(before, (30, y)); im.paste(after, (770, y)); y += 430
d.text((30, y), 'Sample hero: original  |  new palette  |  4x repaint with the ramps (first automatic pass)', FG, f2); y += 30
im.paste(hero, (30, y)); y += hero.height + 20
d.text((30, y), 'Sample map piece: original  |  new palette  |  4x repaint (stone bevels lit from top-left)', FG, f2); y += 30
im.paste(tile, (30, y)); y += tile.height + 30
d.text((30, y), 'Ramps (dark to light; each slides cool in shadow, warm in light)', FG, f2); y += 34
for k, n in enumerate(rows):
    x0 = 30 + (k % 2) * 730; yy = y + (k // 2) * 40
    d.text((x0, yy + 6), n, MUT, f3)
    for s in range(9):
        c = tuple(int(v) for v in RAMPS[n](s / 8))
        d.rectangle((x0 + 130 + s * 62, yy, x0 + 130 + s * 62 + 58, yy + 32), fill=c)
im.save(outp, optimize=True); print(im.size)
