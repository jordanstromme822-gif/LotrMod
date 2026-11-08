from g import *
init(); load('shopopen'); run(2)
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
tap('LT',6,30)
for i in range(16):
    tap('A',6,30); tap('A',6,30)
    print(i,'gems',r16(P+0x184),'1aa',hex(r8(P+0x1aa)), 'u16 1a8', hex(r16(P+0x1a8)))
shot('full')
