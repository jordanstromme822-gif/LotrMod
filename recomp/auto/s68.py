from g import *
from items import reqlevel
init(); load('moriaE'); run(2)
P=0x03003C00+0x1AC*(r8(0x03003F59)&1)
print('lvl19c',r8(P+0x19C),'hero',r8(P+0x19F),'req',reqlevel(0xffff06f8), reqlevel(0xffff0bf8))
def tp(k,n=1):
    for i in range(n): run(5,k); run(14)
tp('START'); run(30); tp('RT',2); tp('A'); run(15); tp('A'); run(36); shot('mq')
print('pack',[hex(r32(P+0x5c+4*i)) for i in range(8)])
