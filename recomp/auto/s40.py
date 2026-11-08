from g import *
for path in range(4):
    init(); run(400)
    for i in range(5): tap('D',3,10)
    tap('A',4,80); tap('A',4,80)
    for i in range(path): tap('RT',3,20)
    tap('A',4,80); tap('A',4,80); tap('A',4,200); run(400)
    print(path,'state',hex(r8(0x030041B0)),'b8',r8(0x030041B8),'f8',r8(0x030041F8),'d0',r8(0x030041D0),'e0',r8(0x030041E0),'208',r8(0x03004208))
    shot('path%d'%path)
