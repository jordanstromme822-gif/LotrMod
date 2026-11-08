from g import *
init(); load('moria0'); run(2)
h=r32(0x03003C00); print('hero',hex(h))
a=blk(h,0x100)
run(30,'RT'); b=blk(h,0x100)
run(30,'D'); c=blk(h,0x100)
import struct
for o in range(0,0x100,2):
    x,y,z=[struct.unpack_from('<h',v,o)[0] for v in (a,b,c)]
    if x!=y or y!=z: print(hex(o),x,y,z)
