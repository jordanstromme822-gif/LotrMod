from bot3 import *
init(); load('godE3'); run(1)
W,H,g=colmap(); gw=W//8
en,items,trig=scan(); print('hero',pos(),len(en))
for p in en:
    x,y=pos(p); cx,cy=x//8,y//8
    near=sum(OK[g[(cx+dx)+(cy+dy)*gw]] for dx in range(-2,3) for dy in range(-2,3) if 0<=cy+dy<H//8)
    print(hex(p),(x,y),r8(p+0x62),r8(p+0x63),'freecells',near)
shot('ge3')
