import struct
R=open('/tmp/rc/auto/game.gba','rb').read()
T=0x08068F50
def u32(a): return struct.unpack_from('<I',R,a-0x08000000)[0]
def catw(c,k): return u32(T+c*0x28+4*k)
def flags(item):
    c=item&15; i=(item>>8)&255
    return u32(catw(c,8)+8*i)
def pairs(item):
    c=item&15; i=(item>>8)&255; pre=(item>>16)&255; suf=item>>24
    out=[]
    def ent(base,j):
        o=base-0x08000000+12*j
        return R[o:o+12]
    for e in [ent(catw(c,0),i)]+([ent(catw(c,2),pre)] if pre!=255 and c!=7 else [])+([ent(catw(c,5),suf)] if suf!=255 else []):
        for k in range(3,11,2):
            s,v=e[k],struct.unpack('b',e[k+1:k+2])[0]
            if s!=0x5a: out.append((s,v))
    return out
def reqlevel(item):
    c=item&15; i=(item>>8)&255; pre=(item>>16)&255; suf=item>>24
    r=R[catw(c,0)-0x08000000+12*i+2]
    f=flags(item)
    if f&0x80: r+=5
    if f&0x100: r+=5
    if pre!=255 and c!=7:
        r+=R[catw(c,2)-0x08000000+12*pre+2]>>1
        pf=u32(catw(c,3)+4*pre); r+=5*bool(pf&1)+5*bool(pf&2)
    if suf!=255:
        r+=R[catw(c,5)-0x08000000+12*suf+2]
        sf=u32(catw(c,6)+4*suf); r+=5*bool(sf&1)+5*bool(sf&2)
    if f&0x10000: r=1
    return r&255
