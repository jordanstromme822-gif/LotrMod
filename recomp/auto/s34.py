from bot2 import *
init(); load('moriaE'); run(1)
b=Bot(); pl=0x03003C00
lastpk=None
for i in range(4000):
    r=b.tick()
    pk=(r8(pl+0x182),r8(pl+0x184),r8(pl+0x186),r8(pl+0x18c))
    if pk!=lastpk: print(i,'pack',pk); lastpk=pk
    if b.log: print(i,b.log); b.log.clear()
    if i%100==0: print(i,r)
    if r[0]=='done': print(i,r); break
save('bot2end'); shot('b2')
