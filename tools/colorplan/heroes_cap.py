"""Shared helpers: read a hero (all prio-2 sprites) from a capture as index map + palettes."""
import numpy as np, sys
_argv = sys.argv; sys.argv = ['x']
exec(open(__file__.replace('heroes_cap.py', 'oamread.py')).read())
sys.argv = _argv
from oklab import from555
NAMES = ['aragorn', 'gandalf', 'eowyn', 'gimli', 'frodo', 'legolas']
def hero(D):
    sp = [s for s in sprites(D) if s['prio'] == 2]
    x0 = min(s['x'] for s in sp); y0 = min(s['y'] for s in sp)
    W = max(s['x'] + s['w'] for s in sp) - x0; H = max(s['y'] + s['h'] for s in sp) - y0
    idx = np.full((H, W), -1)              # bank*16 + index
    for s in sorted(sp, key=lambda s: -s['i']):
        sub = idx[s['y']-y0:s['y']-y0+s['h'], s['x']-x0:s['x']-x0+s['w']]
        m = s['img'] > 0; sub[m] = s['bank']*16 + s['img'][m]
    pal = [from555(int(v)) for v in np.frombuffer(D[0x18200:0x18400], '<u2')]
    return idx, pal
