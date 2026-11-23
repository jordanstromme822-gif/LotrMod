"""Orthanc's top, pass 2 (pixel image for the page to draw over the map): horns from the tower's own outer-wall field,
overlapping at the base so the tower rises as one shaft before it splits; then each horn curved outward to a hooked
point, lit on its left, shaded on its right, a glassy rim, a high window, and a cast shadow."""
import sys, pickle, numpy as np
sys.path.insert(0,'/home/user/lotrmod/tools/join'); sys.path.insert(0,'/home/user/lotrmod/tools/siege')
from cells import load
from build import pix as pix4
from PIL import Image
d=pickle.load(open('jn3/world.pkl','rb')); GA,GB=d['GA'],d['GB']
R, lv, rgb, grids, pixels = load(sys.argv[1] if len(sys.argv)>1 else 'orig.gba', [50,51,55])
def tile_idx(t):
    if t[0] not in pixels: pixels[t[0]]=R.tiles(lv[55].tileset,[t[0]])[0]
    p=pix4(pixels[t[0]]).copy()
    if t[1]&0x400: p=p[:,::-1]
    if t[1]&0x800: p=p[::-1]
    return p
EDGE0=243
def src(Y, X):
    k=(-Y+5)//6; return GA[Y+6*k][X-k], GB[Y+6*k][X-k]
H=int(sys.argv[2]) if len(sys.argv)>2 else 64      # tile rows above the old top
X0=236; NC=82                                       # canvas tile cols 236..317
def horn(e0, half):
    """palette-8 index image (0 = see-through) of one horn: left edge col e0 at row 0, `half` tiles to the axis"""
    I=np.zeros((H*8,NC*8),np.uint8); ax=e0+half
    for Y in range(-1,-H-1,-1):
        k=(-Y+5)//6
        if e0+k-1>=ax: break
        for X in range(max(e0-1,e0+k-2), ax):
            a,b=src(Y, X-e0+EDGE0)
            for XX,fl in ((X,0),(2*ax-1-X,1)):
                r=(Y+H)*8; c=(XX-X0)*8
                p=np.zeros((8,8),np.uint8)
                if (a[1]>>12)==8 and a[0]: p=tile_idx(a)
                if b[0]: pb=tile_idx(b); p=np.where(pb>0,pb,p)
                if fl: p=p[:,::-1]
                I[r:r+8,c:c+8]=np.where(p>0,p,I[r:r+8,c:c+8])
    return I
np.savez('orth/horns2.npz', h1=horn(243,11), h2=horn(262,10), X0=X0, H=H)
print('ok')
