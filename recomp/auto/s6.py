from g import *
import struct
init(); load('moria0'); run(2)
for p in (0x20157e8,0x2017938):
  a=blk(p,0x148); print(hex(p))
  for o in range(0,0x148,16): print(hex(o), ' '.join('%08x'%struct.unpack_from('<I',a,o+i)[0] for i in range(0,16,4) if o+i+4<=0x148))
