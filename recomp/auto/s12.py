from g import *
init(); load('moria0'); run(2)
G=colmap()
print(go(G,1160,460)); shot('m1'); print(pos())
for p in entities():
    if r32(p+0x18)==0x8014e09: print(hex(p),hex(r32(p+0x14)),pos(p))
