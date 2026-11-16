#!/usr/bin/env python3
"""Play Room v177 page patch (on live v176): enemies turn through 16 facings too (1-player Wide engine).

  enemies360-v177.py in.html out.html turn16.bin

- turn16.bin (tools/turn16) now also runs `enemies()` once a tick from the hero's update.
- The enemy pictures (tools/turn16/genenemy.py -> enemy16.bin, about 3.5 MB, game art: not in the repo) are published
  next to the page as wide/enemy16.dat (gzip). The page fetches and unpacks them when it loads; the game is built with them
  at ROM 0x1080000 (CPU 0x09080000), after the heroes' pictures. If they haven't arrived, that spot is zero and the hook
  leaves enemies alone.
- EWRAM 0x0203FFC3 bit 0 = enemies chasing the hero walk straight at him (localStorage rotk-enemy-chase, default on).
"""
import re, sys
src, dst, t16 = sys.argv[1:4]
s = open(src).read()
code = open(t16, "rb").read()
assert len(code) <= 0x1000
s, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x9F000\);', lambda m: 'game.set(hexBytes("%s"), 0x9F000);' % code.hex(), s)
assert k == 1, k
old = "        const g = new Uint8Array(0x1000000 + H16.length); g.set(game.subarray(0, 0x1000000)); g.set(H16, 0x1000000); game = g; }\n"
assert s.count(old) == 1
s = s.replace(old,
    "        // v177: enemies' in-between pictures (genenemy.py) at ROM 0x1080000, fetched when the page loads (wide/enemy16.dat).\n"
    "        const E16 = window.__enemy16 || null;\n"
    "        const g = new Uint8Array(Math.max(0x1000000 + H16.length, 0x1080000 + (E16 ? E16.length : 4))); g.set(game.subarray(0, 0x1000000)); g.set(H16, 0x1000000);\n"
    "        if (E16) g.set(E16, 0x1080000);\n"
    "        game = g; }\n")
# fetch + gunzip early
anchor = "  // Free-angle joystick + 16 facings (test, Jordan 2026-11-11"
assert s.count(anchor) == 1
s = s.replace(anchor,
    "  // Enemies in 16 facings (v177, Jordan 2026-11-16: \"Next do enemies\"): their in-between pictures, gzipped next to the page.\n"
    "  (async () => {\n"
    "    try {\n"
    "      const r = await fetch(\"wide/enemy16.dat?v=177\"); if (!r.ok) throw new Error(\"enemy16 \" + r.status);\n"
    "      const b = new Uint8Array(await new Response(r.body.pipeThrough(new DecompressionStream(\"gzip\"))).arrayBuffer());\n"
    "      if (b.length > 0x10000 && b[3] === 0x09) window.__enemy16 = b;\n"
    "    } catch (e) { (window.__wideLog || (window.__wideLog = [])).push(\"enemy16: \" + e); }\n"
    "  })();\n"
    "  const enemyChase = () => { try { return localStorage.getItem(\"rotk-enemy-chase\") !== \"0\"; } catch (e) { return true; } };\n"
    "  window.__toggleEnemyChase = () => { try { localStorage.setItem(\"rotk-enemy-chase\", enemyChase() ? \"0\" : \"1\"); } catch (e) {} };\n"
    + anchor, 1)
old2 = "      if (!freeOn()) H[ew + FREE_MB] = 0;                          // joystick 8 ways: the hook leaves his walk alone\n"
assert s.count(old2) == 1
s = s.replace(old2, old2 + "      H[ew + FREE_MB + 3] = enemyChase() ? 1 : 0;                  // v177: chasing enemies walk straight at the hero\n")
open(dst, "w").write(s)
print("enemies 360 patched", len(s))
