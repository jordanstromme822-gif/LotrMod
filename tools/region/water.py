"""Isengard's flood water for the page layer: the game's own water tile, toned for the region.

python3 tools/region/water.py LEVEL_PNG CONFIG.json OUT_DIR   (CONFIG: the mountains config, its "water" key)

LEVEL_PNG is a whole-level picture with open water (tools/storymap/cap.py; Isengard uses level 60, the waterfall pool,
whose water repeats every 32 px). CONFIG 'tile' [x, y] picks one 32 x 32 repeat of it; 'grey' and 'dark' tone it toward
the region's soot-and-ash colours. Writes OUT_DIR/water.png (32 x 32 RGB); the page scrolls it along the ripples and
adds glints and steam (recomp/playroom/mountain-layer.js).
"""
import json, os, sys
import numpy as np
from PIL import Image
src, cfg_path, out = sys.argv[1:4]
C = json.load(open(cfg_path)); C = C.get('water', C)
a = np.array(Image.open(src).convert('RGB')).astype(np.float32)
x, y = C['tile']; t = a[y:y + 32, x:x + 32]
assert np.abs(a[y:y + 32, x + 32:x + 64] - t).max() < 1 and np.abs(a[y + 32:y + 64, x:x + 32] - t).max() < 1, 'not a 32 px repeat'
g = C.get('grey', 0.35); d = C.get('dark', 0.8)
t = (t * (1 - g) + t.mean(2, keepdims=True) * g) * d
os.makedirs(out, exist_ok=True)
Image.fromarray(t.clip(0, 255).astype(np.uint8)).save(os.path.join(out, 'water.png'))
print('water tile', x, y)
