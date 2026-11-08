from g import *
from PIL import Image
init(); load('moria0'); run(2)
W,H,g=colmap(); gw=W//8
h=r32(0x03003C00); x,y=r16(h+0xae),r16(h+0xb2)
seen=set()
import g as G
# flood: use bfs with impossible target and capture prev via monkeypatch
from collections import deque
def free(cx,cy): return g[cx+cy*gw]==0 and g[cx-1+cy*gw]==0 and g[cx+1+cy*gw]==0
s=(x//8,y//8); print(s, g[s[0]+s[1]*gw], free(*s)); q=deque([s]); seen={s}
while q:
    c=q.popleft()
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        n=(c[0]+dx,c[1]+dy)
        if n not in seen and 0<n[0]<gw-1 and 0<n[1]<H//8-1 and free(*n): seen.add(n); q.append(n)
pal={0:(40,40,40),1:(200,0,0),2:(200,200,0)}
im=Image.new('RGB',(gw,H//8)); im.putdata([pal.get(v,(0,0,200)) for v in g])
for c in seen: im.putpixel(c,(0,160,0))
im.resize((W//2,H//2),Image.NEAREST).save('reach.png'); print(len(seen))
