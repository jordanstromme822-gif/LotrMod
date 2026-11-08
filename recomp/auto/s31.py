from bot import *
init(); load('afterbot'); run(1)
W,H,g=colmap(); gw=W//8
x,y=pos(); cx,cy=x//8,y//8; print(x,y)
for yy in range(cy-12,cy+14):
    print(''.join(('@' if (xx,yy)==(cx,cy) else ('.' if g[xx+yy*gw]==0 else '%x'%(g[xx+yy*gw]&15))) for xx in range(cx-25,cx+21)))
G=(W,H,g); prev=dists(G,x,y); p=pathto(prev,962,1099); print(p[:12] if p else None)
