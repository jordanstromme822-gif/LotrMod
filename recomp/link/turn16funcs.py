#!/usr/bin/env python3
"""Add the turn16 hook entries that are reached through pointers (hero +0x14 = hero_upd, knife literal = kt_stun) to the
end of a game-link toml, so the one engine compiles them natively (v179). Run after orcslots/linkfuncs.py.

  python3 turn16funcs.py <tools/turn16/turn16.sym> <game-link.toml>
"""
import sys
sym, toml = sys.argv[1], sys.argv[2]
ad = {n: int(a, 16) for n, a in (l.split() for l in open(sym) if l.strip())}
MARK = "# ---- turn16 hook entries (turn16funcs.py) ----"
t = open(toml).read()
if MARK in t: t = t[:t.index(MARK)].rstrip() + "\n"
t = t.rstrip() + "\n\n" + MARK + "\n" + "".join(f'\n[[extra_func]]\naddr = 0x{ad[n]:08X}\nmode = "thumb"\n' for n in ("hero_upd", "kt_stun"))
open(toml, "w").write(t)
print("turn16 entries", [hex(ad[n]) for n in ("hero_upd", "kt_stun")])
