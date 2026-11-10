import struct,subprocess,os,sys
from ex2 import mem
from kinds import recaddrs
from PIL import Image
L=int(sys.argv[1]); types=set(map(int,sys.argv[2].split(',')))
ew,iw=mem(L); hero=struct.unpack('<I',iw[0x3C00:0x3C04])[0]
rs=[r for a,r in recaddrs(L) if r[8] in types][:4]
d='/tmp/rc/sm/W%d'%L; os.makedirs(d,exist_ok=True); os.system('cp fight.state %s/'%d)
s='load fight\npoke 030041F8 %x\npoke 030041F4 5\npoke 030041F0 81\n600 -\n'%L
for i,r in enumerate(rs):
    x,y=struct.unpack('<HH',r[12:16])
    s+='poke 03003D90 01010000\npoke %08x %08x\npoke %08x %08x\n20 -\nshot a%d\n50 -\nshot b%d\n'%(hero+0xAC,(x+60)<<16,hero+0xB0,(y+20)<<16,i,i)
open(d+'/s.txt','w').write(s)
subprocess.run(['/tmp/rc/fx/run2','/tmp/rc/oh/rotk.gba',d+'/s.txt',d],capture_output=True,timeout=300)
sh=Image.new('RGB',(480,160*len(rs)))
for i in range(len(rs)):
    for j,c in enumerate('ab'):
        sh.paste(Image.open(d+'/%s%d.ppm'%(c,i)),(240*j,160*i))
sh.save(d+'/sheet.png')
