from g import *
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
for path in [['LT']*6+['U']*6+['RT']*2, ['RT']*6+['U']*6+['LT']*2, ['U']*3]:
    load('nearchest2'); run(1)
    e=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1049][0]
    for d in path: run(3,d)
    p0=pos()
    for i in range(3): run(6,path[-1]+'+R'); run(20)
    print(path[-1], p0, pos(), r8(e+0x63), blk(e+0x58,0x20).hex())
