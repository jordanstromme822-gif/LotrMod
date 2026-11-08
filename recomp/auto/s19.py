from g import *
import numpy as np
init(); load('fight'); run(2)
t=0x20177f0
snaps=[]
def snap(): return np.frombuffer(blk(0x02000000,0x40000)+blk(0x03000000,0x8000),dtype='<u2').copy()
for i in range(120):
    x,y=pos(); ex,ey=pos(t)
    run(2,steer(x,y,ex,ey)); run(4,'A'); run(6)
    snaps.append(snap())
S=np.array(snaps)
d=np.diff(S.astype(np.int32),axis=0)
dec=(d<0).sum(0); inc=(d>0).sum(0)
idx=np.where((dec>=2)&(inc==0))[0]
for k in idx[:60]:
    a=k*2; addr=(0x02000000+a) if a<0x40000 else (0x03000000+a-0x40000)
    print(hex(addr),S[0,k],S[-1,k],dec[k])
