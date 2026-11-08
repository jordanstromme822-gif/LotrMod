from g import *
import struct
init(); load('moria0'); run(2)
h=r32(0x03003C00)
p=h; seen=0
while p and seen<200:
    print(hex(p), 'upd',hex(r32(p+0x14)),hex(r32(p+0x18)),hex(r32(p+0x1c)),'f20',hex(r32(p+0x20)),'x',r16(p+0xae),'y',r16(p+0xb2))
    p=r32(p+4); seen+=1
