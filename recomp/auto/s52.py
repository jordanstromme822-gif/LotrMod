from g import *
import sys
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
states=['moriaE','godE2','godE3']+[f'god_{i}' for i in range(0,4001,250)]
for fn in [0x80200c9,0x80326ad,0x8043c8d,0x8033d1d,0x8014a3d,0x8036851]:
    best=None
    for st in states:
        load(st); run(1)
        x,y=pos()
        for e in lstents():
            if r32(e+0x14)==fn:
                d=abs(r16(e+0xae)-x)+abs(r16(e+0xb2)-y)
                if best is None or d<best[0]: best=(d,st,r16(e+0xae),r16(e+0xb2))
    print(hex(fn),best)
    d,st,tx,ty=best
    load(st); run(1)
    W,H,gm=colmap(); gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
    ok=go((W,H,gm),tx,ty,maxsteps=600,near=40)
    print(' reached',ok,pos())
    shot(f'ent_{fn:x}')
