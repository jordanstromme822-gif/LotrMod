#!/usr/bin/env python3
"""In-between facing pictures for all 8 heroes (16-facing walk, tools/turn16/turn16.c).

  python3 -I gen16all.py <original ROM .gba> <out hero16.bin> [base address, default 0x09000000]

Generalises gen16.py (Frodo only) to every hero: hero id h has its anim table at 0x08282898 + 4h (object + 0x88) and
its sprite palette at 0x08282C68 + 4h. Colour matching uses the palette (RGB distance) instead of Frodo's hand-made
colour groups. Output: an index of 8 words (our table per hero id, 0 = none) followed by each hero's table copy and
pictures, laid out like gen16.py's. Made from the game's own art: keep it out of the repository.
"""
import struct, sys, numpy as np
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR
ROM = open(sys.argv[1], 'rb').read()
DECODER = 0x03003940
MU = None
def mk():
    global MU
    if MU: return MU
    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    mu.mem_map(0x08000000, 0x1000000); mu.mem_write(0x08000000, ROM[:0x1000000])
    mu.mem_map(0x02000000, 0x40000); mu.mem_map(0x03000000, 0x8000)
    mu.mem_write(DECODER, ROM[0xD1D4:0xD1D4 + 0x1F8])
    mu.mem_map(0x06000000, 0x20000); mu.mem_map(0x0, 0x4000)
    MU = mu; return mu
def call(mu, fn, args):
    END = 0x1000
    mu.mem_write(END, b'\xfe\xe7')
    for r, a in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3], args): mu.reg_write(r, a)
    mu.reg_write(UC_ARM_REG_SP, 0x03007E00); mu.reg_write(UC_ARM_REG_LR, END | 1)
    mu.emu_start(fn | 1, END, count=50_000_000)
def u8(a): return ROM[a-0x8000000]
def u16(a): return struct.unpack_from('<H',ROM,a-0x8000000)[0]
def u32(a): return struct.unpack_from('<I',ROM,a-0x8000000)[0]
HEROTBL = 0x08282898; HEROPAL = 0x08282C68
def entry(T,kind,d):
    p=u32(T+4*kind); return struct.unpack_from('<III',ROM,p-0x8000000+16*d)
def frames(T,kind,d):
    tiles,hdr,_=entry(T,kind,d); n=u8(hdr+6); out=[]
    for f in range(n):
        rec=hdr+0xC+u16(hdr+0xC+2*f)
        fl=u8(rec); np_=fl&0x1f; w,h=u8(rec+2),u8(rec+3); toff=u16(rec+4); nb=u16(rec+6)
        po=rec+8+6*u8(hdr+0xB)+2*u8(hdr+0xA)
        parts=[]
        for k in range(np_):
            v=struct.unpack_from('<I',ROM,po+4*k-0x8000000)[0]
            x=v&0x1ff; x-= 0x200 if x&0x100 else 0
            y=(v>>9)&0x1ff; y-=0x200 if y&0x100 else 0
            parts.append((x,y,(v>>20)&3,(v>>18)&3,v>>22))
        out.append(dict(rec=rec,fl=fl,w=w,h=h,toff=toff,nb=nb,parts=parts,src=tiles+toff))
    return out
SZ={(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),(1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),(2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}
def decode(fr):
    t=fr['fl']>>5
    if t==0: return ROM[fr['src']-0x8000000:fr['src']-0x8000000+fr['nb']]
    mu=mk(); mu.mem_write(0x06010000,b'\0'*0x8000)
    if t==2: call(mu,0x0804E09C,[fr['src'],0x06010000,0x03007F00,DECODER])
    elif t==1: call(mu,0x0804DC6C,[fr['src'],0x06010000])
    return bytes(mu.mem_read(0x06010000,fr['nb']))
def render(fr,data):
    px={}
    for (x,y,sh,sz,tile) in fr['parts']:
        W,H=SZ[(sh,sz)]
        for ty in range(H//8):
            for tx in range(W//8):
                base=(tile+ty*(W//8)+tx)*32
                for yy in range(8):
                    for xx in range(8):
                        i=base+yy*4+xx//2
                        b=data[i] if i<len(data) else 0
                        c=(b>>4) if xx&1 else (b&0xf)
                        if c: px[(x+tx*8+xx,y+ty*8+yy)]=c
    return px
def palette(h):
    a=u32(HEROPAL+4*h)
    return [((v&31)*8,((v>>5)&31)*8,((v>>10)&31)*8) for v in struct.unpack_from('<16H',ROM,a-0x8000000)]
def colcost(pal, T=110.0):
    """cost[c][cc]: 0 same index, up to 3 for close colours, inf (no match) beyond T."""
    P=np.array(pal,float); d=np.sqrt(((P[:,None,:]-P[None,:,:])**2).sum(-1))
    C=np.where(d<T, 1.0+2.0*(d/T)**2, np.inf); np.fill_diagonal(C,0.0); return C
def nearest(src,dst,C,R=7):
    S=np.array([(x,y,c) for (x,y),c in src.items()],float); D=np.array([(x,y,c) for (x,y),c in dst.items()],float)
    d2=((S[:,None,:2]-D[None,:,:2])**2).sum(-1)+C[S[:,2].astype(int)][:,D[:,2].astype(int)]
    j=d2.argmin(1); bd=d2[np.arange(len(S)),j]
    disp={}
    for i,(x,y,c) in enumerate(S):
        disp[(int(x),int(y))]=None if bd[i]>R*R else (int(D[j[i],0]-x),int(D[j[i],1]-y))
    sm={}
    for (x,y),d in disp.items():
        xs=[];ys=[]
        for dx in range(-2,3):
            for dy in range(-2,3):
                e=disp.get((x+dx,y+dy))
                if e: xs.append(e[0]); ys.append(e[1])
        if xs: xs.sort(); ys.sort(); sm[(x,y)]=(xs[len(xs)//2],ys[len(ys)//2])
        else: sm[(x,y)]=None
    return sm
def morph(A,B,C,t=0.5):
    if not A or not B: return dict(A or B)
    dA=nearest(A,B,C); dB=nearest(B,A,C)
    cand={}
    for (x,y),c in A.items():
        d=dA[(x,y)]
        if d is None:
            if t<0.5: cand.setdefault((x,y),[]).append((1.0,c,0))
            continue
        p=(round(x+t*d[0]),round(y+t*d[1])); cand.setdefault(p,[]).append((abs(t*d[0])+abs(t*d[1]),c,0))
    for (x,y),c in B.items():
        d=dB[(x,y)]
        if d is None:
            if t>=0.5: cand.setdefault((x,y),[]).append((1.0,c,1))
            continue
        p=(round(x+(1-t)*d[0]),round(y+(1-t)*d[1])); cand.setdefault(p,[]).append((abs((1-t)*d[0])+abs((1-t)*d[1]),c,1))
    out={}
    for p,l in cand.items(): l.sort(); out[p]=l[0][1]
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
    return {p:c for p,c in out.items() if sum(((p[0]+dx,p[1]+dy) in out) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))>=1}
KINDS=(4,6)
SHAPES=[(4,4,0,2),(4,2,1,2),(2,4,2,2),(2,2,0,1),(4,1,1,1),(1,4,2,1),(2,1,1,0),(1,2,2,0),(1,1,0,0)]
def clean(px):
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
    x0,y0=min(xs),min(ys)
    occ={((x-x0)//8,(y-y0)//8) for (x,y) in px}
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
                        c=px.get((x,y),0)
                        owner=next(i for i,(a,b,ww,hh,_,__) in enumerate(parts) if a<=x<a+ww*8 and b<=y<b+hh*8)
                        if parts[owner][:2]!=(px0,py0): c=0
                        row|=c<<(4*xx)
                    tiles+=struct.pack('<I',row)
        enc.append(struct.pack('<I',(px0&0x1ff)|((py0&0x1ff)<<9)|(sz<<18)|(sh<<20)|(t0<<22)))
    return tiles,enc,max(xs)-x0+1,max(ys)-y0+1
def hero_pics(h):
    T=u32(HEROTBL+4*h); C=colcost(palette(h)); sheet={}
    for k in KINDS:
        F=[frames(T,k,d) for d in range(5)]
        R=[[render(f,decode(f)) for f in F[d]] for d in range(5)]
        for j in range(4):
            n=min(len(F[j]),len(F[j+1]))
            sheet[(k,j)]=(F,R,[clean(morph(R[j][i],R[j+1][i],C)) for i in range(n)])
    return T,sheet
def build_hero(out,BASE,h,T,sheet):
    def here(): return BASE+len(out)
    def align():
        while len(out)%4: out.append(0)
    align()
    nk=0
    while 0x08000000<=u32(T+4*nk)<0x09000000 and nk<64: nk+=1
    start=here(); tbl_at=len(out); out+=b'\0'*(4*nk)
    ent_at={}
    for k in KINDS: ent_at[k]=len(out); out+=b'\0'*(16*4)
    for k in KINDS:
        for j in range(4):
            F,R,pics=sheet[(k,j)]; n=len(pics)
            tiles,hdr_src,_=entry(T,k,j)
            packed=[pack(p) for p in pics]
            align(); tile_addr=here(); toffs=[]
            for (tl,enc,w,hh) in packed: toffs.append(here()-tile_addr); out.extend(tl)
            align(); hdr_addr=here()
            hd=bytearray(ROM[hdr_src-0x8000000:hdr_src-0x8000000+12])
            hd[6]=n; hd[0xA]=0; hd[0xB]=1
            hd[8:10]=struct.pack('<H',max(len(p[0]) for p in packed))
            recs=[]
            for i,(tl,enc,w,hh) in enumerate(packed):
                src=F[j][i]['rec']
                hb=ROM[src+8-0x8000000:src+14-0x8000000] if u8(hdr_src+0xB)==1 else b'\0'*6
                assert toffs[i] < 0x10000
                recs.append(bytes([len(enc),0,w,hh])+struct.pack('<HH',toffs[i],len(tl))+hb+b''.join(enc))
            offs=[]; body=b''
            for r in recs:
                offs.append(2*n+len(body)); body+=r
                while len(body)%2: body+=b'\0'
            out.extend(bytes(hd)+b''.join(struct.pack('<H',o) for o in offs)+body)
            out[ent_at[k]+16*j:ent_at[k]+16*j+16]=struct.pack('<III',tile_addr,hdr_addr,0)+bytes([u8(u32(T+4*k)+16*j+12),0,0,0])
    for k in range(nk):
        p=BASE+ent_at[k] if k in KINDS else u32(T+4*k)
        out[tbl_at+4*k:tbl_at+4*k+4]=struct.pack('<I',p)
    return start, here()
if __name__=='__main__':
    import pickle, os
    BASE=int(sys.argv[3],16) if len(sys.argv)>3 else 0x09000000
    out=bytearray(b'\0'*0x40); idx=[]
    heroes=[int(x) for x in os.environ.get('HEROES','0 1 2 3 4 5 6 7').split()]
    for h in range(8):
        if h not in heroes: idx.append((0,0,0)); continue
        T,sheet=hero_pics(h)
        pickle.dump({kj:v[2] for kj,v in sheet.items()},open(f'/tmp/rc/g16/sheet{h}.pkl','wb'))
        s,e=build_hero(out,BASE,h,T,sheet); idx.append((T,s,e)); print('hero',h,hex(T),hex(s),'bytes',e-s,flush=True)
    for h,(T,s,e) in enumerate(idx): out[8*h:8*h+8]=struct.pack('<II',T,s)
    open(sys.argv[2],'wb').write(out); print('total',len(out))
