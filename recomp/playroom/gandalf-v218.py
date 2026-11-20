#!/usr/bin/env python3
"""Play Room v218 (Jordan, 2026-11-20): Gandalf's Dash looks like the light pulls him forward, and it no longer plays
the hurt sound or shows the hurt pose.

  gandalf-v218.py in.html out.html      (in.html already has gandalf-v204 .. v214)

Page only: gandalf-shield.js is swapped in whole. The dash still uses the game's hit-reaction state 6 for its movement
(so the game's wall checks apply), but sets the hero's "hit already under way" bit (+0xE8 bit 0x20, timer +0x56) so
the state 6 handler never starts a hit (hurt anim 3 + hurt sound), holds the staff-raised frame of the cast animation,
and draws the light pull on the effects layer.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8").read()
head = "  // Gandalf's always-on Shield and Lightning Blade"
assert s.count(head) == 1, "Gandalf block not found once"
i = s.index(head)
j = s.index("\n  })();\n", i) + len("\n  })();\n")
assert "gsCanvas" in s[i:j] and "DASH_F" not in s[i:j], "unexpected Gandalf block"
js = open(os.path.join(HERE, "gandalf-shield.js"), encoding="utf-8").read().rstrip("\n")
s = s[:i] + "\n".join("  " + l if l else l for l in js.split("\n")) + "\n" + s[j:]
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
