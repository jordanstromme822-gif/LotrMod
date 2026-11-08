from bot3 import *
import sys
init(); load(sys.argv[1]); run(1)
GOD=len(sys.argv)>4
import random; random.seed(1)
same=0; lastt=None
b=Bot(); pl=0x03003C00
done=0
for i in range(int(sys.argv[2])):
    if r8(0x030041B0)!=1 or r16(pl+0x17c)==0 or r16(pl+0x17c)>2000: run(10); continue
    L.w16(pl+0x17c,r16(pl+0xd0)) if GOD else None
    r=b.tick()
    if b.log: print(i,b.log); b.log.clear()
    if i%200==0: print(i,r,flush=True)
    if i%250==0: save('god_%d'%i)
    same = same+1 if r[1:2]==lastt else 0; lastt=r[1:2]
    if same>400: print('STUCK',i,r); break
    if r[0]=='done':
        done+=1
        if done>20: print('DONE',i,r); break
        run(4)
    else: done=0
save(sys.argv[3]); shot(sys.argv[3])
print('equip',[hex(r32(pl+0x3c+4*s)) for s in range(8)]); print('pack',[hex(r32(pl+0x5c+4*s)) for s in range(17)])
