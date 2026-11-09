import struct,subprocess,os,sys,json
from ex2 import mem
from kinds import recaddrs
from concurrent.futures import ThreadPoolExecutor
def run(L):
    ew,iw=mem(L); hero=struct.unpack('<I',iw[0x3C00:0x3C04])[0]
    rs=[(a,r) for a,r in recaddrs(L) if r and r[8] not in (3,11,12,17,18)]
    d='/tmp/rc/sm/C%d'%L; os.makedirs(d,exist_ok=True); os.system('cp fight.state %s/; rm -f %s/dump.bin'%(d,d))
    s='load fight\npoke 030041F8 %x\npoke 030041F4 5\npoke 030041F0 81\n600 -\n3 A\n30 -\n3 A\n30 -\n'%L
    for a,r in rs:
        x,y=struct.unpack('<HH',r[12:16])
        s+='poke %08x %08x\npoke %08x %08x\n3 A\n3 -\n3 A\n24 -\ndump 02000000 40000\ndump 030041B0 4\n'%(hero+0xAC,(x+30)<<16,hero+0xB0,y<<16)
    open(d+'/s.txt','w').write(s)
    subprocess.run(['/tmp/rc/fx/run2','/tmp/rc/oh/rotk.gba',d+'/s.txt',d],capture_output=True,timeout=900)
    D=open(d+'/dump.bin','rb').read(); res=[]; R=0x40004
    for i,(a,r) in enumerate(rs):
        m=D[i*R:i*R+0x40000]; st=D[i*R+0x40000]
        o=struct.unpack('<I',m[a-0x02000000:a-0x02000000+4])[0]
        k=m[(o&0x3ffff)+0x61] if o>>24==2 else -1
        res.append((r[8],k,st))
    os.remove(d+'/dump.bin')
    return L,res
levels=[int(x) for x in sys.argv[1:]]
with ThreadPoolExecutor(4) as ex:
    out=dict(ex.map(run,levels))
json.dump(out,open('/tmp/rc/sm/counts.json','w'))
for L in levels:
    bad=sum(1 for t,k,st in out[L] if st!=1)
    print(L,len(out[L]),'notplay',bad)
