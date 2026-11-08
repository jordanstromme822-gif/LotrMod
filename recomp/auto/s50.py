from g import *
import g as G
init(); load('moriaE'); run(10)
def ents(fn):
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return [e for e in lst if r32(e+0x14)==fn]
B=ents(0x8046125)
for e in B: print(hex(e),r16(e+0xae),r16(e+0xb2),blk(e+0x58,0x20).hex())
W,H,gm=colmap()
# patch walkable test: block only v&7 in 1,2
gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
x,y=pos()
B.sort(key=lambda e:abs(r16(e+0xae)-x)+abs(r16(e+0xb2)-y))
e=B[0]; tx,ty=r16(e+0xae),r16(e+0xb2)
print('go',tx,ty,go((W,H,gm),tx,ty,near=30))
print(pos()); shot('pot1')
save('nearpot')
before=blk(e+0x58,0x20).hex(); print(r32(e+0x14))
for i in range(6):
    run(3,'D'); run(4,'D+B'); run(20)
    print(i, hex(r32(e+0x14)), blk(e+0x58,0x20).hex(), r8(e+0x62), r8(e+0x63), pos())
shot('pot2')
