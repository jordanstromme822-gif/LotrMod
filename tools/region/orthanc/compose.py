import sys, numpy as np, json
from PIL import Image
z=np.load('orth/horns2.npz'); h1,h2,X0,Hh=z['h1'],z['h2'],int(z['X0']),int(z['H'])
c=np.load('orth/comp.npz'); CI,CP,rgb=c['CI'],c['CP'],c['rgb']
P8=rgb[128:144].astype(np.float32)
Hp,Wp=h1.shape
def mirror(I):                       # about the tower centre: canvas px x <-> 679 - x
    O=np.zeros_like(I); xs=np.arange(Wp); m=679-xs; ok=(m>=0)&(m<Wp)
    O[:,xs[ok]]=I[:,m[ok]]; return O
# brightness ramp in the tower's own purple-grey family (no teal or green steps)
order=[1,15,14,12,9,8,3,5,6]
near={i:min(range(len(order)),key=lambda k:((P8[order[k]]-P8[i])**2).sum()) for i in range(1,16)}
rank={i:near[i] for i in range(1,16)}
def step(I,n):                       # move palette indices n steps along the brightness ramp
    O=I.copy()
    for i in range(1,16):
        k=min(len(order)-1,max(0,rank[i]+n)); O[I==i]=order[k]
    return O
def finish(I, dirx, K):
    """curve outward (dirx -1 left, +1 right) by K px at the tip, light left / shade right, glassy rim"""
    m=I>0; rows=np.where(m.any(1))[0]; top,bot=rows.min(),Hp-1
    O=np.zeros_like(I)
    for y in rows:
        h=(bot-y)/(bot-top+1e-6); s=int(round(dirx*K*h**2.2))
        xs=np.where(m[y])[0]; l,r=xs.min(),xs.max(); w=max(1,r-l)
        row=I[y].copy(); t=(np.arange(Wp)-l)/w
        fade=min(1.0,max(0.0,(Hp-1-y-56)/64.0))     # no shading near the old top, so the horns grow out of it
        lit=(t<0.28*fade)&m[y]; sh=(t>1-0.28*fade)&m[y]; sh2=(t>1-0.12*fade)&m[y]
        row=np.where(lit, step(row[None],1)[0], row); row=np.where(sh, step(row[None],-1)[0], row); row=np.where(sh2, step(row[None],-1)[0], row)
        row[l]=3 if I[y,l] else row[l]          # glassy rim on the lit edge
        row[r]=15
        if s>0: row=np.concatenate([np.zeros(s,np.uint8),row[:-s]])
        elif s<0: row=np.concatenate([row[-s:],np.zeros(-s,np.uint8)])
        O[y]=row
    return O
H1=finish(h1,-1,int(sys.argv[1]) if len(sys.argv)>1 else 34); H4=finish(mirror(h1),1,int(sys.argv[1]) if len(sys.argv)>1 else 34)
H2=finish(h2,-1,int(sys.argv[2]) if len(sys.argv)>2 else 14); H3=finish(mirror(h2),1,int(sys.argv[2]) if len(sys.argv)>2 else 14)
T=np.zeros((Hp,Wp),np.uint8)
for L in (H1,H4,H2,H3): T=np.where(L>0,L,T)
# high window: the tower's own arched window (without its balcony), set into the shaft where the inner horns meet
arch=CI[50:90,371:405].copy(); ap=CP[50:90,371:405]
yy,xx=np.mgrid[0:40,0:34]; mask=((xx-16.5)/17.5)**2+((yy-17)/17.5)**2<=1; mask|= (yy>=17)&(xx>=0)&(xx<34)&(yy<38)
mask&=(ap==8)&(arch>0)
cx=(278-X0)*8+4-17; cy=Hp-60
T[cy:cy+40,cx:cx+34]=np.where(mask,arch,T[cy:cy+40,cx:cx+34])
# ledge along the old top (as on the map): hides where the inner horns stand on the old inner walls
L,Rr=59,620
for r,v in {1:15,2:4,3:4,4:9,5:12,6:12,7:14}.items():
    T[Hp-8+r,L:Rr+1]=v; T[Hp-8+r,L]=15; T[Hp-8+r,Rr]=15
    if r>=2: T[Hp-8+r,L+1]=9; T[Hp-8+r,Rr-1]=9
np.save('orth/top_idx.npy',T)
rgba=np.zeros((Hp,Wp,4),np.uint8); rgba[...,:3]=P8[T].astype(np.uint8); rgba[...,3]=(T>0)*255
Image.fromarray(rgba).save('orth/orthanc_top.png'); print(T.shape)
