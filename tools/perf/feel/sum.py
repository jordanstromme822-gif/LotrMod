import sys
L=open(sys.argv[1]).read().split('\n'); angs=list(map(int,sys.argv[2].split(',')))
seg=[];cur=None
for l in L:
  if l=='--': cur=[];seg.append(cur);continue
  if l=='up': cur.append('up');continue
  p=l.split()
  if cur is not None and len(p)==11: cur.append(list(map(int,p)))
bad=0
for i,s in enumerate(seg):
  up=s.index('up'); mv=s[:up]
  ticks=[];last=None
  for r in mv:
    k=(r[2],r[3],r[6])
    if k!=last: ticks.append(r); last=k
  dx=mv[-1][2]-mv[0][2]; dy=mv[-1][3]-mv[0][3]
  fr=sum(1 for a,b in zip(ticks,ticks[1:]) if a[6]!=b[6])
  if fr<15: bad+=1
  print('ang',angs[i],'moved',dx,dy,'leg frames',fr)
print('frozen',bad,'of',len(seg))
