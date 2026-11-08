from g import *
init(); load('moriaE')
run(30)
xs=[]
for i in range(160):
    run(1,'RT' if i<80 else 'D')
    x,y=pos(); xs.append((x,y,r16(0x04000010+4*1),r16(0x04000014+4*1-4)))
prev=None
out=[]
for i,(x,y,a,b) in enumerate(xs):
    if prev: out.append(f"{x-prev[0]},{y-prev[1]}")
    prev=(x,y)
print(' '.join(out))
print(xs[:5])
