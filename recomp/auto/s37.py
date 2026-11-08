from bot2 import *
init(); load('bot2end'); run(1)
pl=0x03003C00
for i in range(30):
    run(20)
    en,items,trig=scan()
    print(i,hex(r8(0x030041B0)),pos() if r32(0x03003C00) else None,r16(pl+0x17c),len(en),len(trig),len(entities()) if r32(0x03003C00) else 0)
shot('dead')
