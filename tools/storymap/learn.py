import json,struct
from collections import defaultdict,Counter
from kinds import recaddrs
C=json.load(open('counts_all.json'))
ex=defaultdict(list)   # type -> [(recbytes,kind)]
cache={}
for L,res in C.items():
    rs=[(a,r) for a,r in recaddrs(int(L)) if r and r[8] not in (3,11,12,17,18)]
    cache[L]=rs
    for (a,r),(t,k,st) in zip(rs,res):
        if k>=0: ex[t].append((r,k))
best={}
for t,v in sorted(ex.items()):
    ks=Counter(k for r,k in v)
    # find byte position p in 16..19 such that r[p] -> kind is a function
    fn=None
    for p in range(16,20):
        m={}; ok=True
        for r,k in v:
            if m.setdefault(r[p],k)!=k: ok=False;break
        if ok: fn=p;break
    best[t]=(fn, ks)
    print(t,len(v),dict(ks),'byte',fn)
print()
for t in (25,26,23,32,29):
    seen={}
    for r,k in ex[t]:
        key=r[16:24].hex()
        seen.setdefault(key,Counter())[k]+=1
    print(t, list(seen.items())[:14])
