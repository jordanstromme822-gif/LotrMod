from g import *
import struct
init(); load('near1'); run(2)
G=colmap()
t=0x20177f0; pl=0x03003C00
prev=None
for i in range(200):
    x,y=pos(); ex,ey=pos(t)
    if abs(ex-x)+abs(ey-y)>30:
        path=bfs(*G,x,y,lambda c:abs(c[0]-ex//8)<=2 and abs(c[1]-ey//8)<=2)
        if path: wp=path[min(3,len(path)-1)]; run(4,steer(x,y,wp[0]*8+4,wp[1]*8+4))
        else: run(4)
    else:
        run(2,steer(x,y,ex,ey)); run(4,'A'); run(6)
    hp=r16(pl+0x17c)
    e=blk(t,0x148)
    if prev:
        ch=[(hex(o),struct.unpack_from('<H',prev,o)[0],struct.unpack_from('<H',e,o)[0]) for o in range(0x20,0x148,2) if prev[o:o+2]!=e[o:o+2] and not (0xa8<=o<0xe0) and o not in (0xe0,0xe2,0xe8,0xea,0xec,0xf2,0x50,0x62,0x66,0x5e,0xf8,0x8e)]
    else: ch=[]
    prev=e
    print(i,(x,y),(ex,ey),'hp',hp,ch[:8])
    if hp==0 or hp>200: break
