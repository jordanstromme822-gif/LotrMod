"""Check a built region for walking without playing it (2026-11-23): which places can reach which, and any blocked
spot on a road.

python3 tools/region/walkcheck.py REGION.pkl POINTS.json [OUT.png]

POINTS.json: {"name": [x, y], ...} in region px. A spot (8 px) is walkable when its collision's low 3 bits are 0 and it
has ground (not the see-through void past the map's edge). The hero is wider than one spot, so a way only counts where
a 2 x 2 block of spots is walkable (WIDTH env changes it). Prints, for every place, which other places it reaches, the
road spots that are blocked, and writes OUT.png (walkable grey, blocked dark, reached from the first place green, roads
yellow, places red) at 1 px per spot.
"""
import json, os, pickle, sys
import numpy as np
from scipy import ndimage

R = pickle.load(open(sys.argv[1], 'rb')); P = json.load(open(sys.argv[2]))
GA, GC = R['GA'], R['GC']; H8, W8 = len(GA), len(GA[0])
walk = np.array([[c is not None and (c & 7) == 0 and a is not None and a[0] != 0 for a, c in zip(ra, rc)] for ra, rc in zip(GA, GC)])
w = int(os.environ.get('WIDTH', 2))
fit = ndimage.binary_erosion(walk, structure=np.ones((w, w), bool), origin=0, border_value=0)
lab, n = ndimage.label(fit)
def spot(xy):
    x, y = int(xy[0]) // 8, int(xy[1]) // 8
    if fit[y, x]: return lab[y, x]
    ys, xs = np.nonzero(fit[max(0, y - 3):y + 4, max(0, x - 3):x + 4])   # stand on the nearest fitting spot (within 24 px)
    if len(ys) == 0: return 0
    k = np.argmin((ys - min(3, y)) ** 2 + (xs - min(3, x)) ** 2)
    return lab[max(0, y - 3) + ys[k], max(0, x - 3) + xs[k]]
ids = {k: spot(v) for k, v in P.items()}
ok = True
for k, v in ids.items():
    if not v: print('%-24s NOT WALKABLE here' % k); ok = False; continue
    same = [o for o, u in ids.items() if u == v and o != k]
    print('%-24s reaches %s' % (k, ', '.join(same) or 'nothing else'))
road = R.get('road')
if road is not None:
    bad = np.argwhere(road & ~walk)
    print('road spots', int(road.sum()), 'blocked', len(bad), ('first ' + str([(int(x) * 8, int(y) * 8) for y, x in bad[:10]])) if len(bad) else '')
    ok &= len(bad) == 0
if len(sys.argv) > 3:
    img = np.zeros((H8, W8, 3), np.uint8) + 20
    img[walk] = (110, 110, 110)
    first = next(iter(ids.values()))
    if first: img[lab == first] = (70, 160, 80)
    if road is not None: img[road] = (220, 200, 90)
    for v in P.values():
        x, y = int(v[0]) // 8, int(v[1]) // 8; img[max(0, y - 4):y + 5, max(0, x - 4):x + 5] = (230, 40, 40)
    from PIL import Image
    Image.fromarray(img).save(sys.argv[3])
print('ALL OK' if ok else 'PROBLEMS')
