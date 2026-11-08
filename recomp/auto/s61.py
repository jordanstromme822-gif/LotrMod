from g import *
init(); load('nearshrine'); run(2)
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
print('equip',[hex(r32(P+0x3c+4*i)) for i in range(8)])
print('pack',[hex(r32(P+0x5c+4*i)) for i in range(8)])
tap('START',6,60); shot('st0'); tap('RT',6,30); shot('st1'); tap('RT',6,30); shot('st2')
from PIL import Image
W=Image.new('RGB',(960,640))
for i in range(3): W.paste(Image.open(f'/tmp/rc/auto/st{i}.png'),((i%2)*480,(i//2)*320))
W.save('/tmp/rc/auto/st.png')
