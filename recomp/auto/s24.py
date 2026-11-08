from g import *
from PIL import Image
init(); load('moriaE'); run(2)
ims=[]
for k in ['A','B','R','L']:
    load('moriaE'); run(2); run(3,k); run(5); shot('k_'+k); ims.append(Image.open('k_'+k+'.png').copy())
c=Image.new('RGB',(960,640))
for i,im in enumerate(ims): c.paste(im,((i%2)*480,(i//2)*320))
c.save('keys.png')
