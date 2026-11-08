from bot import *
from PIL import Image
init(); load('afterbot'); run(1)
G=colmap(); W,H,g=G; gw=W//8
x,y=pos(); prev=dists(G,x,y)
pal={0:(40,40,40),1:(200,0,0),2:(200,200,0)}
im=Image.new('RGB',(gw,H//8)); im.putdata([pal.get(v,(0,0,200)) for v in g])
for c in prev: im.putpixel(c,(0,140,0))
en,items,trig=scan()
for p in en: im.putpixel((pos(p)[0]//8,pos(p)[1]//8),(255,255,255))
for p in trig: im.putpixel((pos(p)[0]//8,pos(p)[1]//8),(255,0,255))
im.putpixel((x//8,y//8),(255,128,0))
im.resize((W//2,H//2),Image.NEAREST).save('reach2.png')
