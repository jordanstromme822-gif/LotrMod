#!/usr/bin/env python3
"""Frodo's in-between facing pictures for the 16-facing walk test (tools/turn16/turn16.c).

  python3 -I gen16.py <original ROM .gba> <out fr16.bin> [sheet.png]

The game draws Frodo in 5 directions (up, up-right, right, down-right, down; the left side is mirrored), 12 walk
and 12 standing pictures each. For every pair of neighbouring directions this makes the picture half-way between,
frame by frame: each pixel of one picture is matched to the nearest pixel of the same colour group in the other
(skin, leather, rust, shadow, cloak), the matches are smoothed, and both pictures are moved half-way and merged,
then holes are filled and specks dropped. The result is laid out like the game's own anim table (0x0806170C) for
ROM 0x0808A000: a copy of the table with kinds 4 (stand) and 6 (walk) pointing at 4 in-between directions, each
with raw 4bpp tiles, the neighbour's frame header, hitboxes and timing, and OAM parts packed around the picture.

The output is made from the game's own art: keep it out of the repository (the Play Room page carries it).
Needs unicorn (pip) to run the game's own picture unpacker (IWRAM code copied from ROM 0xD1D4 to 0x03003940).
"""
import struct, sys
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR
ROM = open(sys.argv[1], 'rb').read()
DECODER = 0x03003940            # the game's unpacker, copied to IWRAM at boot from ROM 0xD1D4 (0x1F8 bytes)
def mk():
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    mu.mem_map(0x08000000, 0x1000000); mu.mem_write(0x08000000, ROM[:0x1000000])
    mu.mem_map(0x02000000, 0x40000); mu.mem_map(0x03000000, 0x8000)
    mu.mem_write(DECODER, ROM[0xD1D4:0xD1D4 + 0x1F8])
    mu.mem_map(0x06000000, 0x20000); mu.mem_map(0x0, 0x4000)
    return mu
def call(mu, fn, args):
    END = 0x1000
    mu.mem_write(END, b'\xfe\xe7')
    for r, a in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3], args): mu.reg_write(r, a)
    mu.reg_write(UC_ARM_REG_SP, 0x03007E00); mu.reg_write(UC_ARM_REG_LR, END | 1)
    mu.emu_start(fn | 1, END, count=50_000_000)

def u8(a): return ROM[a-0x8000000]
def u16(a): return struct.unpack_from('<H',ROM,a-0x8000000)[0]
def u32(a): return struct.unpack_from('<I',ROM,a-0x8000000)[0]
TBL=0x0806170C   # Frodo's anim table (hero object + 0x88)
def entry(kind,d):
    p=u32(TBL+4*kind); return struct.unpack_from('<III',ROM,p-0x8000000+16*d)
def frames(kind,d):
    tiles,hdr,_=entry(kind,d); n=u8(hdr+6); out=[]
    for f in range(n):
        rec=hdr+0xC+u16(hdr+0xC+2*f)
        fl=u8(rec); np_=fl&0x1f; w,h=u8(rec+2),u8(rec+3); toff=u16(rec+4); nb=u16(rec+6)
        po=rec+8+6*u8(hdr+0xB)+2*u8(hdr+0xA)
        parts=[]
        for k in range(np_):
            v=u32(po+4*k) if (po&3)==0 else struct.unpack_from('<I',ROM,po+4*k-0x8000000)[0]
            x=v&0x1ff; x-= 0x200 if x&0x100 else 0
            y=(v>>9)&0x1ff; y-=0x200 if y&0x100 else 0
            parts.append((x,y,(v>>20)&3,(v>>18)&3,v>>22))
        out.append(dict(rec=rec,fl=fl,w=w,h=h,toff=toff,nb=nb,parts=parts,src=tiles+toff))
    return out
SZ={(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),(1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),(2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}
def decode(fr):
    mu=mk()
    mu.mem_write(0x06010000,b'\0'*0x8000)
    t=fr['fl']>>5
    if t==0: data=ROM[fr['src']-0x8000000:fr['src']-0x8000000+fr['nb']]; return data
    if t==2:
        call(mu,0x0804E09C,[fr['src'],0x06010000,0x03007F00,DECODER])
    elif t==1:
        call(mu,0x0804DC6C,[fr['src'],0x06010000])
    return bytes(mu.mem_read(0x06010000,fr['nb']))
def render(fr,data,pal=None):
    # returns dict (x,y)->index, relative to object origin
    px={}
    for (x,y,sh,sz,tile) in fr['parts']:
        W,H=SZ[(sh,sz)]
        for ty in range(H//8):
            for tx in range(W//8):
                t=tile+ty*(W//8)+tx
                base=t*32
                for yy in range(8):
                    for xx in range(8):
                        b=data[base+yy*4+xx//2] if base+yy*4+xx//2<len(data) else 0
                        c=(b>>4) if xx&1 else (b&0xf)
                        if c: px[(x+tx*8+xx,y+ty*8+yy)]=c
    return px

GROUP={1:0,2:0,3:0,4:1,8:1,9:1,10:1,11:1,5:2,6:2,7:2,12:3,13:4,14:4,15:4}
def nearest(src,dst,R=7):
    # for each pixel of src find nearest pixel in dst with same group (prefer same index)
    disp={}
    dl={}
    for (x,y),c in dst.items(): dl.setdefault(GROUP.get(c,c),[]).append((x,y,c))
    for (x,y),c in src.items():
        best=None;bd=1e9
        for (u,v,cc) in dl.get(GROUP.get(c,c),[]):
            d=(u-x)**2+(v-y)**2 + (0 if cc==c else 2)
            if d<bd: bd=d;best=(u-x,v-y)
        if best is None or bd>R*R: best=None
        disp[(x,y)]=best
    # smooth: median of neighbours' displacements
    sm={}
    for (x,y),d in disp.items():
        xs=[];ys=[]
        for dx in range(-2,3):
            for dy in range(-2,3):
                e=disp.get((x+dx,y+dy))
                if e: xs.append(e[0]); ys.append(e[1])
        if xs:
            xs.sort(); ys.sort(); sm[(x,y)]=(xs[len(xs)//2],ys[len(ys)//2])
        else: sm[(x,y)]=None
    return sm
def morph(A,B,t=0.5):
    dA=nearest(A,B); dB=nearest(B,A)
    cand={}
    for (x,y),c in A.items():
        d=dA[(x,y)]
        if d is None: 
            if t<0.5: cand.setdefault((x,y),[]).append((1.0,c,0))  # unmatched part fades
            continue
        p=(round(x+t*d[0]),round(y+t*d[1])); cand.setdefault(p,[]).append((abs(t*d[0])+abs(t*d[1]),c,0))
    for (x,y),c in B.items():
        d=dB[(x,y)]
        if d is None:
            if t>=0.5: cand.setdefault((x,y),[]).append((1.0,c,1))
            continue
        p=(round(x+(1-t)*d[0]),round(y+(1-t)*d[1])); cand.setdefault(p,[]).append((abs((1-t)*d[0])+abs((1-t)*d[1]),c,1))
    out={}
    for p,l in cand.items():
        # prefer darker outline index? choose smallest travel, tie -> A
        l.sort(); out[p]=l[0][1]
    # fill 1-px holes: empty pixel with >=3 of 4 neighbours filled
    for _ in range(2):
        add={}
        xs=[x for x,y in out]; ys=[y for x,y in out]
        for x in range(min(xs),max(xs)+1):
            for y in range(min(ys),max(ys)+1):
                if (x,y) in out: continue
                nb=[out.get(q) for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))]
                nb=[c for c in nb if c]
                if len(nb)>=3: add[(x,y)]=max(set(nb),key=nb.count)
        out.update(add)
    # remove isolated single pixels
    out={p:c for p,c in out.items() if sum(((p[0]+dx,p[1]+dy) in out) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))>=1}
    return out

BASE=0x0808A000
KINDS=(4,6)
SHAPES=[(4,4,0,2),(4,2,1,2),(2,4,2,2),(2,2,0,1),(4,1,1,1),(1,4,2,1),(2,1,1,0),(1,2,2,0),(1,1,0,0)] # wcells,hcells,shape,size
def clean(px):
    # drop connected components smaller than 4 px
    seen=set(); out={}
    for p in px:
        if p in seen: continue
        comp=[p]; st=[p]; seen.add(p)
        while st:
            x,y=st.pop()
            for q in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if q in px and q not in seen: seen.add(q); comp.append(q); st.append(q)
        if len(comp)>=4:
            for q in comp: out[q]=px[q]
    return out
def pack(px):
    xs=[x for x,y in px]; ys=[y for x,y in px]
    x0,y0=min(xs),min(ys); W=(max(xs)-x0)//8+1; H=(max(ys)-y0)//8+1
    occ={(cx,cy) for (x,y) in px for cx,cy in [((x-x0)//8,(y-y0)//8)]}
    cov=set(); parts=[]
    while occ-cov:
        cy,cx=min((c[1],c[0]) for c in occ-cov)
        best=None
        for (w,h,sh,sz) in SHAPES:
            for ax in range(cx-w+1,cx+1):
                cells={(ax+i,cy+j) for i in range(w) for j in range(h)}
                new=len((cells&occ)-cov); waste=len(cells-(occ-cov))
                sc=new-0.6*waste
                if new and (best is None or sc>best[0]): best=(sc,ax,w,h,sh,sz,cells)
        _,ax,w,h,sh,sz,cells=best; cov|=cells
        parts.append((x0+ax*8,y0+cy*8,w,h,sh,sz))
    tiles=b''; enc=[]
    for (px0,py0,w,h,sh,sz) in parts:
        t0=len(tiles)//32
        for ty in range(h):
            for tx in range(w):
                for yy in range(8):
                    row=0
                    for xx in range(8):
                        x=px0+tx*8+xx; y=py0+ty*8+yy
                        # a pixel belongs to the first part that covers it
                        c=px.get((x,y),0)
                        owner=next(i for i,(a,b,ww,hh,_,__) in enumerate(parts) if a<=x<a+ww*8 and b<=y<b+hh*8)
                        if parts[owner][:2]!=(px0,py0): c=0
                        row|=c<<(4*xx)
                    tiles+=struct.pack('<I',row)
        v=(px0&0x1ff)|((py0&0x1ff)<<9)|(sz<<18)|(sh<<20)|(t0<<22)
        enc.append(struct.pack('<I',v))
    w_=max(x for x,y in px)-x0+1; h_=max(y for x,y in px)-y0+1
    return tiles,enc,w_,h_
def build():
    out=bytearray(); fix=[]
    def here(): return BASE+len(out)
    def align():
        while len(out)%4: out.append(0)
    # game table: copy all kind pointers
    nk=0
    while 0x08000000<=u32(TBL+4*nk)<0x09000000 and nk<64: nk+=1
    tbl_at=len(out); out+=b'\0'*(4*nk)
    ent_at={}
    for k in KINDS: ent_at[k]=len(out); out+=b'\0'*(16*4)
    sheet={}
    for k in KINDS:
        F=[frames(k,d) for d in range(5)]
        R=[[render(f,decode(f)) for f in F[d]] for d in range(5)]
        for j in range(4):
            n=min(len(F[j]),len(F[j+1]))
            tiles,hdr_src,_=entry(k,j)
            pics=[clean(morph(R[j][i],R[j+1][i])) for i in range(n)]
            sheet[(k,j)]=pics
            packed=[pack(p) for p in pics]
            # tiles blob
            align(); tile_addr=here(); toffs=[]
            for (tl,enc,w,h) in packed:
                toffs.append(len(out)-(tile_addr-BASE)); out.extend(tl)
            align(); hdr_addr=here()
            h=bytearray(ROM[hdr_src-0x8000000:hdr_src-0x8000000+12])
            h[6]=n; h[0xA]=0; h[0xB]=1
            mx=max(len(p[0]) for p in packed); h[8:10]=struct.pack('<H',mx)
            recs=[]
            for i,(tl,enc,w,hh) in enumerate(packed):
                src=F[j][i]['rec']; hb=ROM[src+8-0x8000000:src+14-0x8000000] if u8(hdr_src+0xB)==1 else b'\0'*6
                recs.append(bytes([len(enc),0,w,hh])+struct.pack('<HH',toffs[i],len(tl))+hb+b''.join(enc))
            offs=[]; body=b''
            base_off=2*n
            for r in recs:
                offs.append(base_off+len(body)); body+=r
                while len(body)%2: body+=b'\0'
            blob=bytes(h)+b''.join(struct.pack('<H',o) for o in offs)+body
            out.extend(blob)
            e=struct.pack('<III',tile_addr,hdr_addr,0)+bytes([u8(u32(TBL+4*k)+16*j+12),0,0,0])
            out[ent_at[k]+16*j:ent_at[k]+16*j+16]=e
    for k in range(nk):
        p=BASE+ent_at[k] if k in KINDS else u32(TBL+4*k)
        out[tbl_at+4*k:tbl_at+4*k+4]=struct.pack('<I',p)
    return bytes(out),sheet,nk
if __name__=='__main__':
    b,sheet,nk=build()
    assert len(b)<=0x9E400-0x8A000
    open(sys.argv[2],'wb').write(b); print('bytes',len(b),'kinds',nk)
