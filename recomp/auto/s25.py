from g import *
from collections import Counter
init(); load('moriaE'); run(2)
c=Counter()
for p in entities():
    c[(hex(r32(p+0x14)),hex(r32(p+0x18)))]+=1
for k,v in c.items(): print(k,v)
for p in entities():
    if r32(p+0x14)==0x802ed21: print(hex(p),pos(p),[hex(r8(p+o)) for o in range(0x60,0x6c)],hex(r32(p+0x88)),hex(r32(p+0xc)))
