import struct
def a4(n): return (n+3)&~3
def parse_groups(src):
    """src = part buffer starting at part+8"""
    G=src[0]; groups=[]
    for g in range(G):
        go=struct.unpack('<H',src[2+2*g:4+2*g])[0]; grp=src[go:]
        m=grp[0]; sizes=list(grp[2:2+m]); p=a4(m+2); items=[]
        for n in sizes: items.append(bytes(grp[p:p+n])); p+=n
        groups.append(dict(b1=grp[1],items=items))
    return groups
def build_groups(groups):
    G=len(groups); hdr=bytearray([G,0])+bytearray(2*G)
    while len(hdr)%4: hdr.append(0)
    body=bytearray()
    for g,gr in enumerate(groups):
        struct.pack_into('<H',hdr,2+2*g,len(hdr)+len(body))
        m=len(gr['items']); b=bytearray([m,gr.get('b1',0)])+bytes(len(x) for x in gr['items'])
        while len(b)%4: b.append(0)
        for x in gr['items']: b+=x
        while len(b)%4: b.append(0)
        body+=b
    return bytes(hdr+body)
