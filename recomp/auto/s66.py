from g import *
init(); load('god_1500'); run(1)
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
W,H,gm=colmap(); gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
go((W,H,gm),1371,640,maxsteps=600,near=26); print(pos())
ch=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1371][0]
save('nearchest')
for k in ['R','B']:
    load('nearchest'); run(1)
    b0=blk(ch+0x58,0x20)
    for i in range(3): run(3,'RT'); run(4,'RT+'+k); run(25)
    print(k, b0.hex(), blk(ch+0x58,0x20).hex(), hex(r32(ch+0x14)))
    shot('ch_'+k)
