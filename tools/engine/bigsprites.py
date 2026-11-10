"""Extra sprite tiles (engine upgrade, 2026-11-10).

The game keeps sprite pictures in 1024 tiles of OBJ VRAM; with ~70 monsters on screen
it runs out and frames go missing. With an engine that has the extra 32 KB of OBJ VRAM
(recomp/gbarecomp-obj-ext.patch: IO 0x040000E0 switch, OAM attr0 bit 12 = tile bit 10),
this patch lets the game hand out tiles 1024-2047. On other emulators the switch reads
back wrong, the extra tiles stay marked as used and the game behaves as before.

  python3 tools/engine/bigsprites.py in.gba out.gba [hex ROM offset for code, default 9F400]

Changes: the sprite-tile bitmaps (bigsprites_init.c explains where they live); the
bitmap resets (0x080499F8, 0x08049A54, 0x08049A8C), allocate/mark/free (0x08049AB8, 0x08049C80, 0x08049CCC, 0x08049D24) and
the per-frame fold (0x08049984) are rewritten in C (bigsprites_init.c); and the seven places that put a tile
number into an OAM entry or template keep bit 10 in attr0 bit 12 (bigsprites_stubs.s)."""
import os, struct, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1], sys.argv[2]
base = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x9F400
t = tempfile.mkdtemp()
cc = ['clang', '--target=thumbv4t-none-eabi', '-mcpu=arm7tdmi', '-mthumb', '-Os', '-ffreestanding', '-fno-builtin']
subprocess.check_call(cc + ['-c', os.path.join(here, 'bigsprites_init.c'), '-o', t + '/i.o'])
subprocess.check_call(cc + ['-c', os.path.join(here, 'bigsprites_stubs.s'), '-o', t + '/s.o'])
subprocess.check_call(['ld.lld', '-Ttext=0x%08X' % (0x08000000 + base), '-e', 'bs_init', t + '/i.o', t + '/s.o', '-o', t + '/b.elf'])
subprocess.check_call(['llvm-objcopy', '-O', 'binary', '-j', '.text', t + '/b.elf', t + '/b.bin'])
sym = {}
for l in subprocess.check_output(['llvm-nm', t + '/b.elf']).decode().split('\n'):
    p = l.split()
    if len(p) == 3: sym[p[2]] = int(p[0], 16)
code = open(t + '/b.bin', 'rb').read()
d = bytearray(open(src, 'rb').read())
assert set(d[base:base + len(code)]) <= {0, 0xFF} or d[base:base + len(code)] == code or '--force' in sys.argv, 'code area not empty'
d[base:base + len(code)] = code

def u16(a): return struct.unpack('<H', d[a - 0x08000000:a - 0x08000000 + 2])[0]
def put16(a, v): d[a - 0x08000000:a - 0x08000000 + 2] = struct.pack('<H', v)
def bl(s, x):
    o = (x - (s + 4)) >> 1
    assert -(1 << 21) <= o < (1 << 21), 'bl out of range (Thumb bl reaches 4 MB): put the code below 0x400000'
    return struct.pack('<HH', 0xF000 | ((o >> 11) & 0x7FF), 0xF800 | (o & 0x7FF))
def patch_bl(at, target, expect, span):
    """replace `span` bytes at `at` (checked against `expect` hex) with bl target + nops"""
    cur = bytes(d[at - 0x08000000:at - 0x08000000 + span])
    assert cur.hex() == expect, (hex(at), cur.hex())
    new = bl(at, target) + b'\xc0\x46' * ((span - 4) // 2)
    d[at - 0x08000000:at - 0x08000000 + span] = new
def jump(at, target):
    """function entry -> ldr r3,[pc]; bx r3; .word target|1 (entry must be 4-aligned)"""
    assert at % 4 == 0
    d[at - 0x08000000:at - 0x08000000 + 8] = struct.pack('<HHI', 0x4B00, 0x4718, target | 1)

# 1. the bookkeeping functions jump to bigsprites_init.c
for at, name in ((0x08049984, 'bs_fold'), (0x080499F8, 'bs_init'), (0x08049A54, 'bs_reset_a'),
                 (0x08049A8C, 'bs_reset_b'), (0x08049AB8, 'bs_alloc'), (0x08049C80, 'bs_mark'),
                 (0x08049CCC, 'bs_free_now'), (0x08049D24, 'bs_free_later')):
    jump(at, sym[name])
# 5. tile bit 10 -> attr0 bit 12
patch_bl(0x08002D6A, sym['bs_e1'], '8905890d', 4)
patch_bl(0x0800262C, sym['bs_e3'], '8905890d', 4)
patch_bl(0x08039406, sym['bs_e7'], '8905890d', 4)
patch_bl(0x08002C72, sym['bs_e2'], '9105890d301cdf300078800980000918114b181c0140104c201c02400a43', 30)
patch_bl(0x08003398, sym['bs_e4'], '1c49081c04990140089b1a881a48104008431880', 20)
patch_bl(0x08047B20, sym['bs_e5'], '2b1ce0330b4901401a880b48104008431880', 18)
patch_bl(0x08002BE6, sym['bs_e6'], '341ce0343749014022883648104008432080', 18)
open(dst, 'wb').write(d)
print('bigsprites: code %d bytes at 0x%X' % (len(code), base))
