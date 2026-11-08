import ctypes,os
from PIL import Image
L=ctypes.CDLL('/tmp/rc/auto/libwrap.so')
for f in 'r8 r16 r32'.split(): getattr(L,f).restype=ctypes.c_uint
K=dict(A=1,B=2,SEL=4,START=8,RT=16,LT=32,U=64,D=128,L=512,R=256)
# note: libmgba bit8=L? run.c says bit 8 = L, bit 9 = R
K['R']=256; K['L']=512
def keys(s): 
    m=0
    for t in s.split('+'):
        if t and t!='-': m|=K[t]
    return m
def init(): L.init(b'/tmp/rc/auto/game.gba',1)
def run(n,k='-'): L.step(keys(k),n)
def tap(k,hold=4,after=20): run(hold,k); run(after)
def shot(name):
    L.shot(f'/tmp/rc/auto/{name}.ppm'.encode()); Image.open(f'/tmp/rc/auto/{name}.ppm').resize((480,320),Image.NEAREST).save(f'/tmp/rc/auto/{name}.png')
def blk(a,n):
    b=(ctypes.c_ubyte*n)(); L.readblk(a,n,b); return bytes(b)
r8=L.r8; r16=L.r16; r32=L.r32
def save(n): L.savest(f'/tmp/rc/auto/{n}.state'.encode())
def load(n): L.loadst(f'/tmp/rc/auto/{n}.state'.encode())
def colmap():
    W=r16(0x03005F90)*8; H=r16(0x03005F88)*8
    bm=r32(0x0300206C); ct=r32(0x03002068)
    bw=W>>5
    blocks=blk(bm,(bw*(H>>5))*2)
    import struct
    gw,gh=W//8,H//8
    g=bytearray(gw*gh)
    cache={}
    for cy in range(gh):
        for cx in range(gw):
            b=struct.unpack_from('<H',blocks,((cx>>2)+(cy>>2)*bw)*2)[0]&0xfff
            if b not in cache: cache[b]=blk(ct+(b<<4),16)
            g[cx+cy*gw]=cache[b][(cx&3)|((cy&3)<<2)]
    return W,H,g
def bfs(W,H,g,sx,sy,targets_fn,maxd=100000):
    from collections import deque
    gw,gh=W//8,H//8
    def free(cx,cy):
        if cx<1 or cy<1 or cx>=gw-1 or cy>=gh-1: return False
        return g[cx+cy*gw]==0 and g[cx-1+cy*gw]==0 and g[cx+1+cy*gw]==0
    s=(sx//8,sy//8); prev={s:None}; q=deque([s])
    while q:
        c=q.popleft()
        if targets_fn(c): 
            path=[]
            while c: path.append(c); c=prev[c]
            return path[::-1]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            n=(c[0]+dx,c[1]+dy)
            if n in prev or not free(*n): continue
            if dx and dy and not (free(c[0]+dx,c[1]) and free(c[0],c[1]+dy)): continue
            prev[n]=c; q.append(n)
    return None
def entities():
    out=[]; p=r32(0x03003C00)
    while p:
        out.append(p); p=r32(p+4)
    return out
H_=lambda: r32(0x03003C00)
def pos(p=None):
    p=p or r32(0x03003C00); return r16(p+0xae),r16(p+0xb2)
def steer(x,y,wx,wy,extra=''):
    k=[]
    if wx-x>2:k.append('RT')
    if wx-x<-2:k.append('LT')
    if wy-y>2:k.append('D')
    if wy-y<-2:k.append('U')
    if extra:k.append(extra)
    return '+'.join(k)
def go(g3,tx,ty,maxsteps=400,near=12,cb=None):
    W,H,g=g3
    for it in range(maxsteps):
        x,y=pos()
        if abs(x-tx)<near and abs(y-ty)<near: return True
        path=bfs(W,H,g,x,y,lambda c:abs(c[0]-tx//8)<=1 and abs(c[1]-ty//8)<=1)
        if not path: return False
        wp=path[min(3,len(path)-1)]
        run(4,steer(x,y,wp[0]*8+4,wp[1]*8+4))
        if cb: cb(it)
    return False
