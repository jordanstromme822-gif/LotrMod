#!/usr/bin/env python3
"""Big maps read straight from ROM (2026-11-22, see bigmap.s and docs/findings.md "Big maps").

  python3 tools/bigmap/bigmap.py IN.gba OUT.gba     patch a ROM (the engine generation ROM)
  python3 tools/bigmap/bigmap.py --js               print the buildGame step for the page

The five map loads call the stubs in bigmap.s (ROM 0x284C00, in the zero run 0x2833C5-0x2862A8 after bigsprites)
instead of the decompressor. Normal levels load exactly as before; a level whose map blobs start with header byte
0x01 keeps them in ROM, so its size is no longer limited by the 0x2810-byte EWRAM buffers.
"""
import os, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 0x284C00
DECOMP = 0x08019D54
SITES = {'stub_mapA': 0x3EEC6, 'stub_mapB': 0x3F04E, 'stub_metaA': 0x3EF8A, 'stub_metaB': 0x3F0CA, 'stub_col': 0x3411C}
# the gameplay tick's call of 0x080016F8 goes through bm_frame (tile set swap on joined levels)
FRAME = (0x31ED4, 0x080016F8, 'bm_frame')


def thumb_bl(src, dst):
    off = (dst - (src + 4)) >> 1
    return struct.pack('<HH', 0xF000 | ((off >> 11) & 0x7FF), 0xF800 | (off & 0x7FF))


def assemble():
    d = tempfile.mkdtemp()
    o, e, b = (os.path.join(d, n) for n in ('b.o', 'b.elf', 'b.bin'))
    subprocess.check_call(['llvm-mc', '-triple=thumbv4t-none-eabi', '-filetype=obj', os.path.join(HERE, 'bigmap.s'), '-o', o])
    subprocess.check_call(['ld.lld', '-Ttext=0x%08X' % (0x08000000 + BASE), '-e', '0', o, '-o', e])
    subprocess.check_call(['llvm-objcopy', '-O', 'binary', '-j', '.text', e, b])
    syms = {}
    for line in subprocess.check_output(['llvm-nm', e]).decode().split('\n'):
        p = line.split()
        if len(p) == 3: syms[p[2]] = int(p[0], 16)
    return open(b, 'rb').read(), syms


def patches():
    code, syms = assemble()
    out = [(BASE, bytes(len(code)), code)]
    for name, at in SITES.items():
        out.append((at, thumb_bl(0x08000000 + at, DECOMP), thumb_bl(0x08000000 + at, syms[name])))
    at, old, name = FRAME
    out.append((at, thumb_bl(0x08000000 + at, old), thumb_bl(0x08000000 + at, syms[name])))
    return out, syms


if __name__ == '__main__':
    ps, syms = patches()
    if sys.argv[1] == '--js':
        old = ', '.join('[0x%X, "%s"]' % (o, a.hex()) for o, a, _ in ps)
        new = ', '.join('[0x%X, "%s"]' % (o, b.hex()) for o, _, b in ps)
        print('      // Big maps read straight from ROM (tools/bigmap): the five map loads go through small stubs that keep a\n'
              '      // level\'s map in ROM when its data starts with 0x01; every other level loads exactly as before.\n'
              '      { const BM_OLD = [%s];\n        const BM_NEW = [%s];\n'
              '        if (BM_OLD.every(([o, h]) => eq(o, h))) BM_NEW.forEach(([o, h]) => game.set(hexBytes(h), o)); }' % (old, new))
    else:
        r = bytearray(open(sys.argv[1], 'rb').read())
        for o, a, b in ps:
            assert r[o:o + len(a)] == a, hex(o)
            r[o:o + len(b)] = b
        open(sys.argv[2], 'wb').write(r)
        print('patched', ' '.join('%s=%x' % (k, v) for k, v in sorted(syms.items())))
