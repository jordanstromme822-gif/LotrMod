"""Sample map piece: a crop of a captured screen, repainted at 4x.
usage: sample_tile.py capdir x y w h out.png   (capdir has before.png + dump.bin)"""
import sys, numpy as np
from PIL import Image
from oklab import from555, to_lch
from plan import recolor, auto_material
from paint4x import paint
cap, x, y, w, h, outp = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
D = open(cap + '/dump.bin', 'rb').read()
pal = [from555(int(v)) for v in np.frombuffer(D[0x18000:0x18400], '<u2')]
env_t = lambda L: (L - 0.12) / (0.78 - 0.12)
colors = {}
for b in (11, 12, 13, 14, 15):
    for i in range(1, 16):
        c = pal[b*16+i]
        if c != (0, 0, 0) or True: colors.setdefault(c, len(colors))
img = np.array(Image.open(cap + '/before.png').convert('RGB'))[y:y+h, x:x+w]
inv = {v: k for k, v in colors.items()}
idx = np.full((h, w), -1)
for c, k in colors.items(): idx[(img == c).all(-1)] = k
# pixels not from the stone palettes (rain, sprites): take the nearest stone colour
miss = idx < 0
if miss.any():
    keys = np.array(list(colors.keys())); 
    d = ((img[miss][:, None, :].astype(int) - keys[None]) ** 2).sum(-1)
    idx[miss] = np.array(list(colors.values()))[d.argmin(1)]
table = {k: (auto_material(c), min(1, max(0, env_t(to_lch(c)[0])))) for c, k in colors.items()}
a = Image.fromarray(img).resize((w*4, h*4), Image.NEAREST)
flat = np.zeros((h, w, 3), np.uint8)
for k in np.unique(idx): flat[idx == k] = recolor(inv[k], table[k][0], env_t)
b = Image.fromarray(flat).resize((w*4, h*4), Image.NEAREST)
c = Image.fromarray(paint(idx, table, sprite=False, light=0.10, soften=0.3, sigma=1.4)).convert('RGB')
sheet = Image.new('RGB', (w*4*3 + 80, h*4 + 40), (58, 50, 60))
for k, im in enumerate((a, b, c)): sheet.paste(im, (20 + k*(w*4+20), 20))
sheet.save(outp)
