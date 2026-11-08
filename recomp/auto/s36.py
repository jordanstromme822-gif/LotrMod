from bot2 import *
pl=0x03003C00; it=0x2017418
init()
for name in ['A','L','R','SEL','B']:
    load('nearherb'); run(1); run(3,name); run(12)
    print(name,pos(),r8(it+0x63),r16(pl+0x17c))
