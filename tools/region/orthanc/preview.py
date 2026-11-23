import json, numpy as np, sys
from PIL import Image
D=sys.argv[1]; d=json.load(open(D+'/region.json')); im=np.asarray(Image.open(D+'/region.png').convert('RGB')).astype(np.float32)
b=d['blocks'][0]; ox,oy=b['x']*32+236*8, b['y']*32-512
top=np.asarray(Image.open('orth/orthanc_top.png')).astype(np.float32)
H,W=top.shape[:2]
x0,y0=ox-300,oy-60; x1,y1=ox+W+700,oy+H+360
crop=im[y0:y1,x0:x1].copy()
# cast shadow: the tower (base + top) laid down toward the east on the ground, softened at its far end
base=np.asarray(Image.open(D+'/region.png').convert('RGB'))[oy+512:oy+512+330, ox:ox+W].astype(np.float32)
bm=(np.abs(base-np.array([0,0,0])).sum(-1)>0)
# tower body mask from the map: dark tower colours (palette 8 range) vs gravel: use the top overlay + base rows
sil=np.zeros((H+330,W),bool); sil[:H]=top[...,3]>0
dark=(base.mean(-1)<70); sil[H:]=dark
sh=np.zeros(crop.shape[:2],np.float32)
gy0=oy+512+300-y0                                   # ground line (bottom of the tower base) in crop coords
ys,xs=np.nonzero(sil)
hgt=(H+300)-ys                                      # height above the ground line
px=(ox-x0)+xs+(hgt*0.85).astype(int); py=gy0-(hgt*0.12).astype(int)
ok=(px>=0)&(px<sh.shape[1])&(py>=0)&(py<sh.shape[0])
sh[py[ok],px[ok]]=np.maximum(sh[py[ok],px[ok]],1-hgt[ok]/1600)
from scipy import ndimage
sh=ndimage.grey_dilation(sh,size=(3,3)); sh=ndimage.uniform_filter(sh,3)
crop*=1-0.42*sh[...,None]
# tower top over everything
ty,tx=oy-y0,ox-x0
a=top[...,3:]/255; crop[ty:ty+H,tx:tx+W]=crop[ty:ty+H,tx:tx+W]*(1-a)+top[...,:3]*a
Image.fromarray(crop.clip(0,255).astype(np.uint8)).save(sys.argv[2]); print(crop.shape)
