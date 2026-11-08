from bot import *
init(); load('afterbot'); run(1)
G=colmap(); x,y=pos(); print(x,y)
prev=dists(G,x,y); xs=[c[0] for c in prev]; ys=[c[1] for c in prev]
print(len(prev),min(xs),max(xs),min(ys),max(ys))
h=r32(0x03003C00); print(hex(h), r16(h+0xae), r16(h+0xb2), r16(h+0xce), r16(h+0xd2))
