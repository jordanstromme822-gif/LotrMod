import struct,subprocess,os,sys
from ex2 import mem, rd
from collections import Counter,defaultdict
rom=open('/tmp/rc/oh/rotk.gba','rb').read()
HP=lambda k: struct.unpack('<H',rom[0x57518+k*20+6:0x57518+k*20+8])[0]
def recaddrs(L):
    ew,iw=mem(L); p=struct.unpack('<I',iw[0x3234:0x3238])[0]
    G=struct.unpack('<H',rd(ew,iw,p,2))[0]; out=[]
    for g in range(G):
        go=struct.unpack('<H',rd(ew,iw,p+2+2*g,2))[0]; gb=p+go; m=struct.unpack('<H',rd(ew,iw,gb,2))[0]
        for k in range(m):
            io=struct.unpack('<H',rd(ew,iw,gb+2+2*k,2))[0]; out.append((gb+io, rd(ew,iw,gb+io,20)))
    return out
def run(L):
    ew,iw=mem(L); hero=struct.unpack('<I',iw[0x3C00:0x3C04])[0]
    rs=[(a,r) for a,r in recaddrs(L) if r[8] not in (3,11,12,17,18)]
    d='/tmp/rc/sm/K%d'%L; os.makedirs(d,exist_ok=True); os.system('cp fight.state %s/; rm -f %s/dump.bin'%(d,d))
    s='load fight\npoke 030041F8 %x\npoke 030041F4 5\npoke 030041F0 81\n600 -\n'%L
    for a,r in rs:
        x,y=struct.unpack('<HH',r[12:16])
        s+='poke 03003D90 01010000\npoke %08x %08x\npoke %08x %08x\n40 -\ndump 02000000 40000\n'%(hero+0xAC,(x+30)<<16,hero+0xB0,y<<16)
    open(d+'/s.txt','w').write(s)
    subprocess.run(['/tmp/rc/fx/run2','/tmp/rc/oh/rotk.gba',d+'/s.txt',d],capture_output=True,timeout=600)
    D=open(d+'/dump.bin','rb').read(); kinds=defaultdict(set)
    for i,(a,r) in enumerate(rs):
        m=D[i*0x40000:(i+1)*0x40000]
        o=struct.unpack('<I',m[a-0x02000000:a-0x02000000+4])[0]
        if o>>24!=2: continue
        k=m[(o&0x3ffff)+0x61]; kinds[r[8]].add(k)
    return kinds
if __name__=='__main__':
    for L in map(int,sys.argv[1:]):
        k=run(L); allk=sorted(set().union(*k.values())) if k else []
        print(L,{t:sorted(v) for t,v in k.items()},'| big:',[(x,HP(x)) for x in allk if HP(x)>=150])
