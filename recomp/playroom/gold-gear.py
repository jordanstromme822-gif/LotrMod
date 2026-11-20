# v213 Gold border on better gear in the HD Backpack and the HD Forge / Shrine (Jordan, 2026-11-20). See gold-gear.js.
#   python3 gold-gear.py in.html out.html
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a)); s = s.replace(a, b)
assert "window.__goldGear" not in s, "already patched"
js = open(os.path.join(HERE, "gold-gear.js"), encoding="utf-8").read().rstrip("\n")
rep("  const WideHost = {", js + "\n  const WideHost = {")
# styles: gold border + glow and a small up arrow; the cursor's own style still wins on the box it is on
for sel in ("#hdBp", "#hdSh"):
    cur = "        '" + sel + " .cell.cur{"
    rep(cur, "        '" + sel + " .cell.gb{border-color:#ffc21a;box-shadow:0 0 0 1px #ffc21a,0 0 calc(var(--c)*0.22) rgba(255,190,30,0.8),inset 0 2px 6px rgba(0,0,0,0.55)}' +\n" +
        "        '" + sel + " .cell .gu{position:absolute;left:6%;top:3%;z-index:2;font-size:calc(var(--c)*0.2);line-height:1;color:#ffd23a;text-shadow:0 1px 2px #000,0 0 4px rgba(255,190,30,0.9);pointer-events:none}' +\n" + cur)
GU = '<span class="gu">&#9650;</span>'
# HD Backpack: backpack boxes (8-15 and the stash boxes 30-34) against the worn gear (boxes 0-7)
rep("""          return '<div class="cell ' + (cls || "") + " " + tier(ww) + (ctx.sub === 6""",
    """          const gb = ((cc >= 8 && cc < 16) || cc >= 30) && window.__goldGear && window.__goldGear(ww, inv.slice(0, 8), hid);
          return '<div class="cell ' + (cls || "") + " " + tier(ww) + (gb ? " gb" : "") + (ctx.sub === 6""")
rep("""'" data-c="' + cc + '">' + pic(ww) +""", """'" data-c="' + cc + '">' + pic(ww) + (gb ? '""" + GU + """' : "") +""")
# HD Forge / Shrine: backpack boxes and the gear for sale
rep("""        const cell = (cc) => '<div class="cell' + ("c" + cc === hc ? " cur" : "") + '" data-id="c' + cc + '">' + pic(wordOf(cc)) + "</div>";""",
    """        const gold = (w) => !!(window.__goldGear && window.__goldGear(w, inv.slice(0, 8), heroId));
        const cell = (cc) => { const gb = gold(wordOf(cc)); return '<div class="cell' + (gb ? " gb" : "") + ("c" + cc === hc ? " cur" : "") + '" data-id="c' + cc + '">' + pic(wordOf(cc)) + (gb ? '""" + GU + """' : "") + "</div>"; };""")
rep("""          return '<div class="cell sk' + (id === hc ? " cur" : "") + (it ? "" : " sold") + '" data-id="' + id + '">' + (it ? pic(it) +""",
    """          const gb = it && gold(it);
          return '<div class="cell sk' + (gb ? " gb" : "") + (id === hc ? " cur" : "") + (it ? "" : " sold") + '" data-id="' + id + '">' + (it ? pic(it) + (gb ? '""" + GU + """' : "") +""")
open(out, "w", encoding="utf-8").write(s); print("ok gold gear")
