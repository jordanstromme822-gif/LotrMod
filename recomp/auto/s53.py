from g import *
init()
for st,fn,tx,ty in [('godE2',0x80200c9,1385,1214),('god_1000',0x8043c8d,1626,715),('god_2250',0x8036851,1613,1103)]:
    load(st); run(1)
    W,H,gm=colmap(); gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
    go((W,H,gm),tx,ty+40,maxsteps=600,near=10)
    run(30); print(hex(fn),pos()); shot(f'e2_{fn:x}')
