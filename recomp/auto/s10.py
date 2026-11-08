from g import *
init(); load('moria0'); run(2)
W,H,g=colmap()
h=r32(0x03003C00)
tx,ty=942,1081
def go(tx,ty,maxsteps=600):
    for it in range(maxsteps):
        x,y=r16(h+0xae),r16(h+0xb2)
        if abs(x-tx)<12 and abs(y-ty)<12: return True
        path=bfs(W,H,g,x,y,lambda c:abs(c[0]-tx//8)<=1 and abs(c[1]-ty//8)<=1)
        if not path: print('nopath'); return False
        wp=path[min(3,len(path)-1)]; wx,wy=wp[0]*8+4,wp[1]*8+4
        k=[]
        if wx-x>2:k.append('RT')
        if wx-x<-2:k.append('LT')
        if wy-y>2:k.append('D')
        if wy-y<-2:k.append('U')
        run(4,'+'.join(k))
        if it%25==0: print(it,x,y,len(path))
    return False
print(go(tx,ty)); shot('w2')
