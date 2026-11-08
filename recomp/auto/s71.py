from g import *
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
for k in ['R','U+R','RT+R','LT+R','D+R']:
    load('nearchest2'); run(1)
    e=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1049][0]
    for i in range(3):
        d=k.split('+')[0]
        if d!='R': run(4,d)
        run(6,k); run(20)
    print(k, r8(e+0x63), pos())
