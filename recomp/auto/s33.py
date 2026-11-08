from bot import *
init(); load('moriaE'); run(1)
pl=0x03003C00
print('flags19a',hex(r8(pl+0x19a)),'opt',hex(r8(0x03002083)),hex(r8(0x03005820)))
import struct
inv=[r32(pl+o) for o in range(0x3c,0x5c,4)]; print('equip',[hex(v) for v in inv])
bp=[r32(pl+0x5c+4*i) for i in range(24)]; print('pack',[hex(v) for v in bp])
print([hex(r8(pl+o)) for o in range(0x180,0x1ac)])
