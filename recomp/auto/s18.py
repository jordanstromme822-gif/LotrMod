from g import *
init(); load('near1'); run(2)
G=colmap()
t=0x20177f0
for i in range(54):
    x,y=pos(); ex,ey=pos(t)
    if abs(ex-x)+abs(ey-y)>30:
        path=bfs(*G,x,y,lambda c:abs(c[0]-ex//8)<=2 and abs(c[1]-ey//8)<=2)
        if path: wp=path[min(3,len(path)-1)]; run(4,steer(x,y,wp[0]*8+4,wp[1]*8+4))
        else: run(4)
    else:
        run(2,steer(x,y,ex,ey)); run(4,'A'); run(6)
save('fight')
print(pos(),pos(t))
