from g import *
init(); load('near1'); run(2)
G=colmap()
t=0x20177f0; pl=0x03003C00
for i in range(200):
    x,y=pos(); ex,ey=pos(t)
    if r32(t+0x14)!=0x801b9d1: print('gone',i,hex(r32(t+0x14))); break
    if r16(t+0x8e)>0x100: w16(t+0x8e,0x100) if False else L.w16(t+0x8e,0x100)
    if abs(ex-x)+abs(ey-y)>30:
        path=bfs(*G,x,y,lambda c:abs(c[0]-ex//8)<=2 and abs(c[1]-ey//8)<=2)
        if path: wp=path[min(3,len(path)-1)]; run(4,steer(x,y,wp[0]*8+4,wp[1]*8+4))
        else: run(4)
    else:
        run(2,steer(x,y,ex,ey)); run(4,'A'); run(6)
    if i>40: print(i,hex(r16(t+0x8c)),hex(r16(t+0x8e)),hex(r8(t+0x63)),hex(r8(t+0x6c)), hex(r32(t+0x14)))
    if i>90: break
shot('f3')
