"""Orthanc's top for the Isengard region: four horns built from the tower's own tiles.
The tower's outer faces repeat every 6 tile rows shifted one tile inward (their silhouette edge too, on layer B), so a
horn = that face (left half) + its mirror (right half), narrowing one tile per side every 6 rows to a spear point
(Tolkien: four piers opening into horns, 'their pinnacles sharp as the points of spears'). A ledge on layer B along the
tower's old top row hides the change from the old faces to the horns."""
import sys, pickle, numpy as np
sys.path.insert(0,'/home/user/lotrmod/tools/join'); sys.path.insert(0,'/home/user/lotrmod/tools/siege')
from cells import load, pix
sys.path.insert(0,"/home/user/lotrmod/tools/siege")
d=pickle.load(open('jn3/world.pkl','rb')); GA,GB=d['GA'],d['GB']
R, lv, rgb, grids, pixels = load(sys.argv[1] if len(sys.argv)>1 else 'orig.gba', [50,51,55])
FL=0x400
def flip(t): return (t[0], t[1]^FL) if t[0] else t
EDGE0=243; CEN2=556            # left silhouette tile col at row 0; mirror sum about the tower centre
NROW=44; X0=240; NCOL=80       # block: 8px cols 240..319, rows -44..-1
A=[[None]*NCOL for _ in range(NROW)]; B=[[(0,0)]*NCOL for _ in range(NROW)]; C=[[None]*NCOL for _ in range(NROW)]
def src(Y, X):                 # the left outer face field (A, B) at any row above the map: 6 rows up = one tile right
    k=(-Y+5)//6; return GA[Y+6*k][X-k], GB[Y+6*k][X-k], k
def horn(e0, half):            # e0: left edge col at row 0 (field translated to it), half: tiles from edge to axis
    ax=e0+half                 # first col of the mirrored half
    for Y in range(-1,-NROW-1,-1):
        k=(-Y+5)//6
        if e0+k-1>=ax: break
        for X in range(e0+k-2, ax):
            if X<e0-1: continue
            a,b,_=src(Y, X-e0+EDGE0)
            for XX,aa,bb in ((X,a,b),(2*ax-1-X,flip(a),flip(b))):
                r=Y+NROW; c=XX-X0
                if (aa[1]>>12)==8 and aa[0]: A[r][c]=aa
                if bb[0]: B[r][c]=bb
                C[r][c]=1
hw=7; horn(243,hw); horn(263,6)
# right two horns: mirror of the left two about the tower centre
for r in range(NROW):
    for c in range(NCOL):
        X=c+X0; M=CEN2-X
        if X<=278 or not (X0<=M<X0+NCOL): continue
        mc=M-X0
        if A[r][mc] is not None: A[r][c]=flip(A[r][mc])
        if B[r][mc][0]: B[r][c]=flip(B[r][mc])
        if C[r][mc] is not None: C[r][c]=C[r][mc]
pickle.dump(dict(A=A,B=B,C=C,X0=X0,NROW=NROW), open('orth/horns.pkl','wb'))
print('A tiles', sum(a is not None for row in A for a in row), 'B', sum(b[0]>0 for row in B for b in row))

# ---- ledge + polished floor where the horns meet the old top -------------------------------------------------------
from build import pix as pix4
need={t[0] for row in A for t in row if t}|{t[0] for row in B for t in row}|{GA[y][x][0] for y in range(8) for x in range(240,320)}|{GB[y][x][0] for y in range(8) for x in range(240,320)}
miss=sorted(need-set(pixels)); pixels.update(dict(zip(miss, R.tiles(lv[55].tileset, miss))))
def tix(t):
    p=pix4(pixels[t[0]]).copy()
    if t[1]&0x400: p=p[:,::-1]
    if t[1]&0x800: p=p[::-1]
    return p
def pack(p): return bytes(int(p.reshape(64)[2*i]) | int(p.reshape(64)[2*i+1])<<4 for i in range(32))
# opaque tower pixels of tile rows -2, -1 (16 px rows) over cols 240..319
op=np.zeros((16,640),bool); bimg=np.zeros((16,640),np.uint8)
for i,Y in enumerate((-2,-1)):
    for c in range(NCOL):
        a=A[Y+NROW][c]; b=B[Y+NROW][c]
        if a is not None: op[i*8:i*8+8,c*8:c*8+8]|=tix(a)>0
        if b[0]:
            pb=tix(b); op[i*8:i*8+8,c*8:c*8+8]|=pb>0; bimg[i*8:i*8+8,c*8:c*8+8]=np.where(pb>0,pb,0)
# tower bounds: left silhouette of horn 1 (and its mirror) on the beam rows
lrow=[int(np.where(op[r,:120])[0].min()) for r in range(16)]
L=min(lrow[8:]); Rr=(4455-X0*8)-L - 0          # mirror in block px: x' = 4455 - (X0*8 + x) - X0*8
Rr=4455-2*X0*8-L
print('beam px', L, Rr)
prof={1:15,2:4,3:4,4:9,5:12,6:12,7:14}
new=bimg.copy()
for r,v in prof.items():
    new[8+r,L:Rr+1]=v; new[8+r,L]=15; new[8+r,Rr]=15
    if r>=2: new[8+r,L+1]=9; new[8+r,Rr-1]=9
# floor between the horns (only where no horn stands): back edge, then dark polished stone with one sheen line
for r in range(16):
    if r<9: continue
for r in range(1,9):
    v={1:15,2:14,3:13,4:13,5:11,6:13,7:13,8:13}[r]
    rr=r if r<8 else 8          # rows 1..7 of tile -2, row 8 = row 0 of tile -1
    m=~op[rr,L+1:Rr]
    seg=new[rr,L+1:Rr]; seg[m]=v; new[rr,L+1:Rr]=seg
newpix={}; nid=[200000]
def tid(p):
    k=pack(p)
    for i,v in newpix.items():
        if v==k: return i
    nid[0]+=1; newpix[nid[0]]=k; return nid[0]
for i,Y in enumerate((-2,-1)):
    for c in range(NCOL):
        p=new[i*8:i*8+8,c*8:c*8+8]
        if not (p>0).any(): continue
        if (p==bimg[i*8:i*8+8,c*8:c*8+8]).all(): continue
        B[Y+NROW][c]=(tid(p),8<<12); C[Y+NROW][c]=1
print('new ledge tiles', len(newpix))
# the old top's see-through slit inside the tower: the dark tile under it
fixA=[]
for Y in range(0,6):
    for X in range(244,313):
        if GA[Y][X][0]==0 and GB[Y][X][0]==0:
            for YY in range(Y+1,20):
                if GA[YY][X][0] and (GA[YY][X][1]>>12)==8: fixA.append((Y,X,GA[YY][X])); break
print('slit fixes', fixA)
pickle.dump(dict(A=A,B=B,C=C,X0=X0,NROW=NROW,newpix=newpix,fixA=fixA), open('orth/horns.pkl','wb'))
