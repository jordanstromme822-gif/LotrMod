#!/usr/bin/env python3
"""Play Room v224 "modern classic" (Jordan, 2026-11-20): HD Stats and Skills pages, the Backpack / Forge / Shrine in the
new menus' look, and a bigger HUD (all in hd-pages.js).

  hd-pages-v224.py in.html out.html

- WideHost.draw() hands out the game's last finished picture (window.__gbaFrame) so the pages can cut the game's own
  skill icons, hero picture and skill orb out of it, and skips drawing the picture while the HD Stats / Skills page
  covers it (as it already does for the Backpack and the Forge / Shrine).
- The Backpack's page buttons say where they go: L opens Stats, R opens Skills.
- hd-menus.js (window.__hdPaint for the shared backdrop) is swapped in, and hd-pages.js goes in as its own <script>
  right after it (replaced whole if it is there already).
"""
import os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8").read()

a = """    draw() {
      if (!this.d || !this.canvas) return;
"""
b = a + """      // v224: the game's last finished picture (RGB, 3 bytes a pixel) for the HD Stats / Skills pages and the HD HUD.
      if (!window.__gbaFrame) { const WH = this; window.__gbaFrame = () => { const u = WH.u32(), b = WH.ptr + WH.d.video + WH.front * WH.d.videoStride; return { u8: new Uint8Array(u.buffer), off: b + WH.d.pixels, w: u[b >> 2], h: u[(b >> 2) + 1] }; }; }
"""
if "window.__gbaFrame" not in s:
    assert s.count(a) == 1, "draw"; s = s.replace(a, b)

a = "        if (this.keepAspect && !native && w > 0 && h > 0) { const k = Math.min(CW / w, CH / h), dw = Math.round(w * k), dh = Math.round(h * k); dest = [(CW - dw) >> 1, (CH - dh) >> 1, dw, dh]; }\n"
b = a + "        window.__gbaView = { w, h, sx, sy, sw, sh, dest, CW, CH };   // v224: where the picture lands (the HD HUD covers the game's own)\n"
if "window.__gbaView" not in s:
    assert s.count(a) == 1, "view"; s = s.replace(a, b)

a = "      if (window.__hdShopOn || window.__hdBpOn) { this.pumpAudio(); return; }"
b = "      if (window.__hdShopOn || window.__hdBpOn || window.__hdPgOn) { this.pumpAudio(); return; }"
if b not in s:
    assert s.count(a) == 1, "skip draw"; s = s.replace(a, b)

a = """R += '<div class="bar"><b data-k="L">&#9666; L Skills</b><b data-k="R">Stats R &#9656;</b></div>';"""
b = """R += '<div class="bar"><b data-k="L">&#9666; L&nbsp; Stats</b><b data-k="R">Skills &nbsp;R &#9656;</b></div>';"""
if b not in s:
    assert s.count(a) == 1, "backpack bar"; s = s.replace(a, b)

open(dst, "w", encoding="utf-8").write(s)
subprocess.check_call([sys.executable, os.path.join(HERE, "hd-menus-v215.py"), dst, dst])
s = open(dst, encoding="utf-8").read()
js = open(os.path.join(HERE, "hd-pages.js"), encoding="utf-8").read().rstrip("\n")
block = '<script id="hdPagesJs">\n' + js + "\n</script>\n"
if 'id="hdPagesJs"' in s:
    s = re.sub(r'<script id="hdPagesJs">.*?</script>\n', lambda m: block, s, count=1, flags=re.S)
else:
    m = re.search(r'<script id="hdMenusJs">.*?</script>\n', s, flags=re.S)
    assert m, "hdMenusJs"
    s = s[:m.end()] + block + s[m.end():]
open(dst, "w", encoding="utf-8").write(s)
print("ok v224", len(s))
