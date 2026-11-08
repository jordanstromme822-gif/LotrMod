from g import *
init()
allt={}
for st in ['moriaE','godE2','godE3']+[f'god_{i}' for i in range(0,4001,250)]:
    load(st)
    run(2)
    if r8(0x030041F8)!=82: continue
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    for e in lst:
        f=r32(e+0x14)
        allt.setdefault(f,set()).add((r16(e+0xae),r16(e+0xb2),r8(e+0x60),r8(e+0x63)))
for f,s in sorted(allt.items(),key=lambda t:-len(t[1])): print(hex(f),len(s),sorted(s)[:6])
