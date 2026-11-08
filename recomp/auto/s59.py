from g import *
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
for st in ['godE2','godE3']+[f'god_{i}' for i in range(0,4001,250)]:
    load(st); run(1)
    for e in lstents():
        if r32(e+0x14)==0x80200c9 and r16(e+0xae)==756: print(st,pos()); break
    else: continue
    break
W,H,gm=colmap(); gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
print(go((W,H,gm),756,509,maxsteps=800,near=36), pos())
save('nearforge'); shot('fg0'); tap('R',6,60); shot('fg1')
