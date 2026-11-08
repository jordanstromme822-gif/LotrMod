from bot3 import *
init(); load('godE2'); run(1)
x,y=pos(); print('hero',x,y)
en,items,trig=scan()
for p in en+trig: print(hex(p),hex(r32(p+0x14)),pos(p),r8(p+0x62),r8(p+0x63))
W,H,g=colmap(); gw=W//8; cx,cy=x//8,y//8
for yy in range(cy-10,cy+12):
    print(''.join(('@' if (xx,yy)==(cx,cy) else ('T' if (xx,yy)==(1180//8,1312//8) else ('.' if OK[g[xx+yy*gw]] else '%x'%(g[xx+yy*gw]&15)))) for xx in range(cx-30,cx+30)))
shot('gs')
