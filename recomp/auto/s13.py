from g import *
import struct
init(); load('moria0'); run(2)
G=colmap()
go(G,1160,460)
save('near1')
en=[p for p in entities() if r32(p+0x14)==0x801b9d1]
def near():
    x,y=pos(); best=None
    for p in en:
        ex,ey=pos(p); d=abs(ex-x)+abs(ey-y)
        if best is None or d<best[0]: best=(d,p)
    return best
d,t=near(); print('target',hex(t),pos(t),d)
before=blk(t,0x148)
for i in range(120):
    x,y=pos(); ex,ey=pos(t)
    if abs(ex-x)+abs(ey-y)>30:
        path=bfs(*G,x,y,lambda c:abs(c[0]-ex//8)<=2 and abs(c[1]-ey//8)<=2)
        if path: wp=path[min(3,len(path)-1)]; run(4,steer(x,y,wp[0]*8+4,wp[1]*8+4))
        else: run(4)
    else:
        run(2,steer(x,y,ex,ey)); run(4,'A'); run(6)
    if i%5==0:
        print(i,pos(t),[hex(r16(t+o)) for o in range(0x84,0x98,2)],"hero",[r16(r32(0x03003C00)+o) for o in (0x84,0x86,0x88,0x8a,0x8c,0x8e)])
    if 0:
        a=blk(t,0x148)
        ch=[(hex(o),struct.unpack_from('<H',before,o)[0],struct.unpack_from('<H',a,o)[0]) for o in range(0x40,0x148,2) if before[o:o+2]!=a[o:o+2] and o not in range(0xa8,0xe0)]
        print(i,pos(),pos(t),ch[:14])
shot('f1')
