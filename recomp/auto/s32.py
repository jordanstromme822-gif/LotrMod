from bot import *
init(); load('afterbot'); run(1)
print(pos()); shot('st1')
for k in ['LT','U','D','RT','LT+U','LT+D']:
    load('afterbot'); run(1); run(20,k); print(k,pos(), hex(r8(r32(0x03003C00)+0x62)))
