# v218 red over gear the hero can't wear, in the HD Backpack and the HD Forge / Shrine, like the game's own inventory
# (Jordan, 2026-11-20). Swaps in the newer gold-gear.js (window.__goldGear.cant) and marks the boxes.
#   python3 red-gear-v218.py in.html out.html
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a)); s = s.replace(a, b)
assert ".cant = cant" not in s, "already patched"
js = open(os.path.join(HERE, "gold-gear.js"), encoding="utf-8").read().rstrip("\n")
i = s.index("  // v213 Gold border on better gear"); j = s.index("    return better;\n  })();", i) + len("    return better;\n  })();")
s = s[:i] + js + s[j:]
for sel in ("#hdBp", "#hdSh"):
    cur = "        '" + sel + " .cell.cur{"
    rep(cur, "        '" + sel + " .cell.rw::after{content:\"\";position:absolute;inset:0;z-index:1;border-radius:inherit;background:rgba(200,20,10,0.45);box-shadow:inset 0 0 0 2px rgba(255,70,50,0.9);pointer-events:none}' +\n" + cur)
# HD Backpack: every box with gear (worn, backpack, stash)
rep("""          const gb = ((cc >= 8 && cc < 16) || cc >= 30) && window.__goldGear && window.__goldGear(ww, inv.slice(0, 8), hid);
          return '<div class="cell ' + (cls || "") + " " + tier(ww) + (gb ? " gb" : "")""",
    """          let gb = ((cc >= 8 && cc < 16) || cc >= 30) && window.__goldGear && window.__goldGear(ww, inv.slice(0, 8), hid);
          const rw = window.__goldGear && window.__goldGear.cant && window.__goldGear.cant(ww, hid, H8[hero + 0x19C] + 1);
          if (rw) gb = false;   // red wins: it can't go on yet
          return '<div class="cell ' + (cls || "") + " " + tier(ww) + (gb ? " gb" : "") + (rw ? " rw" : "")""")
# HD Forge / Shrine: backpack boxes and the gear for sale
rep("""        const cell = (cc) => { const gb = gold(wordOf(cc)); return '<div class="cell' + (gb ? " gb" : "")""",
    """        const cant = (w) => !!(window.__goldGear && window.__goldGear.cant && window.__goldGear.cant(w, heroId, lvl));
        const cell = (cc) => { const rw = cant(wordOf(cc)), gb = !rw && gold(wordOf(cc)); return '<div class="cell' + (gb ? " gb" : "") + (rw ? " rw" : "")""")
rep("""          const gb = it && gold(it);""", """          const rw = it && cant(it), gb = it && !rw && gold(it);""")
rep("""          return '<div class="cell sk' + (gb ? " gb" : "")""", """          return '<div class="cell sk' + (gb ? " gb" : "") + (rw ? " rw" : "")""")
open(out, "w", encoding="utf-8").write(s); print("ok red gear")
