from g import *
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
res=[]
for dx,dy,face in [(-20,0,'RT'),(20,0,'LT'),(0,12,'U'),(0,-14,'D'),(-14,8,'RT'),(14,8,'LT')]:
    load('nearchest2'); run(1)
    e=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1049][0]
    h=r32(0x03003C00)
    L.w16(h+0xae,1049+dx); L.w16(h+0xb2,217+dy); run(2)
    run(3,face)
    for i in range(2): run(6,face+'+R'); run(25)
    res.append((dx,dy,face,pos(),r8(e+0x63)))
for r in res: print(r)
