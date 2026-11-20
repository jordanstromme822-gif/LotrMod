#!/usr/bin/env python3
"""Play Room v209 (Jordan, 2026-11-20): "If Frodo's traps don't have a target have them slowly shift back and forth a few
frames in the direction they are currently facing like they are searching for a target". Apply after v208.

  bolt-trap-search-v209.py in.html out.html

With no foe in range the crossbow sweeps 2 facings (of 32, 22.5 degrees) either side of the way it last pointed, one
facing every 8 game ticks (a full sweep takes about 2 s). It turns back to a foe as soon as one shows up.
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:90]!r}")
    s = s.replace(old, new)

rep("""                if (t) {
                  const want = Math.round(Math.atan2(t[0], -(t[1] + 4)) / (2 * Math.PI) * 32) & 31;
                  let d = ((want - q.f + 48) & 31) - 16;
                  q.f = (q.f + Math.sign(d) * Math.min(Math.abs(d), steps) + 32) & 31;
                }""",
"""                if (t) {
                  const want = Math.round(Math.atan2(t[0], -(t[1] + 4)) / (2 * Math.PI) * 32) & 31;
                  let d = ((want - q.f + 48) & 31) - 16;
                  q.f = (q.f + Math.sign(d) * Math.min(Math.abs(d), steps) + 32) & 31;
                  q.home = -1;
                } else {   // v209: no foe: sweep 2 facings either side of where it points, like it is searching
                  if (q.home === undefined || q.home < 0) { q.home = q.f; q.sw = 0; q.swT = now; }
                  if (((now - q.swT) | 0) >= 8) { q.swT = now; q.sw = (q.sw + 1) & 7; q.f = (q.home + [0, 1, 2, 1, 0, -1, -2, -1][q.sw] + 32) & 31; }
                }""")
open(dst, "w", encoding="utf-8").write(s)
print("v209 trap search sway patched")
