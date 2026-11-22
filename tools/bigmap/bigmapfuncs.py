#!/usr/bin/env python3
"""Add the big-map stubs (tools/bigmap, ROM 0x284C00) to a game-link toml as [[extra_func]] so the one engine compiles
them natively. Run after feelfuncs.py.   python3 bigmapfuncs.py <game-link.toml>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bigmap import assemble
toml = sys.argv[1]
MARK = "# ---- big map stubs (bigmapfuncs.py) ----"
_, syms = assemble()
t = open(toml).read()
if MARK in t: t = t[:t.index(MARK)].rstrip() + "\n"
t = t.rstrip() + "\n\n" + MARK + "\n"
for n in sorted(k for k in syms if (k.startswith('stub_') or k in ('bm_frame', 'call_r4'))):
    t += "\n[[extra_func]]\naddr = 0x%08X\nmode = \"thumb\"\n" % syms[n]
open(toml, "w").write(t)
print("big map stubs", ' '.join(hex(syms[k]) for k in sorted(syms) if (k.startswith('stub_') or k in ('bm_frame', 'call_r4'))))
