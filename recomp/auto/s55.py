from g import *
init(); load('nearshrine'); run(2); tap('R',6,60); save('shopopen')
import sys
seqs=sys.argv[1:]
for i,s in enumerate(seqs):
    load('shopopen'); run(2)
    for k in s.split(','): tap(k,6,30)
    run(30); shot(f'sp{i}')
from PIL import Image
W=Image.new('RGB',(960,320*((len(seqs)+1)//2)))
for i in range(len(seqs)): W.paste(Image.open(f'/tmp/rc/auto/sp{i}.png'),((i%2)*480,(i//2)*320))
W.save('/tmp/rc/auto/sp.png')
