from g import *
import struct
init(); load('near1'); run(2)
pl=0x03003C00
a=blk(pl,0x1ac)
print([ (hex(o),struct.unpack_from('<H',a,o)[0]) for o in range(0,0x1ac,2) if 0<struct.unpack_from('<H',a,o)[0]<2000])
