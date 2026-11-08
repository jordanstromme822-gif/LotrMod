from g import *
init(); run(400)
for i in range(5): tap('D',3,10)
tap('A',4,80); tap('A',4,80)
tap('A',4,80); shot('c1')
tap('A',4,80); shot('c2')
tap('A',4,200); shot('c3')
run(400); shot('c4'); print(hex(r8(0x030041B0)))
save('moria0')
