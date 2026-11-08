from g import *
init(); load('moria0'); run(2)
h=r32(0x03003C00)
tx,ty=942,1081
for i in range(300):
    x,y=r16(h+0xae),r16(h+0xb2)
    dx,dy=tx-x,ty-y
    k=[]
    if dx>8:k.append('RT')
    if dx<-8:k.append('LT')
    if dy>8:k.append('D')
    if dy<-8:k.append('U')
    if not k: break
    run(4,'+'.join(k))
    if i%20==0: print(i,x,y)
shot('w1'); print(r16(h+0xae),r16(h+0xb2))
