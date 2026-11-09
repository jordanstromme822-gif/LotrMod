import struct
def mem(L):
    d=open('/tmp/rc/sm/L%d/dump.bin'%L,'rb').read()
    return d[8+0x10000:8+0x50000], d[8+0x50000:8+0x58000]
def rd(ew,iw,a,n):
    if 0x02000000<=a<0x02040000: return ew[a-0x02000000:a-0x02000000+n]
    if 0x03000000<=a<0x03008000: return iw[a-0x03000000:a-0x03000000+n]
    return None
def groups(L):
    ew,iw=mem(L)
    p=struct.unpack('<I',iw[0x3234:0x3238])[0]
    n=struct.unpack('<H',rd(ew,iw,p,2))[0]
    G=[]
    for g in range(n):
        go=struct.unpack('<H',rd(ew,iw,p+2+2*g,2))[0]; gb=p+go
        m=struct.unpack('<H',rd(ew,iw,gb,2))[0]
        items=[]
        for k in range(m):
            io=struct.unpack('<H',rd(ew,iw,gb+2+2*k,2))[0]
            items.append(rd(ew,iw,gb+io,20))
        G.append(items)
    return G
if __name__=='__main__':
    for L in (51,109,13,30):
        G=groups(L); print(L,'groups',len(G),[len(x) for x in G])
        if len(G)>2:
            for it in G[2]: print('  ',it.hex(' '), 'lv',it[8+0xb],'entry',it[8+0xa])
