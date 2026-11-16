#!/usr/bin/env python3
"""Play Room v178 page patch (on live v177): a quick Play tap waits (up to 20 s) for the enemies' 16-facing
pictures. Before, a game started before wide/enemy16.wasm arrived was built without them, and enemies kept
their 8 facings for that whole game.

  enemywait-v178.py in.html out.html
"""
import sys
src, dst = sys.argv[1:3]
s = open(src).read()
a = '  (async () => {\n    try {\n      const r = await fetch("wide/enemy16.wasm?v=177");'
assert s.count(a) == 1
s = s.replace(a, a.replace("  (async", "  window.__enemy16P = (async", 1))
a = '    if (!onlinePick) { startGame(null); return; }'
assert s.count(a) == 1
s = s.replace(a, '''    if (!onlinePick) {
      // v178: wait for the enemies' 16-facing pictures (up to 20 s) so a quick Play tap doesn't start without them.
      if (!window.__enemy16 && window.__enemy16P) {
        if (window.__e16wait) return; window.__e16wait = true;
        unlockAudio(); setStatus($("playStatus"), "Loading enemy pictures…", "");
        Promise.race([window.__enemy16P, new Promise((ok) => setTimeout(ok, 20000))]).then(() => { setStatus($("playStatus"), "", ""); startGame(null); });
        return;
      }
      startGame(null); return;
    }''')
open(dst, "w").write(s)
print("enemy wait patched", len(s))
