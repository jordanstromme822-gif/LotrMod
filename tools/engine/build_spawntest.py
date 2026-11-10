"""Test-only ROM: every gameplay frame, if EWRAM 0x0203FF00 (count) is set, spawn that many
copies of the level's enemy groups next to the hero. Never share the output ROM.
  python3 tools/engine/build_spawntest.py rotk.gba test.gba [hex ROM offset, default 9F000]
Then from a runner script: poke 0203FF08 <spread px>, 0203FF04 <group or ff = all>,
0203FF10 <bitmask of spawn types, 6600000 = types 22,25,26,29>, 0203FF00 <copies>.
0203FF0C counts the monsters spawned. Code goes to 0x9F000 (Spanish text bank) and the
bl at 0x08031ED0 (per-frame call 0x080391C4) is pointed at it."""
import os,struct,subprocess,sys,tempfile
here=os.path.dirname(os.path.abspath(__file__))
src,dst=sys.argv[1],sys.argv[2]
base=int(sys.argv[3],16) if len(sys.argv)>3 else 0x9F000  # ROM offset for the hook code
t=tempfile.mkdtemp()
subprocess.check_call(['clang','--target=thumbv4t-none-eabi','-mcpu=arm7tdmi','-mthumb','-Os','-ffreestanding','-fno-builtin','-c',os.path.join(here,'spawntest.c'),'-o',t+'/h.o'])
subprocess.check_call(['ld.lld','-Ttext=0x%08X'%(0x08000000+base),'-e','hook',t+'/h.o','-o',t+'/h.elf'])
subprocess.check_call(['llvm-objcopy','-O','binary','-j','.text',t+'/h.elf',t+'/h.bin'])
d=bytearray(open(src,'rb').read()); h=open(t+'/h.bin','rb').read()
d[base:base+len(h)]=h
def bl(s,x):
    o=(x-(s+4))>>1; return struct.pack('<HH',0xF000|((o>>11)&0x7FF),0xF800|(o&0x7FF))
assert d[0x31ED0:0x31ED4]==bl(0x08031ED0,0x080391C4)
d[0x31ED0:0x31ED4]=bl(0x08031ED0,0x08000000+base)
open(dst,'wb').write(d)
