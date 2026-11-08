from g import *
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
load('nearchest2'); run(1)
e=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1049][0]
for sp in [(1049,229),(1029,217),(1069,217)]:
    load('nearchest2'); run(1)
    for i in range(80):
        x,y=pos(); tx,ty=sp
        if abs(tx-x)<=3 and abs(ty-y)<=3: break
        k=[]
        if tx-x>1:k.append('RT')
        if tx-x<-1:k.append('LT')
        if ty-y>1:k.append('D')
        if ty-y<-1:k.append('U')
        run(4,'+'.join(k)); run(2)
    print(sp,'reached',pos(),i)
