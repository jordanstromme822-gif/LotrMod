from g import *
init(); load('god_2250'); run(1)
def lstents():
    p=r32(0x03003C00); seen=set(); lst=[]
    q=p
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q+4)
    q=r32(p)
    while q and q not in seen: seen.add(q); lst.append(q); q=r32(q)
    return lst
x,y=pos(); print(pos())
for e in lstents():
    f=r32(e+0x14)
    if f in (0x8036851,0x8046125,0x8014a3d):
        ex,ey=r16(e+0xae),r16(e+0xb2)
        if abs(ex-x)<130 and abs(ey-y)<90: print(hex(f),ex-x,ey-y,r8(e+0x63))
shot('bar0')
