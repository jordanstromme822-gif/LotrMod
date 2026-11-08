from g import *
init(); load('shopopen'); run(2)
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
tap('LT',6,30)
seq=['A','U','A','A','U','A','A','U','A','A']
for i,k in enumerate(seq):
    tap(k,6,40)
    print(i,k,'gems',r16(P+0x184),'1aa',hex(r8(P+0x1aa)),hex(r8(P+0x1ab)),hex(r8(P+0x1a8)),hex(r8(P+0x1a9)))
    shot(f'b{i}')
