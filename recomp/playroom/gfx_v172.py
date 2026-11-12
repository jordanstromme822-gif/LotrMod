# Graphics High/Low (Jordan, 2026-11-12: "Even solo it slows down huge with the graphics we added").
# Measured (tools/lightbench/perf.js, 344x160 game picture): almost all the cost is the final lighting pass, which ran once
# per screen pixel. A 3x phone in landscape has ~3 million of them, while the sharpened picture it reads is only 3x the
# game size (~1032x480). So the canvas is now capped: High = longest side 1280 px, Low = 860 px; the browser stretches
# it to fill the screen (smooth). Low also skips the living fire/trees/shadow pass. Setup screen chip "Graphics: High/Low"
# (localStorage rotk-gfx). If the picture rate stays under 40 a second on High, the page drops to Low first; only if Low
# is still too slow does it fall back to plain pixels as before.
# Usage: python3 gfx_v172.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)

# 1. Canvas size capped while Sharp HD is on.
rep("""      const W = Math.max(1, Math.round(r.width * d)), H = Math.max(1, Math.round(r.height * d));
      if (r.width > 0""",
"""      let W = Math.max(1, Math.round(r.width * d)), H = Math.max(1, Math.round(r.height * d));
      this._gfx = !!(window.__gfxLow && window.__gfxLow()); if (this.sharp && !this.plain) { const cap = window.__gfxLow && window.__gfxLow() ? 860 : 1280, k = Math.min(1, cap / Math.max(W, H)); W = Math.max(1, Math.round(W * k)); H = Math.max(1, Math.round(H * k)); }
      if (r.width > 0""")

# Refit when the setting changes.
rep("        if (this.fitDue !== false) this.fit();", "        if (this.fitDue !== false || this._gfx !== !!(window.__gfxLow && window.__gfxLow())) this.fit();")

# 2. Too slow: High -> Low first, then plain.
rep("""            if (this.slow >= 2) { this.plain = true; (window.__wideLog || (window.__wideLog = [])).push("sharp off, fps " + fps.toFixed(1)); }""",
"""            if (this.slow >= 2 && window.__gfxLow && !window.__gfxLow()) { window.__gfxSet(true, true); this.slow = 0; (window.__wideLog || (window.__wideLog = [])).push("graphics low, fps " + fps.toFixed(1)); }
            else if (this.slow >= 2) { this.plain = true; this.fitDue = true; (window.__wideLog || (window.__wideLog = [])).push("sharp off, fps " + fps.toFixed(1)); }""")

# 3. Low skips the living fire/trees/shadow pass.
rep("if (aliveP && aT && !window.__aliveOff && (", "if (aliveP && aT && !window.__aliveOff && !(window.__gfxLow && window.__gfxLow()) && (")

# 4. Setup chip + setting.
rep("""<button id="lightSetup" class="chip" """,
"""<button id="gfxSetup" class="chip" type="button" style="display:block;margin:8px auto 0" onclick="window.__toggleGfx&&__toggleGfx()">Graphics: High</button>
<button id="lightSetup" class="chip" """)
rep("""  // Rich lighting on/off: setup screen button, or G on a keyboard while playing.""",
"""  // Graphics High/Low (2026-11-12): Low = smaller drawing size + no living fire/trees pass. Auto-set to Low when too slow.
  window.__gfxLow = () => { try { return localStorage.getItem("rotk-gfx") === "low"; } catch (e) { return !!window.__gfxLowMem; } };
  const gfxShow = () => { const b = document.getElementById("gfxSetup"); if (b) b.textContent = "Graphics: " + (window.__gfxLow() ? "Low" : "High"); };
  window.__gfxSet = (low, auto) => { window.__gfxLowMem = low; try { localStorage.setItem("rotk-gfx", low ? "low" : "high"); } catch (e) {} gfxShow();
  };
  window.__toggleGfx = () => window.__gfxSet(!window.__gfxLow(), false);
  window.addEventListener("DOMContentLoaded", gfxShow); setTimeout(gfxShow, 0);
  // Rich lighting on/off: setup screen button, or G on a keyboard while playing.""")
open(out, "w").write(s); print("ok gfx")
