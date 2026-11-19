#!/usr/bin/env python3
"""Add the movement-feel wrapper (tools/feel/feel.c hero_feel at ROM 0x8A000, reached through hero +0x14) to the end of a
game-link toml, so the one engine compiles it natively (v199). Run after turn16funcs.py.

  python3 feelfuncs.py <game-link.toml>
"""
import sys
toml = sys.argv[1]
MARK = "# ---- feel hook entry (feelfuncs.py) ----"
t = open(toml).read()
if MARK in t: t = t[:t.index(MARK)].rstrip() + "\n"
t = t.rstrip() + "\n\n" + MARK + "\n\n[[extra_func]]\naddr = 0x0808A000\nmode = \"thumb\"\n"
open(toml, "w").write(t)
print("feel entry 0x0808a000")
