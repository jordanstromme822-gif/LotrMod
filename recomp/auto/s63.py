from g import *
init(); load('nearshrine'); run(2)
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
tap('START',6,60)
prev=(blk(P,0x1AC),blk(0x03000000,0x8000))
for k in ['RT','RT','D','LT','U']:
    tap(k,6,30)
    cur=(blk(P,0x1AC),blk(0x03000000,0x8000))
    d1=[(hex(i),prev[0][i],cur[0][i]) for i in range(0x1AC) if prev[0][i]!=cur[0][i]]
    d2=[(hex(0x03000000+i),prev[1][i],cur[1][i]) for i in range(0x8000) if prev[1][i]!=cur[1][i] and not (0x3c00<=i<0x3c00+0x358)]
    print(k,d1,d2[:30])
    prev=cur
