"""Recolour a captured scene by rewriting palette RAM and re-rendering it in mGBA.
usage: scene.py rom state outdir   (writes outdir/before.png, after.png)"""
import sys, subprocess, numpy as np, os
from PIL import Image
from plan import recolor, auto_material
from oklab import from555, gba, to_lch
rom, state, out = sys.argv[1:4]
D = open(os.path.join(out, 'dump.bin'), 'rb').read()
pal = [int(v) for v in np.frombuffer(D[0x18000:0x18400], '<u2')]
new = pal[:]
def env_t(L): return (L - 0.12) / (0.78 - 0.12)
def hero_t(L): return (L - 0.08) / (0.92 - 0.08)
# environment: BG palettes 11-15 (Helm's Deep stone set)
for b in (11, 12, 13, 14, 15):
    for i in range(1, 16):
        c = from555(pal[b*16+i]);
        if c == (0, 0, 0): continue
        new[b*16+i] = gba(recolor(c, auto_material(c), env_t))[1]
# Aragorn: OBJ palette 0 (=16), tagged by hand
TAG = {1:'steel',2:'steel',3:'steel',4:'steel',5:'steel',6:'steel',7:'ranger',8:'ranger',9:'steel',
       10:'skin',11:'skin',12:'skin',13:'skin',14:'leather',15:'leather'}
for i, m in TAG.items():
    new[256+i] = gba(recolor(from555(pal[256+i]), m, hero_t))[1]
open(os.path.join(out, 'newpal.bin'), 'wb').write(np.array(new, '<u2').tobytes())
s = 'load hd\n1 -\nshot before\n'
for k in range(0, 512, 2):
    s += 'poke %08x %08x\n' % (0x05000000 + k*2, new[k] | (new[k+1] << 16))
s += '1 -\nshot after\n'
open(os.path.join(out, 'p.txt'), 'w').write(s)
subprocess.run(['/tmp/run', rom, os.path.join(out, 'p.txt'), out], check=True)
for n in ('before', 'after'):
    Image.open(os.path.join(out, n + '.ppm')).save(os.path.join(out, n + '.png'))
