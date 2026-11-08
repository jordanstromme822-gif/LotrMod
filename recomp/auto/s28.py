from bot import *
from PIL import Image
init(); load('afterbot'); run(1)
W,H,g=colmap(); gw=W//8
x,y=pos(); cx,cy=x//8,y//8
for yy in range(cy-8,cy+9):
    print(''.join(('@' if (xx,yy)==(cx,cy) else ('.' if g[xx+yy*gw]==0 else '%x'%(g[xx+yy*gw]&15))) for xx in range(cx-20,cx+21)))
shot('ab2')
