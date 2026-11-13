#!/usr/bin/env python3
"""Play Room v176 page patch (on live v175): 16 facings for every hero, not just Frodo (1-player Wide engine).

  all360-v176.py in.html out.html turn16.bin hero16.bin

hero16.bin is tools/turn16/gen16all.py's output (in-between walk and stand pictures for all 8 heroes, made from the
game's own art: it stays out of the repository; the page carries it). It is about 480 KB, more than the free text banks
hold, so the page grows the built game past 16 MB and puts it at ROM 0x1000000 (CPU 0x09000000). Frodo's old pictures at
0x8A000 are dropped (hero16.bin has his too). The 2-player engine and the game file download get the first 16 MB only:
the hook that reads the pictures runs only in the 1-player engine, and a 16 MB file saves on any emulator.
"""
import base64, re, sys
src, dst, t16, h16 = sys.argv[1:5]
s = open(src).read()
code, pics = open(t16, "rb").read(), open(h16, "rb").read()
assert len(code) <= 0x1000 and len(pics) < 0x200000
# 1. Frodo's pictures at 0x8A000 -> all heroes' pictures past 16 MB.
s, k = re.subn(r'( *)// Smooth 360-degree walking test \(tools/turn16\): Frodo\'s in-between facing pictures \(0x8A000, freed German text bank\)\n'
               r' *// and the free-angle hook \(0x9F000\)\. Nothing runs them until the page points the hero\'s update at 0x0809F001\.\n'
               r' *game\.set\(hexBytes\("[0-9a-f]+"\), 0x8A000\);[^\n]*\n',
               lambda m: m.group(1) + "// Smooth 360-degree walking (tools/turn16): every hero's in-between facing pictures (gen16all.py, ~480 KB) go past\n"
               + m.group(1) + "// the 16 MB game (ROM 0x1000000 = CPU 0x09000000), and the free-angle hook (0x9F000). Nothing reads them until the page\n"
               + m.group(1) + "// points the hero's update at 0x0809F001 (1-player engine only).\n"
               + m.group(1) + '{ const H16 = Uint8Array.from(atob("%s"), (c) => c.charCodeAt(0));\n' % base64.b64encode(pics).decode()
               + m.group(1) + "  const g = new Uint8Array(0x1000000 + H16.length); g.set(game.subarray(0, 0x1000000)); g.set(H16, 0x1000000); game = g; }\n", s)
assert k == 1, k
# 2. new hook code (looks up the hero's picture table instead of Frodo only)
s, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x9F000\);', lambda m: 'game.set(hexBytes("%s"), 0x9F000);' % code.hex(), s)
assert k == 1, k
# 3. 2-player engine and download: first 16 MB only
s, k = re.subn(r'window\.__linkRom = \(r\) => \{\n(\s*)const x = r\.slice\(\),',
               lambda m: 'window.__linkRom = (r) => {\n' + m.group(1) + 'const x = r.slice(0, 0x1000000),', s)
assert k == 1, k
s, k = re.subn(r'const game = buildGame\(mod\);\n(\s*)const blob = zipOne\(base \+ "\.gba", game\);',
               lambda m: 'const game = buildGame(mod).subarray(0, 0x1000000); // v176: the 1-player 360 pictures stay in the page\n' + m.group(1) + 'const blob = zipOne(base + ".gba", game);', s)
assert k == 1, k
open(dst, "w").write(s)
print("all heroes 360 patched", len(s))
