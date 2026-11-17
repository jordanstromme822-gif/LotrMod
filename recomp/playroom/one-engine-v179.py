#!/usr/bin/env python3
"""Play Room v179 page patch (on live v178): one engine for 1-player and P2 games.

  one-engine-v179.py in.html out.html

Jordan (2026-11-16): "I just want one, not multiple, combine them all into the 1".
- The 2-player build (wide/rotk-link*, ?v=179), generated from today's page ROM with every hook compiled natively
  (orcslots, HD Backpack, 12 slots, turn16 hero + enemy hooks), now also runs 1-player games. The old solo engine
  (wide/rotk*) is no longer loaded.
- In a 1-player game the page hides the engine's _rotk_link_* exports, so every 1-player check behaves as before.
- P2 games get the full page ROM (the 16-facing pictures past 16 MB too); the old slot-code ROM (__linkRom) is gone.
"""
import sys
src, dst = sys.argv[1:3]
s = open(src).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
rep("const fetchEngine = (isLink) =>", "const fetchEngine = (isLink0, isLink = true) =>   // v179: one engine (the 2-player build) for every game\n     ")
rep('const V = isLink ? "?v=172" : "?v=hd2";', 'const V = isLink ? "?v=179" : "?v=hd2";')
rep('      m.FS.mkdir("/data"); m.FS.mkdir("/data/saves");\n',
    '      // v179: a 1-player game on the one engine looks like the old 1-player engine to the rest of the page.\n'
    '      if (!linkCfg) for (const k of Object.keys(m)) if (k.startsWith("_rotk_link_")) delete m[k];\n'
    '      m.FS.mkdir("/data"); m.FS.mkdir("/data/saves");\n')
i = s.index("  // 2-player engine (rotk-link ?v=169) still runs the slot code"); j = s.index("\n  };\n", i) + len("\n  };\n")
s = s[:i] + "  // v179: the one engine is built from the page ROM itself, so P2 games get it unchanged (all of it, past 16 MB too).\n  window.__linkRom = (r) => r.slice();\n" + s[j:]
open(dst, "w").write(s)
print("one engine patched", len(s))
