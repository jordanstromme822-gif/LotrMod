from g import *
init(); load('nearshrine'); run(2)
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
tap('START',6,60); tap('RT',6,30); tap('D',6,30); tap('B',6,60); print('state after B',r8(0x030041B0)); shot('cl0')
tap('START',6,60); shot('cl1'); 
tap('START',6,60); print('state after START',r8(0x030041B0)); 
from PIL import Image
W=Image.new('RGB',(960,320))
for i in range(2): W.paste(Image.open(f'/tmp/rc/auto/cl{i}.png'),(i*480,0))
W.save('/tmp/rc/auto/cl.png')
