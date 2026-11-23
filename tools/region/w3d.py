"""3D World picture of a region: the region's ground (region.png from tools/region/region.py) with the page-drawn
landmark layers (tools/region/orthanc/layer.py: the cast shadow, then Orthanc's horns) composited, scaled to fit an
iPhone texture (longest side 4000 px).

python3 tools/region/w3d.py REGION_DIR LAYER_DIR OUT.webp
"""
import base64, io, json, sys
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
rdir, ldir, out = sys.argv[1:4]
im = Image.open(rdir + '/region.png').convert('RGB')
L = json.load(open(ldir + '/layer.json'))
png = lambda b: Image.open(io.BytesIO(base64.b64decode(b)))
a = np.array(im).astype(np.float32)
sh = np.array(png(L['shadow']).convert('L')).astype(np.float32) / 255.0
y0, x0 = L['sy'], L['sx']; h, w = sh.shape
a[y0:y0 + h, x0:x0 + w] *= (1 - sh)[..., None]
im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
top = png(L['top']).convert('RGBA')
im.paste(top, (L['x'], L['y']), top)
k = 4000 / max(im.size)
im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
im.save(out, 'WEBP', quality=88, method=6)
print(out, im.size)
