#!/usr/bin/env python3
"""In-between facing pictures for enemies (walk and stand), like gen16all.py for heroes.

  python3 -I genenemy.py <original ROM .gba> <out enemy16.bin> [base, default 0x09080000]

Enemy species s (object + 0x61) has 6 anim sets at 0x08056820 + 24 s (0 walk, 1 stand, 2 attack, ...); each set is
5 entries of 16 bytes {tiles, frames header, 0, hold}, one per drawn direction (DIR5). Many species share sets.
For each distinct walk and stand set this makes 4 in-between entries (between drawn directions d and d + 1).
Output: u32 address of SP[82][2] (ours for species s walk / stand, 0 = none), then 70 x {game's set, ours} (ours = 4 entries of 16 bytes), then the pictures.
Enemy palettes aren't known here, so colours match by palette index (neighbouring indexes are the same colour ramp).
Made from the game's own art: keep it out of the repository.
"""
import struct, sys, os, numpy as np
ROMPATH=sys.argv[1]; OUT=sys.argv[2]; BASE=int(sys.argv[3],16) if len(sys.argv)>3 else 0x09080000
sys.argv=[sys.argv[0],ROMPATH]
G=os.path.join(os.path.dirname(os.path.abspath(__file__)),'gen16all.py')
exec(open(G).read().split("if __name__")[0])
ET=0x08056820
def setframes(p,d):
    tiles,hdr,_=struct.unpack_from('<III',ROM,p-0x8000000+16*d); n=u8(hdr+6); out=[]
    for f in range(n):
        rec=hdr+0xC+u16(hdr+0xC+2*f)
        fl=u8(rec); np_=fl&0x1f; w,h=u8(rec+2),u8(rec+3); toff=u16(rec+4); nb=u16(rec+6)
        po=rec+8+6*u8(hdr+0xB)+2*u8(hdr+0xA); parts=[]
        for k in range(np_):
            v=struct.unpack_from('<I',ROM,po+4*k-0x8000000)[0]
            x=v&0x1ff; x-= 0x200 if x&0x100 else 0
            y=(v>>9)&0x1ff; y-=0x200 if y&0x100 else 0
            parts.append((x,y,(v>>20)&3,(v>>18)&3,v>>22))
        out.append(dict(rec=rec,fl=fl,w=w,h=h,toff=toff,nb=nb,parts=parts,src=tiles+toff))
    return out
IDX=np.arange(16); C=np.where(abs(IDX[:,None]-IDX[None,:])<=2, 1.0+abs(IDX[:,None]-IDX[None,:])*0.8, np.inf); np.fill_diagonal(C,0.0)
sets=[]
for s in range(82):
    for k in (0,1):
        p=u32(ET+24*s+4*k)
        if 0x08000000<=p<0x09000000 and p not in sets: sets.append(p)
def build_set(out,p):
    def here(): return BASE+len(out)
    def align():
        while len(out)%4: out.append(0)
    F=[setframes(p,d) for d in range(5)]
    R=[[render(f,decode(f)) for f in F[d]] for d in range(5)]
    align(); ent_at=len(out); out+=b'\0'*64; sheet=[]
    for j in range(4):
        n=min(len(F[j]),len(F[j+1]))
        pics=[clean(morph(R[j][i],R[j+1][i],C)) for i in range(n)]
        pics=[q if q else R[j][i] for i,q in enumerate(pics)]
        sheet.append(pics)
        tiles,hdr_src,_=struct.unpack_from('<III',ROM,p-0x8000000+16*j)
        packed=[pack(q) for q in pics]
        align(); tile_addr=here(); toffs=[]
        for (tl,enc,w,hh) in packed: toffs.append(here()-tile_addr); out.extend(tl)
        align(); hdr_addr=here()
        hd=bytearray(ROM[hdr_src-0x8000000:hdr_src-0x8000000+12]); nb_=u8(hdr_src+0xB)
        hd[6]=n; hd[0xA]=0; hd[0xB]=1
        hd[8:10]=struct.pack('<H',max(len(q[0]) for q in packed))
        recs=[]
        for i,(tl,enc,w,hh) in enumerate(packed):
            src=F[j][i]['rec']; hb=ROM[src+8-0x8000000:src+14-0x8000000] if nb_>=1 else b'\0'*6
            assert toffs[i]<0x10000
            recs.append(bytes([len(enc),0,w,hh])+struct.pack('<HH',toffs[i],len(tl))+hb+b''.join(enc))
        offs=[]; body=b''
        for r in recs:
            offs.append(2*n+len(body)); body+=r
            while len(body)%2: body+=b'\0'
        out.extend(bytes(hd)+b''.join(struct.pack('<H',o) for o in offs)+body)
        out[ent_at+16*j:ent_at+16*j+16]=struct.pack('<III',tile_addr,hdr_addr,0)+ROM[p-0x8000000+16*j+12:p-0x8000000+16*j+16]
    return BASE+ent_at, sheet
if __name__=='__main__':
    import pickle
    out=bytearray(b'\0'*(4+8*len(sets))); pairs=[]; sheets={}
    for p in sets:
        a,sh=build_set(out,p); pairs.append((p,a)); sheets[p]=sh
        print(hex(p),hex(a),len(out),flush=True)
    for i,(p,a) in enumerate(pairs): out[4+8*i:12+8*i]=struct.pack('<II',p,a)
    while len(out)%4: out.append(0)
    sp=BASE+len(out); M=dict(pairs)             # SP[82][2]: ours for (species, walk / stand); word 0 points at it
    for s in range(82):
        for k in range(2): out+=struct.pack('<I',M.get(u32(ET+24*s+4*k),0))
    out[0:4]=struct.pack('<I',sp)
    open(OUT,'wb').write(out); pickle.dump(sheets,open(OUT+'.pkl','wb'))
    print('sets',len(sets),'bytes',len(out))
