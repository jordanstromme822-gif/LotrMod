from bot import *
from items import flags,pairs,reqlevel
import random
HERBS=set(range(15,25))
def wstat(s):
    if s<=6: return 3
    if s<=12: return 0.5
    if s<=15: return 2
    if s==16: return 1
    if s<=21: return 1.5
    if s==22: return 0.3
    if s==23: return 0.2
    if s==46: return 1
    return 0.4
def score(it): return sum(wstat(s)*v for s,v in pairs(it))
def slot_of(f):
    for s in range(8):
        if f&(1<<(18+s)): return s
    return -1
def wanted(pl,it):
    if it&15==15 or (it&15)==7: return False
    f=flags(it)
    if f&0x10000: return False
    hero=r8(pl+0x19f); hero=0 if hero==6 else hero
    if hero>=6 or not (f&(0x04000000<<hero)): return False
    s=slot_of(f)
    if s<0: return False
    if s==2 and (flags(r32(pl+0x40))&0x20000) and r32(pl+0x40)&15!=15: return False
    cur=r32(pl+0x3c+4*s)
    best=score(cur) if cur&15!=15 else -1e9
    for k in range(8):
        b=r32(pl+0x5c+4*k)
        if b&15!=15 and slot_of(flags(b))==s: best=max(best,score(b))
    full=all(r32(pl+0x5c+4*k)&15!=15 for k in range(8))
    return score(it)>best+0.01 and not full
class Bot:
    def __init__(s,pl=0x03003C00):
        s.pl=pl; s.hist=[]; s.stuck=0; s.G=None; s.step=0; s.log=[]; s.tries={}; s.kills=0
    def tick(s):
        s.step+=1
        if s.G is None or s.step%40==0: s.G=colmap()
        x,y=pos(); en,items,trig=scan()
        prev=dists(s.G,x,y)
        hp=r16(s.pl+0x17c); mhp=r16(s.pl+0xd0)
        tgt=None
        close=[p for p in en if abs(pos(p)[0]-x)+abs(pos(p)[1]-y)<70]
        for p in en:
            ex,ey=pos(p)
            if abs(ex-x)<=22 and abs(ey-y)<=16: tgt=('hit',p); break
        low=hp*10<mhp*4
        if tgt is None and (not close or low):
            for p in items:
                if r8(p+0x63)!=3 or s.tries.get(p,0)>6: continue
                t=r8(p+0x60)
                if t in HERBS: pass
                elif t>=25 and not close and wanted(s.pl,r32(p+0x88)): pass
                else: continue
                ix,iy=pos(p)
                if abs(ix-x)<=8 and abs(iy-y)<=8: tgt=('pick',p); break
                pth=pathto(prev,ix,iy,1)
                if pth and len(pth)<60 and (tgt is None or len(pth)<tgt[2]): tgt=('go',p,len(pth),pth,'item')
        if tgt is None:
            for p in en:
                pth=pathto(prev,*pos(p))
                if pth and (tgt is None or len(pth)<tgt[2]): tgt=('go',p,len(pth),pth)
        if tgt is None:
            for p in trig:
                pth=pathto(prev,*pos(p),r=3)
                if pth and (tgt is None or len(pth)<tgt[2]): tgt=('go',p,len(pth),pth)
        if tgt is None: return ('done',len(en),len(trig))
        if tgt[0]=='hit':
            ex,ey=pos(tgt[1]); run(2,steer(x,y,ex,ey)); run(4,'B'); run(4)
        elif tgt[0]=='pick':
            p=tgt[1]; s.tries[p]=s.tries.get(p,0)+1
            t=r8(p+0x60); w=r32(p+0x88)
            run(3,'R'); run(5)
            s.log.append(('pick',t,hex(w),r8(p+0x63)))
        else:
            pth=tgt[3]; wp=pth[min(3,len(pth)-1)]; k=steer(x,y,wp[0]*8+4,wp[1]*8+4)
            s.hist.append((x,y))
            if len(s.hist)>8 and abs(s.hist[-8][0]-x)+abs(s.hist[-8][1]-y)<4:
                s.stuck+=1
                if len(tgt)>4: s.tries[tgt[1]]=s.tries.get(tgt[1],0)+1
                # block the cells we keep bumping into, so the path goes around
                W_=s.G[0]//8; gg=s.G[2]
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        c=(wp[0]+dx)+(wp[1]+dy)*W_
                        if 0<=c<len(gg) and (wp[0]+dx,wp[1]+dy)!=(x//8,y//8): gg[c]=1
                if s.stuck%3: run(2,k); run(4,'B'); run(4)
                else: run(10,random.choice(['U','D','LT','RT']))
                s.hist.clear()
            else: run(4,k)
        return (tgt[0],pos(tgt[1]),hp,len(en),len(trig))
