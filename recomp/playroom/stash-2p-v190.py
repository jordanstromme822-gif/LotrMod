"""Play Room: the 4 extra backpack boxes (the stash, cells 30-34 of the HD Backpack) work in 2-player and online games too
(Jordan, 2026-11-18: "Certain bag slots won't let me sell or access at the forge").
They were 1-player only: tools/orcslots kept the Backpack cursor off them and ignored the Forge/Shrine and Move Item
requests (SWIN, MVREQ) in linked games, and the HD shop ignored taps on them. Now the local player's own stash works in
every game: the swap runs inside that player's game, so online both pages run it the same way (the request byte travels
with the buttons since v180).
Usage: stash-2p-v190.py live.html out.html, then tools/orcslots/pagejs.py out.html (new Orc Head code), engine ?v=190."""
import sys
src, out = sys.argv[1:3]
t = open(src).read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)
rep('const V = isLink ? "?v=182" : "?v=hd2";', 'const V = isLink ? "?v=190" : "?v=hd2";')
rep('      const V = "?v=182";', '      const V = "?v=190";')
rep('''            if (ctx.linked) return;
            ctx.H8[ctx.ew + 0x3F605] = c - 30 + 1;''', '''            ctx.H8[ctx.ew + 0x3F605] = c - 30 + 1;   // v190: 2-player and online too''')
open(out, 'w').write(t)
print('ok')
