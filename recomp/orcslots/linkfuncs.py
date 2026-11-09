#!/usr/bin/env python3
"""Rewrite the hook block at the end of recomp/link/game-link.toml from tools/orcslots/orcslots.sym.

  python3 linkfuncs.py <tools/orcslots/orcslots.sym> <recomp/link/game-link.toml>

The 2-player engine compiles every Orc Head / quiver hook natively (extra_func per entry). Bridging
them through the interpreter crashed that engine in long fights (a call to 0x00000008 deep inside
nested bridges). The addresses move whenever the hook code changes, so run this after every
tools/orcslots/build.py and regenerate with a ROM that has orcslots.bin at 0x7F000.
"""
import sys

DATA = {"seven", "ODDS", "TIER_NAME", "frame_hook.order", "orc_tiles", "orc_pal", "slot_pal",
        "arrow_tiles", "arrow_pal", "abox_tiles", "abox_pal", "aquiv_tiles", "aquiv_pal",
        "xb_anim", "xb_frames", "xb_tiles", "xb_bolt_touch.snd", "xb_cast.fx", "xb_cast.fy"}
MARK = "# ---- LotrMod hooks (orcslots/linkfuncs.py) ----"

sym, toml = sys.argv[1], sys.argv[2]
funcs = sorted(int(a, 16) for n, a in (l.split() for l in open(sym) if l.strip()) if n not in DATA)
text = open(toml).read()
if MARK in text:
    text = text[:text.index(MARK)].rstrip() + "\n"
else:  # first run: drop the old single recv4 entry
    old = '\n[[extra_func]]\naddr = 0x0807F000\nmode = "thumb"\n'
    text = text.replace(old, "\n") if text.endswith(old) else text
block = "".join(f'\n[[extra_func]]\naddr = 0x{a:08X}\nmode = "thumb"\n' for a in funcs)
open(toml, "w").write(text.rstrip() + "\n\n" + MARK + "\n" + block)
print(len(funcs), "hook entries")
