from g import *
import struct
init(); load('near1'); run(2)
G=colmap()
t=0x20177f0
hist=[]
pl=0x03003C00
for i in range(400):
    if r32(t+0x14)!=0x801b9d1: print('changed at',i,hex(r32(t+0x14))); break
    x,y=pos(); ex,ey=pos(t)
    if abs(ex-x)+abs(ey-y)>30:
        path=bfs(*G,x,y,lambda c:abs(c[0]-ex//8)<=2 and abs(c[1]-ey//8)<=2)
        if path: wp=path[min(3,len(path)-1)]; run(4,steer(x,y,wp[0]*8+4,wp[1]*8+4))
        else: run(4)
    else:
        run(2,steer(x,y,ex,ey)); run(4,'A'); run(6)
    hist.append((blk(t,0x148),blk(pl,0x1ac)))
shot('f2')
# enemy fields monotonic nonincreasing with >=3 decreases
def mono(idx,n):
  for o in range(0,n,2):
    v=[struct.unpack_from('<H',h[idx],o)[0] for h in hist]
    dec=sum(1 for a,b in zip(v,v[1:]) if b<a); inc=sum(1 for a,b in zip(v,v[1:]) if b>a)
    if dec>=2 and inc<=1: print(idx,hex(o),v[0],v[-1],dec,inc)
mono(0,0x148); mono(1,0x1ac)
