from g import *
import struct
init(); load('shopopen'); run(2)
def find(v):
    out=[]
    for base,n in ((0x03000000,0x8000),(0x02000000,0x40000)):
        b=blk(base,n)
        for i in range(0,n-3,2):
            if struct.unpack_from('<H',b,i)[0]==v: out.append(base+i)
    return out
c1=find(1245); print([hex(a) for a in c1][:20])
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
pb=blk(P,0x1AC)
tap('LT',6,30)
for i in range(3):
    tap('A',6,40); 
    print('after A', [ (hex(a),r16(a)) for a in c1][:10])
pb2=blk(P,0x1AC)
print([(hex(i),pb[i],pb2[i]) for i in range(0x1AC) if pb[i]!=pb2[i]])
shot('buy3')
