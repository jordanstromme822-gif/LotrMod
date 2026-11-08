from g import *
from PIL import Image
init(); load('moria0'); run(2)
W,H,g=colmap(); print(W,H)
from collections import Counter; print(Counter(g))
pal={0:(40,40,40),1:(200,0,0),2:(200,200,0)}
im=Image.new('RGB',(W//8,H//8))
im.putdata([pal.get(v,(0,0,255-v*20)) for v in g])
h=r32(0x03003C00)
p=0x2017938
while p:
    x,y=r16(p+0xae),r16(p+0xb2)
    if 0<=x<W and 0<=y<H: im.putpixel((x//8,y//8),(0,255,0) if r32(p+0x18)==0x8014e09 else (255,255,255))
    p=r32(p+4)
im.resize((W//2,H//2),Image.NEAREST).save('cmap.png')
