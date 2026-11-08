from g import *
from PIL import Image
init(); load('fight'); run(2)
t=0x20177f0
ims=[]
for i in range(8):
    x,y=pos(); ex,ey=pos(t)
    run(2,steer(x,y,ex,ey)); run(3,'A'); shot('t%d'%i); ims.append(Image.open('t%d.png'%i).copy()); run(7)
c=Image.new('RGB',(960,1280))
for i,im in enumerate(ims): c.paste(im,((i%2)*480,(i//2)*320))
c.save('fr.png')
