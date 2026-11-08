from g import *
init(); load('godE2'); run(1)
W,H,gm=colmap(); gm=bytearray(0 if (v&7) not in (1,2) else 1 for v in gm)
go((W,H,gm),1385,1214,maxsteps=600,near=40); print(pos())
save('nearshrine')
for k in ['A','R','B','L']:
    load('nearshrine'); run(2); tap(k,6,60); shot('sh_'+k)
