from g import *
from items import *
init(); load('moriaE'); run(1)
pl=0x03003C00
for s in range(8):
    it=r32(pl+0x3c+4*s)
    if it&15==15: print(s,'empty'); continue
    print(s,hex(it),'cat',it&15,'flags',hex(flags(it)),'req',reqlevel(it),pairs(it))
for s in range(17):
    it=r32(pl+0x5c+4*s)
    if it&15==15: continue
    print('bp',s,hex(it),'cat',it&15,'flags',hex(flags(it)),'req',reqlevel(it),pairs(it))
