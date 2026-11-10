# Merge background atlas (cut.py output dir) + sprite tiles npz into one atlas. Usage: merge.py bgdir sprites.npz outdir
import sys, json, numpy as np
from PIL import Image
bg = sys.argv[1]; m = json.load(open(bg + '/map.json')); A = np.asarray(Image.open(bg + '/atlas.png').convert('RGBA'))
C, PER = m['cell'], m['per']; cells = {}
for i, k in enumerate(m['keys']):
    r, c = divmod(i, PER); cells[k] = A[r*C+2:r*C+34, c*C+2:c*C+34]
sp = np.load(sys.argv[2])
for k in sp.files: cells[k] = sp[k]          # sprite version wins (clean edges)
keys = sorted(cells); rows = (len(keys) + PER - 1) // PER
atlas = np.zeros((rows * C, PER * C, 4), np.uint8)
for i, k in enumerate(keys):
    r, c = divmod(i, PER); atlas[r*C:(r+1)*C, c*C:(c+1)*C] = np.pad(cells[k], ((2, 2), (2, 2), (0, 0)), mode='edge')
out = sys.argv[3]; import os; os.makedirs(out, exist_ok=True)
Image.fromarray(atlas, 'RGBA').save(out + '/atlas.png', optimize=True)
json.dump({'cell': C, 'per': PER, 'keys': keys}, open(out + '/map.json', 'w'))
print('tiles', len(keys), atlas.shape)
