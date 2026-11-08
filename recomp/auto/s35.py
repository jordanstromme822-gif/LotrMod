from bot2 import *
init(); load('moriaE'); run(1)
b=Bot(); pl=0x03003C00
for i in range(900):
    r=b.tick()
    if r[0]=='pick': save('nearherb'); print(i,r); break
p=[p for p in entities() if r32(p+0x14)==0x802f131 and r8(p+0x63)==3]
x,y=pos()
for q in p: print(hex(q),r8(q+0x60),pos(q),(x,y),[hex(r8(q+0x8c+k)) for k in range(4)], 'label', hex(r32(0x03003F70+0x70)))
shot('nh')
