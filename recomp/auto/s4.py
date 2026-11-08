from g import *
import struct
init(); load('moria0'); run(2)
h=r32(0x03003C00)
a=blk(h,0x120)
for o in range(0,0x120,16): print(hex(o), ' '.join('%08x'%struct.unpack_from('<I',a,o+i)[0] for i in range(0,16,4)))
