from g import *
init(); load('fight'); run(2)
t=0x20177f0; pl=0x03003C00
import struct
for i in range(600):
    L.w16(pl+0x17c,125)
    x,y=pos(); ex,ey=pos(t)
    if r32(t+0x14)!=0x801b9d1 or r32(t+0x18)!=0x8014e09:
        print('changed',i,hex(r32(t+0x14)),hex(r32(t+0x18)),pos(t)); break
    run(2,steer(x,y,ex,ey)); run(4,'A'); run(6)
    if i%50==0: print(i,hex(r8(t+0x6c)),[hex(r8(t+o)) for o in range(0x60,0x70)])
save('killed1'); shot('k1')
