from g import *
from collections import Counter
init(); load('moriaE'); run(10)
E=entities()
# walk both directions
p=r32(0x03003C00); seen=set(); lst=[]
q=p
while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
q=r32(p)
while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
c=Counter(r32(e+0x14) for e in lst)
for k,v in c.most_common(): 
    ex=[e for e in lst if r32(e+0x14)==k][:3]
    print(hex(k),v,[(r16(e+0xae),r16(e+0xb2),hex(r8(e+0x60)),hex(r8(e+0x62)),hex(r8(e+0x63))) for e in ex])
print('hero',pos())
