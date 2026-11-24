"""The far valley seen past a region's open edge (Isengard's south): two pictures for the page's parallax layer.

python3 tools/region/drop.py LEVEL_PNG CONFIG.json OUT_DIR   (CONFIG: the mountains config, its "drop" key)

LEVEL_PNG is a whole-level picture of a grassland level (tools/storymap/cap.py; Isengard uses Pelennor Fields, level
104: Rohan's golden grass with its earth terraces). From it come
- OUT_DIR/drop-plain.png: the plain far below (CONFIG 'plain' rect), hazed toward 'haze' by 'haze_amount', darkened by
  'dark'. The page scrolls it at half the ground's speed, so it reads as land far below the region's edge.
- OUT_DIR/drop-face.png: the earth bank under the region's edge, the game's own terrace face (CONFIG 'face' rect, the
  columns 'face_cols'), one column per pixel, each column's top at row 0 and transparent below its foot; its lower part
  fades into the haze ('face_fade'), greyed by 'face_grey' and darkened by 'face_dark'. The page hangs it under every edge where the land stops above the drop.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, cfg_path, out = sys.argv[1:4]
CFG = json.load(open(cfg_path)); CFG = CFG.get('drop', CFG)   # the region's mountains config ('drop' key) or a bare one
os.makedirs(out, exist_ok=True)
a = np.array(Image.open(src).convert('RGB')).astype(np.float32)
haze = np.array(CFG.get('haze', [128, 128, 124]), np.float32); ha = CFG.get('haze_amount', 0.4); dk = CFG.get('dark', 0.9)

x0, y0, x1, y1 = CFG['plain']
plain = a[y0:y1, x0:x1] * dk * (1 - ha) + haze * ha
Image.fromarray(plain.clip(0, 255).astype(np.uint8)).save(os.path.join(out, 'drop-plain.png'), optimize=True)

# the face: not-grass pixels around the terrace, cleaned, its largest piece; per column its top and foot
fx0, fy0, fx1, fy1 = CFG['face']
f = a[fy0:fy1, fx0:fx1]; R, G, B = f[..., 0], f[..., 1], f[..., 2]
ng = ~((R > 120) & (G > 95) & (R - B > 60))
ng = ndimage.binary_opening(ndimage.binary_closing(ng, iterations=2), iterations=2)
lab, n = ndimage.label(ng); sz = ndimage.sum(ng, lab, range(1, n + 1)); m = ndimage.binary_fill_holes(lab == 1 + int(np.argmax(sz)))
foot_max = CFG.get('face_foot_max', 9999)
cols = []
for x in [x - fx0 for c0, c1 in CFG['face_cols'] for x in range(c0, c1)]:   # column runs (leaving out bushes at the foot)
    ys = np.nonzero(m[:, x])[0]; top = int(ys.min()); bot = min(int(ys.max()), foot_max - fy0)
    cols.append(f[top:bot + 1, x])
H = max(len(c) for c in cols)
face = np.zeros((H, len(cols), 4), np.float32)
fade = CFG.get('face_fade', 0.35); fg = CFG.get('face_grey', 0); fd = CFG.get('face_dark', 1)
for x, c in enumerate(cols):
    c = (c * (1 - fg) + c.mean(1, keepdims=True) * fg) * fd   # toned toward the region's stone
    t = np.linspace(0, 1, len(c))[:, None]
    face[:len(c), x, :3] = c * (1 - fade * t) + haze * fade * t
    face[:len(c), x, 3] = 255
Image.fromarray(face.clip(0, 255).astype(np.uint8), 'RGBA').save(os.path.join(out, 'drop-face.png'), optimize=True)
json.dump(dict(plain=[x1 - x0, y1 - y0], face=[len(cols), H]), open(os.path.join(out, 'drop.json'), 'w'))
print('plain', x1 - x0, y1 - y0, 'face', len(cols), H)
