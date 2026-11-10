"""Turn bigsprites.py output into the JS step for the Play Room's buildGame (and engine-build/buildrom.js).

  python3 tools/engine/bigsprites_js.py before.gba after.gba
Prints one JS block: it checks the original bytes at every patched spot, then writes the new ones.
"""
import sys
a = open(sys.argv[1], 'rb').read(); b = open(sys.argv[2], 'rb').read()
diff = [i for i in range(len(a)) if a[i] != b[i]]
runs = []; s = p = diff[0]
for x in diff[1:]:
    if x > p + 8: runs.append((s, p + 1)); s = x
    p = x
runs.append((s, p + 1))
old = ', '.join('[0x%X, "%s"]' % (s, a[s:e].hex()) for s, e in runs)
new = ', '.join('[0x%X, "%s"]' % (s, b[s:e].hex()) for s, e in runs)
print('      // Extra sprite tiles (tools/engine/bigsprites.py, engine thread 2026-11-10): the game\'s sprite tile bookkeeping moves to C code')
print('      // that uses 2048 tiles when the engine says it has the extra sprite memory (reg 0x0E0 reads 0x584B); otherwise it acts like the original.')
print('      { const BS_OLD = [%s];' % old)
print('        const BS_NEW = [%s];' % new)
print('        if (BS_OLD.every(([o, h]) => eq(o, h))) BS_NEW.forEach(([o, h]) => game.set(hexBytes(h), o)); }')
