from g import *
init(); run(400)
for i in range(5): tap('D',3,10)
tap('A',4,80); tap('D',4,30); shot('e0'); tap('A',4,80)
tap('A',4,80); tap('A',4,80); tap('A',4,200); run(400); shot('e1'); print(hex(r8(0x030041B0)), r8(r32(0x03003C00)+0) , r8(0x03003C00+0x19F))
save('moriaE')
