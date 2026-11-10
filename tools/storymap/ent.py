import struct,sys,os,shutil,subprocess,json
from ex2 import mem
from kinds import recaddrs
def run(L):
    ew,iw=mem(L); hero=struct.unpack('<I',iw[0x3C00:0x3C04])[0]
    ex=[r for a,r in recaddrs(L) if r[8]==3]
    out=[]
    for i,r in enumerate(ex):
        x,y=struct.unpack('<HH',r[12:16]); dest=r[19]; ent=r[18]
        d='/tmp/rc/sm/EN/%d_%d'%(L,i); shutil.rmtree(d,ignore_errors=True); os.makedirs(d); shutil.copy('fight.state',d)
        s='load fight\npoke 030041F8 %x\npoke 030041F4 5\npoke 030041F0 81\n600 -\n3 A\n30 -\n3 A\n30 -\n'%L
        for k in range(3):
            for off,v in ((0xA4,x),(0xAC,x),(0xCC,x),(0xA8,y),(0xB0,y),(0xD0,y)): s+='poke %08x %08x\n'%(hero+off,v<<16)
            s+='4 -\n'
        s+='dump 03004174 4\n500 -\n3 A\n30 -\n3 A\n60 -\ndump 03004174 4\ndump 03003C00 4\ndump 02000000 40000\n'
        open(d+'/s.txt','w').write(s)
        subprocess.run(['timeout','120','/tmp/rc/fx/run2','/tmp/rc/oh/rotk.gba',d+'/s.txt',d],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            b=open(d+'/dump.bin','rb').read(); l0=b[0]; l1=b[4]; hp=struct.unpack('<I',b[8:12])[0]; e=b[12:]
            o=hp-0x02000000; hx=struct.unpack('<H',e[o+0xAE:o+0xB0])[0]; hy=struct.unpack('<H',e[o+0xB2:o+0xB4])[0]
            out.append(dict(i=i,x=x,y=y,dest=dest,entry=ent,before=l0,after=l1,ax=hx,ay=hy))
        except Exception as ex_: out.append(dict(i=i,x=x,y=y,dest=dest,entry=ent,err=str(ex_)))
        shutil.rmtree(d,ignore_errors=True)
    json.dump(out,open('/tmp/rc/sm/EN/L%d.json'%L,'w')); print(L,out,flush=True)
for L in map(int,sys.argv[1:]): run(L)
