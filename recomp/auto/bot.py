from g import *
OK=[(v&7) not in (1,2) for v in range(256)]
import struct,sys,collections
ENEMY_UPD={0x801b9d1}
DEAD={0x11,0x15,4,0x1b,0x13}
def alive(p):
    if r8(p+0x62) in DEAD or r8(p+0x63)==0x2f or (r32(p+0xe8)&2): return False
    return True
def dists(G,x,y):
    W,H,g=G; gw,gh=W//8,H//8
    def free(cx,cy):
        if cx<1 or cy<1 or cx>=gw-1 or cy>=gh-1: return False
        return OK[g[cx+cy*gw]] and OK[g[cx-1+cy*gw]] and OK[g[cx+1+cy*gw]]
    s=(x//8,y//8); prev={s:None}; q=collections.deque([s])
    if not free(*s):
        for r in (1,2,3):
            for cx in range(s[0]-r,s[0]+r+1):
                for cy in range(s[1]-r,s[1]+r+1):
                    if (cx,cy) not in prev and free(cx,cy): prev[(cx,cy)]=s; q.append((cx,cy))
            if len(q)>1: break
    while q:
        c=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            n=(c[0]+dx,c[1]+dy)
            if n in prev or not free(*n): continue
            if dx and dy and not (free(c[0]+dx,c[1]) and free(c[0],c[1]+dy)): continue
            prev[n]=c; q.append(n)
    return prev
def pathto(prev,tx,ty,r=2):
    best=None
    for cx in range(tx//8-r,tx//8+r+1):
        for cy in range(ty//8-r,ty//8+r+1):
            if (cx,cy) in prev:
                d=abs(cx*8+4-tx)+abs(cy*8+4-ty)
                if best is None or d<best[0]: best=(d,(cx,cy))
    if not best: return None
    c=best[1]; path=[]
    while c: path.append(c); c=prev[c]
    return path[::-1]
def scan():
    en=[];items=[];trig=[]
    for p in entities():
        u=r32(p+0x14)
        if u in ENEMY_UPD and alive(p): en.append(p)
        elif u==0x802f131: items.append(p)
        elif u==0x802ed21 and r8(p+0x63)==0: trig.append(p)
    return en,items,trig
