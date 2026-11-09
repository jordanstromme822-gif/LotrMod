from ex2 import groups
import json
t={}
for l in open('/mnt/project-files/text-dumps/text-en.txt',encoding='utf-8',errors='replace'):
    p=l.rstrip('\n').split('\t',1)
    if len(p)==2 and p[0].isdigit(): t[int(p[0])]=p[1]
E={}
for L in range(1,130):
    ex=[]
    for g in groups(L):
        for it in g:
            if it and it[8]==3: ex.append(it[0x13])
    E[L]=ex
    print(L,t[0x87+L],[(a,t.get(0x87+a)) for a in ex])
json.dump(E,open('exits.json','w'))
