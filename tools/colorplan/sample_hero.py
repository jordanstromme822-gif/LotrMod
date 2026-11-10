"""Sample hero: Aragorn from a Helm's Deep capture. usage: sample_hero.py capdir out.png"""
import sys, numpy as np
from PIL import Image
sys.argv, cap, outp = sys.argv[:1], sys.argv[1], sys.argv[2]
from oklab import from555, to_lch, gba
from plan import recolor
from paint4x import paint
exec(open(__file__.replace('sample_hero.py', 'oamread.py')).read())
D = open(cap + '/dump.bin', 'rb').read()
spr = [s for s in sprites(D) if s['bank'] == 0 and s['prio'] == 2]
x0 = min(s['x'] for s in spr); y0 = min(s['y'] for s in spr)
W = max(s['x'] + s['w'] for s in spr) - x0; H = max(s['y'] + s['h'] for s in spr) - y0
idx = np.full((H, W), -1)
for s in sorted(spr, key=lambda s: -s['i']):
    sub = idx[s['y']-y0:s['y']-y0+s['h'], s['x']-x0:s['x']-x0+s['w']]
    sub[s['img'] > 0] = s['img'][s['img'] > 0]
pal = [from555(int(v)) for v in np.frombuffer(D[0x18200:0x18220], '<u2')]
TAG = {1:'steel',2:'steel',3:'steel',4:'steel',5:'steel',6:'steel',7:'ranger',8:'ranger',9:'steel',
       10:'skin',11:'skin',12:'skin',13:'skin',14:'leather',15:'leather'}
hero_t = lambda L: (L - 0.08) / (0.92 - 0.08)
table = {i: (m, min(1, max(0, hero_t(to_lch(pal[i])[0])))) for i, m in TAG.items()}
def flat(colors):
    im = np.zeros((H, W, 4), np.uint8)
    for i in range(1, 16):
        im[idx == i, :3] = colors[i]; im[idx == i, 3] = 255
    return Image.fromarray(im).resize((W*4, H*4), Image.NEAREST)
a = flat(pal)
b = flat([None] + [recolor(pal[i], TAG[i], hero_t) for i in range(1, 16)])
c = Image.fromarray(paint(idx, table, norim=(5, 6)))
bg = (58, 50, 60)
sheet = Image.new('RGB', (W*4*3 + 80, H*4 + 40), bg)
for k, im in enumerate((a, b, c)): sheet.paste(im, (20 + k*(W*4+20), 20), im)
sheet.save(outp); print(W, H)
