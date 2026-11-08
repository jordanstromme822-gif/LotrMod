from g import *
init()
best=None
for st in ['godE2','godE3']+[f'god_{i}' for i in range(0,4001,250)]:
    load(st); run(1); x,y=pos(); d=abs(x-1049)+abs(y-235)
    if best is None or d<best[0]: best=(d,st)
print(best); load(best[1]); run(1)
W,H,gm=colmap(); gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
print(go((W,H,gm),1049,236,maxsteps=900,near=5), pos())
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
e=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1049]
print(e and r8(e[0]+0x63))
save('nearchest2'); shot('c2a')
