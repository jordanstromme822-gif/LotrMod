from g import *
import struct
init(); load('moriaE'); run(2)
G=colmap(); pl=0x03003C00
load('nearE')
t=0x20177f0
log=[]
for i in range(400):
    x,y=pos(); ex,ey=pos(t)
    if abs(ex-x)+abs(ey-y)>30:
        path=bfs(*G,x,y,lambda c:abs(c[0]-ex//8)<=2 and abs(c[1]-ey//8)<=2)
        if path: wp=path[min(3,len(path)-1)]; run(4,steer(x,y,wp[0]*8+4,wp[1]*8+4))
        else: run(4)
    else:
        run(2,steer(x,y,ex,ey)); run(4,'B'); run(6)
    e=(hex(r32(t+0x14)),r8(t+0x62),r8(t+0x63),r16(t+0x84),r16(t+0x86),r8(t+0x69),r16(t+0x54))
    if not log or log[-1][1]!=e: log.append((i,e)); print(i,e,'hp',r16(pl+0x17c))
    if r32(t+0x14)!=0x801b9d1: break
shot('e2')
