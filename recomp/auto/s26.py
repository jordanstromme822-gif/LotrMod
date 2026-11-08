from bot import *
init(); load(sys.argv[1] if len(sys.argv)>1 else 'moriaE'); run(2)
G=colmap(); pl=0x03003C00
seenitems={}; hist=[]; stuck=0
for step in range(3000):
    x,y=pos()
    if step%40==0: G=colmap()
    en,items,trig=scan()
    for p in items:
        k=(p,r8(p+0x60),r32(p+0x88))
        if k not in seenitems: seenitems[k]=pos(p); print('item',hex(p),'type',r8(p+0x60),'word',hex(r32(p+0x88)),'state',r8(p+0x63),pos(p))
    prev=dists(G,x,y)
    # target: nearest reachable enemy
    tgt=None
    for p in en:
        ex,ey=pos(p)
        if abs(ex-x)<=22 and abs(ey-y)<=16: tgt=('hit',p); break
        pth=pathto(prev,ex,ey)
        if pth and (tgt is None or len(pth)<tgt[2]): tgt=('go',p,len(pth),pth)
    if tgt is None:
        for p in trig:
            pth=pathto(prev,*pos(p),r=3)
            if pth and (tgt is None or len(pth)<tgt[2]): tgt=('trig',p,len(pth),pth)
    if tgt is None: print('done?',step,len(en),len(trig)); break
    if tgt[0]=='hit':
        ex,ey=pos(tgt[1]); run(2,steer(x,y,ex,ey)); run(4,'B'); run(4)
    else:
        pth=tgt[3]; wp=pth[min(3,len(pth)-1)]; k=steer(x,y,wp[0]*8+4,wp[1]*8+4)
        hist.append((x,y))
        if len(hist)>8 and abs(hist[-8][0]-x)+abs(hist[-8][1]-y)<4:
            stuck+=1
            if stuck%3: run(2,k); run(4,'B'); run(4)
            else:
                import random; run(10,random.choice(['U','D','LT','RT']))
            hist.clear()
        else: run(4,k)
    if step%100==0: print(step,(x,y),'hp',r16(pl+0x17c),'en',len(en),'trig',len(trig),tgt[0],pos(tgt[1]))
save('afterbot'); shot('ab')
