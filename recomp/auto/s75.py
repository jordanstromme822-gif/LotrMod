from g import *
init()
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
for side in [(-20,0,'RT'),(20,0,'LT')]:
    load('nearchest2'); run(1)
    e=[e for e in lstents() if r32(e+0x14)==0x8014a3d and r16(e+0xae)==1049][0]
    bx,by=1049,217; sp=(bx+side[0],by+side[1])
    log=[]
    for i in range(60):
        x,y=pos()
        if r8(e+0x63): break
        if abs(sp[0]-x)<=8 and abs(sp[1]-y)<=8:
            run(5,side[2]+'+R'); run(15); log.append(('R',x,y))
        else:
            k=[]
            if sp[0]-x>1:k.append('RT')
            if sp[0]-x<-1:k.append('LT')
            if sp[1]-y>1:k.append('D')
            if sp[1]-y<-1:k.append('U')
            run(4,'+'.join(k)); run(2); log.append(('s',x,y))
    print(side, 'opened' if r8(e+0x63) else 'no', i, log[-6:])
