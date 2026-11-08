from g import *
init(); load('nearforge'); run(2); tap('R',6,60)
for i,k in enumerate(['LT','LT']):
    tap(k,6,30); shot(f'fl{i}')
from PIL import Image
W=Image.new('RGB',(960,320))
for i in range(2): W.paste(Image.open(f'/tmp/rc/auto/fl{i}.png'),(i*480,0))
W.save('/tmp/rc/auto/fl.png')
