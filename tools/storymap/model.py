import json,struct
from collections import defaultdict,Counter
from kinds import recaddrs
rom=open('/tmp/rc/oh/rotk.gba','rb').read()
F=lambda k,i: struct.unpack('<H',rom[0x57518+k*20+2*i:0x57518+k*20+2*i+2])[0]
C=json.load(open('counts_all.json'))
BOSS={47,60,61,63,69}; SPAWN={83,84}; SKIP={74,75,0}
def cls(k):
    if k in SKIP: return None
    if k in BOSS: return 'B'
    if k==67: return 'K'
    if k in SPAWN: return 'P'
    hp=F(k,3); return 'S' if hp<40 else 'M' if hp<150 else 'L'
bykey=defaultdict(Counter); bytype=defaultdict(Counter); recs={}
for L,res in C.items():
    rs=[(a,r) for a,r in recaddrs(int(L)) if r and r[8] not in (3,11,12,17,18)]
    recs[L]=list(zip(rs,res))
    for (a,r),(t,k,st) in recs[L]:
        if k>=0: c=cls(k); bykey[(t,r[16])][c]+=1; bytype[t][c]+=1
def guess(t,r16):
    for d in (bykey.get((t,r16)),bytype.get(t)):
        if d: return d.most_common(1)[0][0]
    return None
out={}; est={}
for L,items in recs.items():
    c=Counter(); g=0
    for (a,r),(t,k,st) in items:
        if k>0: x=cls(k)
        elif k==0: x=None
        else: x=guess(t,r[16]); g+= x is not None
        if x=='K': x='B' if L=='85' else None
        if x: c[x]+=1
    out[int(L)]=[c['S'],c['M'],c['L'],c['B'],c['P']]; est[int(L)]=g
json.dump(out,open('final_counts.json','w'))
for L in sorted(out): print(L,out[L],'guessed',est[L])
print()
for L,items in recs.items():
    for (a,r),(t,k,st) in items:
        if k<0 and guess(t,r[16])=='B': print('guessB',L,'type',t,'r16',r[16])
        if k>0 and cls(k)=='B': print('realB',L,'type',t,'kind',k)
