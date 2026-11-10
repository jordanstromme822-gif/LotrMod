"""Rewrite the Orc Head code block of the Play Room page (or a buildrom.js copy of its buildGame) from orcslots.bin/.sym:
the code hex at 0x7F000, every '// bl <hook>' line, the link message cases and the state table entries.
Usage: pagejs.py file.html [more files]"""
import os, sys, re, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import orcslots as O
s = O.syms(); code = open(O.os.path.join(O.D, 'orcslots.bin'), 'rb').read()
names = {}
def u32(v): return struct.pack('<I', v).hex()
for path in sys.argv[1:]:
    t = open(path).read(); n = 0
    t, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x7F000\); // Orc Head code', 'game.set(hexBytes("%s"), 0x7F000); // Orc Head code' % code.hex(), t); assert k == 1; n += k
    def bl(m):
        if m.group(3) not in s: return m.group(0)
        off = int(m.group(2), 16); return 'game.set(hexBytes("%s"), 0x%s); // bl %s' % (O.thumb_bl(0x08000000 + off, s[m.group(3)]).hex(), m.group(2), m.group(3))
    t, k = re.subn(r'game\.set\(hexBytes\("([0-9a-f]{8})"\), 0x([0-9A-F]+)\); // bl (\w+)', bl, t); n += k; print('bl', k)
    def lk(m):
        return 'game.set(hexBytes("%s"), 0x%s); // link message 4 -> %s' % (u32(s[m.group(3)]), m.group(2), m.group(3))
    t, k = re.subn(r'game\.set\(hexBytes\("([0-9a-f]{8})"\), 0x([0-9A-F]+)\); // link message 4 -> (\w+)', lk, t); n += k; print('link', k)
    def st(m):
        return 'game.set(hexBytes("%s"), 0x%s); // %s -> %s' % (u32(s[m.group(4)] | 1), m.group(2), m.group(3), m.group(4))
    t, k = re.subn(r'game\.set\(hexBytes\("([0-9a-f]{8})"\), 0x([0-9A-F]+)\); // (state table|Backpack exit) -> (\w+)', st, t); n += k; print('state', k)
    open(path, 'w').write(t)
