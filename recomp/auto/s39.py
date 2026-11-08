from g import *
init(); run(400)
for i in range(1): tap('D',3,10)
tap('A',4,80); tap('A',4,200); run(400); print('state',hex(r8(0x030041B0)))
save('normalF'); shot('nf')
a=blk(0x03004180,0x100); 
load('moria0'); run(1); b=blk(0x03004180,0x100)
load('moriaE'); run(1); c=blk(0x03004180,0x100)
for i in range(0x100):
    if a[i]!=b[i] or b[i]!=c[i]: print(hex(0x03004180+i),a[i],b[i],c[i])
