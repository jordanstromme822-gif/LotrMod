from bot import *
init(); load('afterbot'); run(1)
print(pos(), hex(r8(0x030041B0)), r16(0x03003C00+0x17c))
W,H,g=colmap(); print(W,H)
en,items,trig=scan()
for p in en[:10]: print(hex(p),pos(p),r8(p+0x62))
