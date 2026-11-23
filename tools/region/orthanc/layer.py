"""Orthanc's page layer data for the Play Room (recomp/playroom/orthanc-layer.js).

python3 tools/region/orthanc/layer.py REGION_DIR orthanc_top.png OUT_DIR

layer.json: the horns picture (PNG, binary alpha) with its spot in the level (px), the tower's cast shadow (PNG, grey =
darkness) with its spot, and sample points of the region's ground picture that the page matches against the game's
picture to place the layer to the pixel (the camera in memory runs ahead of in-between pictures).
"""
import base64, io, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
D, top_path, out = sys.argv[1:4]
d = json.load(open(os.path.join(D, 'region.json')))
reg = np.asarray(Image.open(os.path.join(D, 'region.png')).convert('RGB'))
b = d['blocks'][0]
ox, oy = b['x'] * 32 + 236 * 8, b['y'] * 32 - 512           # the horns' top-left in level px (as preview.py)
top = np.asarray(Image.open(top_path))
H, W = top.shape[:2]
# cast shadow (preview.py): the tower, base and top, laid down toward the east on the ground
BASEH = 330
base = reg[oy + 512:oy + 512 + BASEH, ox:ox + W].astype(np.float32)
sil = np.zeros((H + BASEH, W), bool); sil[:H] = top[..., 3] > 0; sil[H:] = base.mean(-1) < 70
x0, y0 = ox - 300, oy - 60; x1, y1 = ox + W + 700, oy + H + 360
sh = np.zeros((y1 - y0, x1 - x0), np.float32)
gy0 = oy + 512 + 300 - y0
ys, xs = np.nonzero(sil); hgt = (H + 300) - ys
px = (ox - x0) + xs + (hgt * 0.85).astype(int); py = gy0 - (hgt * 0.12).astype(int)
ok = (px >= 0) & (px < sh.shape[1]) & (py >= 0) & (py < sh.shape[0])
sh[py[ok], px[ok]] = np.maximum(sh[py[ok], px[ok]], 1 - hgt[ok] / 1600)
sh = ndimage.grey_dilation(sh, size=(3, 3)); sh = ndimage.uniform_filter(sh, 3)
a = np.clip(sh * 0.42 * 255, 0, 255).astype(np.uint8)
yy, xx = np.nonzero(a > 2); sy0, sy1, sx0, sx1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
a = a[sy0:sy1, sx0:sx1]
def png(arr, mode):
    f = io.BytesIO(); Image.fromarray(arr, mode).save(f, 'PNG', optimize=True); return base64.b64encode(f.getvalue()).decode()
# matching samples: contrasty, non-blue ground pixels around the tower (not under the horns or the shadow)
g = reg.astype(np.int32)
R0, R1 = max(0, oy - 500), min(reg.shape[0], oy + H + 900); C0, C1 = max(0, ox - 700), min(reg.shape[1], ox + W + 700)
win = g[R0:R1, C0:C1]
lum = win.sum(-1)
edge = np.abs(np.diff(lum, axis=1, prepend=lum[:, :1])) + np.abs(np.diff(lum, axis=0, prepend=lum[:1]))
blue = win[..., 2] > win[..., 0] + 12
cover = np.zeros(lum.shape, bool)
cover[max(0, oy - R0):oy - R0 + H, max(0, ox - C0):ox - C0 + W] |= top[:min(H, R1 - oy), :min(W, C1 - ox), 3] > 0
sb = np.zeros(lum.shape, bool); sb[sy0 + y0 - R0:sy1 + y0 - R0, sx0 + x0 - C0:sx1 + x0 - C0] = a > 2
score = np.where(blue | cover | sb | (lum == 0), 0, edge)
rng = np.random.default_rng(1)
samples = []
for gy in range(0, score.shape[0], 20):            # the best spot in each 20 px square
    for gx in range(0, score.shape[1], 20):
        s = score[gy:gy + 20, gx:gx + 20]
        if s.size and s.max() > 60:
            k = np.argmax(s); yy_, xx_ = divmod(k, s.shape[1])
            p = win[gy + yy_, gx + xx_]
            samples.append([int(C0 + gx + xx_), int(R0 + gy + yy_), int(p[0]), int(p[1]), int(p[2])])
lay = dict(x=int(ox), y=int(oy), w=W, h=H, top=png(top, 'RGBA'), sx=int(x0 + sx0), sy=int(y0 + sy0), sw=int(a.shape[1]), sh=int(a.shape[0]),
           shadow=png(a, 'L'), samples=samples, level=51)
os.makedirs(out, exist_ok=True)
json.dump(lay, open(os.path.join(out, 'layer.json'), 'w'))
print('layer', ox, oy, W, H, 'shadow', lay['sx'], lay['sy'], a.shape, 'samples', len(samples), 'json', os.path.getsize(os.path.join(out, 'layer.json')))
