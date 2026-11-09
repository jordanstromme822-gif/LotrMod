import struct,sys
rom=open('/tmp/rc/oh/rotk.gba','rb').read()
LEN=rom[0x58210:0x58210+80]
def load(L):
    d=open('/tmp/rc/sm/L%d/dump.bin'%L,'rb').read()
    p,lv=struct.unpack('<II',d[:8]); mem=d[8:]
    return p,lv,mem
def scripts(L):
    p,lv,mem=load(L)
    o=p-0x02030000
    if not (0<=o<len(mem)): return lv,None
    n=struct.unpack('<H',mem[o:o+2])[0]
    out=[]
    for i in range(n):
        off=struct.unpack('<H',mem[o+2+2*i:o+4+2*i])[0]
        q=o+off; cmds=[]
        for _ in range(200):
            if q+4>len(mem): break
            op=struct.unpack('<I',mem[q:q+4])[0]
            if op==0 or op>70: cmds.append(('end',op)); break
            ln=LEN[op]; cmds.append((op,mem[q+4:q+ln].hex())); q+=ln
        out.append(cmds)
    return lv,out
if __name__=='__main__':
    for L in range(1,130):
        lv,s=scripts(L)
        ex=[]
        if s:
            for i,c in enumerate(s):
                for op,a in c:
                    if op==28: b=bytes.fromhex(a); ex.append((i,b[2] if len(b)>2 else None,b.hex()))
        print(L,lv,'nscripts',len(s) if s else None,'exits',ex)
