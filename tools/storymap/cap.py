import struct,subprocess,os,sys,shutil
from ex2 import mem
from PIL import Image
OUT='/tmp/rc/sm/maps'; os.makedirs(OUT,exist_ok=True)
def cap(L, maxx=3000, maxy=2600, sx=160, sy=100):
    ew,iw=mem(L); hero=struct.unpack('<I',iw[0x3C00:0x3C04])[0]
    d='/tmp/rc/sm/P%d'%L; shutil.rmtree(d,ignore_errors=True); os.makedirs(d); shutil.copy('fight.state',d)
    s='load fight\npoke 030041F8 %x\npoke 030041F4 5\npoke 030041F0 81\n600 -\n3 A\n30 -\n3 A\n30 -\nlayer 4 0\n'%L
    if L in (115,116,117): s+='layer 1 0\n'
    pts=[(x,y) for y in range(0,maxy,sy) for x in range(0,maxx,sx)]
    for i,(x,y) in enumerate(pts):
        X=(x+120)<<16; Y=(y+80)<<16
        s+=''.join('poke %08x %08x\n'%(hero+o,v) for o,v in ((0xA4,X),(0xAC,X),(0xCC,X),(0xA8,Y),(0xB0,Y),(0xD0,Y)))
        s+='12 -\n'+''.join('poke %08x %08x\n'%(hero+o,v) for o,v in ((0xA4,X),(0xAC,X),(0xCC,X),(0xA8,Y),(0xB0,Y),(0xD0,Y)))
        s+='12 -\nshot s%d\ndump 030020F8 8\ndump 030041B0 4\ndump 03004174 4\n'%i
    open(d+'/s.txt','w').write(s)
    subprocess.run(['/tmp/rc/fx/run2','/tmp/rc/sm/noexit.gba',d+'/s.txt',d],capture_output=True,timeout=1200)
    D=open(d+'/dump.bin','rb').read(); shots=[]
    for i in range(len(pts)):
        cx,_,cy,_=struct.unpack('<hhhh',D[i*16:i*16+8]); st=D[i*16+8]; lv=D[i*16+12]
        if st==1 and lv==L: shots.append((cx,cy,i))
    if not shots: return None
    seen={}; 
    for cx,cy,i in shots: seen.setdefault((cx,cy),i)
    mx=max(c[0] for c in seen)+240; my=max(c[1] for c in seen)+136
    nx=min(c[0] for c in seen); ny=min(c[1] for c in seen)
    can=Image.new('RGB',(mx-nx,my-ny))
    for (cx,cy),i in sorted(seen.items()):
        im=Image.open(d+'/s%d.ppm'%i).crop((0,0,240,136)); can.paste(im,(cx-nx,cy-ny))
    can.save(OUT+'/L%d.png'%L); shutil.rmtree(d)
    return can.size,len(seen),(nx,ny)
if __name__=='__main__':
    for L in map(int,sys.argv[1:]): print(L,cap(L),flush=True)
