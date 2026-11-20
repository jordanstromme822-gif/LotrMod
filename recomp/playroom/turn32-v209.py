#!/usr/bin/env python3
"""Play Room v209: every hero and enemy turns through 32 facings (Jordan 2026-11-20: "give all characters and enemies
360 points of motion instead of 16 like you did to the traps").

  python3 turn32-v209.py in.html out.html tools/turn16/turn16.bin

- The hook at 0x9F000 is the new turn16.bin (32 facings for heroes and enemies; the dead v171 crossbow code is gone,
  the Bolt Trap turns in the page since v208). The engine compiles it ([[extra_func]]), so the engine is regenerated
  from this page's ROM (recomp/link/one/regen.sh, engine key ?v=209).
- The pictures (tools/turn16/gen32.py, ~12 MB of the game's own art, so not in the page or the repository) are published
  gzipped as wide/turn32.wasm and fetched on load in place of wide/enemy16.wasm; buildGame puts its chunks into the built
  game past 16 MB (0x1000000-0x1500000 and 0x1610000-0x2000000). The old embedded hero16 block (H16) is dropped.
"""
import re, sys
src, dst, t16 = sys.argv[1:4]
s = open(src).read()
code = open(t16, "rb").read()

def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:90]!r}")
    s = s.replace(old, new)

# hook code
s, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x9F000\); // free-angle hook \(tools/turn16/turn16\.c\)',
               lambda m: 'game.set(hexBytes("%s"), 0x9F000); // free-angle hook (tools/turn16/turn16.c; v209: 32 facings)' % code.hex(), s)
assert k == 1

# drop the embedded hero16 block, build the game from the fetched chunks
a = s.index('      { const H16 = Uint8Array.from(atob("')
b = s.index('"), (c) => c.charCodeAt(0));', a) + len('"), (c) => c.charCodeAt(0));')
s = s[:a] + '      { // v209: heroes\' and enemies\' 32-facing pictures come from wide/turn32.wasm (tools/turn16/gen32.py), see T32 below.' + s[b:]
rep("        const E16 = window.__enemy16 || null;",
    "        // v209: wide/turn32.wasm = 'T32\\0', count, then {file offset, length, bytes} chunks (heroes and enemies, 32 facings).\n"
    "        const T32 = [];\n"
    "        { const t = window.__enemy16 || null;\n"
    "          if (t && t[0] === 0x54 && t[1] === 0x33 && t[2] === 0x32) {\n"
    "            const v = new DataView(t.buffer, t.byteOffset, t.byteLength); let at = 8;\n"
    "            for (let i = v.getUint32(4, true); i > 0; i--) { const off = v.getUint32(at, true), n = v.getUint32(at + 4, true); T32.push([off, t.subarray(at + 8, at + 8 + n)]); at += 8 + n; }\n"
    "          } }")
rep("const g = new Uint8Array(Math.max(0x1500000 + SIEGE.length, 0x1000000 + H16.length, 0x1080000 + (E16 ? E16.length : 4))); g.set(game.subarray(0, 0x1000000)); g.set(H16, 0x1000000);\n        if (E16) g.set(E16, 0x1080000);",
    "const g = new Uint8Array(Math.max(0x1500000 + SIEGE.length, ...T32.map(([o, d]) => o + d.length))); g.set(game.subarray(0, 0x1000000));\n        for (const [o, d] of T32) g.set(d, o);")
# fetch
rep('const r = await fetch("wide/enemy16.wasm?v=189"); if (!r.ok) throw new Error("enemy16 " + r.status);',
    'const r = await fetch("wide/turn32.wasm?v=209"); if (!r.ok) throw new Error("turn32 " + r.status);   // v209: heroes + enemies, 32 facings')
rep("if (b.length > 0x10000 && b[3] === 0x09) window.__enemy16 = b;",
    "if (b.length > 0x10000 && b[0] === 0x54 && b[1] === 0x33 && b[2] === 0x32) window.__enemy16 = b;")
rep('setStatus($("playStatus"), "Loading enemy pictures…", "");', 'setStatus($("playStatus"), "Loading hero and enemy pictures…", "");')
# engine
assert s.count('"?v=199"') == 2
s = s.replace('"?v=199"', '"?v=209"')
open(dst, "w").write(s)
print("v209 page ok", len(s))
