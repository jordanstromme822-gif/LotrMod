from g import *
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
for name,seq in [('both5',[(5,'LT+R'),(15,'-')]),('both3',[(3,'LT+R'),(15,'-')]),('face7both9',[(7,'LT'),(9,'LT+R'),(15,'-')]),('R only',[(5,'R'),(15,'-')])]:
    load('nearchest2'); run(1)
    e=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1049][0]
    h=r32(0x03003C00); L.w16(h+0xae,1064); L.w16(h+0xb2,219); run(10)
    for n,k in seq*3: run(n,k)
    print(name, r8(e+0x63), pos())
