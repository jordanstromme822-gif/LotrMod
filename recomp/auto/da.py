import sys,capstone
rom=open('/tmp/rc/auto/game.gba','rb').read()
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB)
a=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 40
off=a-0x08000000
for i in md.disasm(rom[off:off+n*2],a): print('%08x  %s %s'%(i.address,i.mnemonic,i.op_str))
