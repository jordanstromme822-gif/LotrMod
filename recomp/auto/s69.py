from g import *
init(); load('moriaE'); run(1)
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
ch=[e for e in lstents() if r32(e+0x14)==0x8014a3d]
for e in ch: print(hex(e), r16(e+0xae), r16(e+0xb2), blk(e+0x58,0x20).hex())
W,H,gm=colmap(); gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
e=[e for e in ch if r16(e+0xae)==1049][0]
print(go((W,H,gm),1049,240,maxsteps=900,near=6), pos())
save('nearchest2'); shot('c2a')
for k in ['U','U+R','R']:
    load('nearchest2'); run(1)
    for i in range(3): run(4,k.split('+')[0]); run(5,k); run(20)
    print(k, r8(e+0x63), pos())
