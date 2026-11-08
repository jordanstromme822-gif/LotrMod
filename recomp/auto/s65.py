from g import *
init(); load('nearshrine'); run(2)
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
print('pack',[hex(r32(P+0x5c+4*i)) for i in range(8)], 'gems', r16(P+0x184))
tap('START',6,60); tap('RT',6,30); tap('A',6,40); tap('D',6,30); tap('A',6,40); shot('dc0')
print('pack',[hex(r32(P+0x5c+4*i)) for i in range(8)])
tap('A',6,40); shot('dc1')
print('pack',[hex(r32(P+0x5c+4*i)) for i in range(8)], 'gems', r16(P+0x184), 'state', r8(0x030041B0))
from PIL import Image
W=Image.new('RGB',(960,320))
for i in range(2): W.paste(Image.open(f'/tmp/rc/auto/dc{i}.png'),(i*480,0))
W.save('/tmp/rc/auto/dc.png')
