# Impact effects (Jordan, 2026-11-17: "full overhaul on animations to make them feel modern"). Adds impact-fx.js to a
# Play Room page and calls it with every new game picture. See impact-fx.js for what it draws and reads.
#   python3 impact_fx.py in.html out.html
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
assert "window.__fxView" not in s, "already patched"
js = open(os.path.join(HERE, "impact-fx.js"), encoding="utf-8").read().rstrip("\n")
js = "\n".join(("  " + ln) if ln else "" for ln in js.split("\n"))
rep("  const WideHost = {", js + "\n  const WideHost = {")
A = "dest = [(CW - dw) >> 1, (CH - dh) >> 1, dw, dh]; }\n"
rep(A, A + "        if (window.__fxView) window.__fxView(w, h, sx, sy, sw, sh, dest, CW, CH, this.canvas);\n")
open(out, "w", encoding="utf-8").write(s); print("ok impact fx")
