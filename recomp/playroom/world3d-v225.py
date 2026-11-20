#!/usr/bin/env python3
"""Play Room v225 "3D World" (Jordan, 2026-11-20): the Story map's first tab is a 3D model of every screen of the game,
joined into one world the way the doors link them, with each hero's campaign path, labels for every screen and land.

  world3d-v225.py in.html out.html

- StoryMap hands its data (names, lands, hero missions, doors, picture sizes, big fights, enemy counts, bonus maps and
  its picture viewer) to window.__smData.
- New "3D World" tab, first and open by default; the Story map's own pinch zoom stays off on it; closing the map or
  changing tab frees the 3D view.
- world3d.js goes in as its own <script id="world3dJs"> (replaced whole if it is there already). It loads three.js
  r128 from lib/three.min.js (published next to the page) only when the tab opens.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8").read()

def rep(a, b, name):
    global s
    if b in s: return
    assert s.count(a) == 1, name + " (%d)" % s.count(a)
    s = s.replace(a, b)

rep("        function open() { if (el) return; el = render();",
    "        window.__smData = { NAMES, REG, region, HEROES, BOSS, SIDE, COUNTS, BONUS, SZ, EE, pic: (l) => pic(l) };   // v225: for the 3D World\n"
    "        function open() { if (el) return; el = render();", "data")
rep('        let tab = "story";', '        let tab = "world";   // v225: the 3D World opens first', "tab")
rep("""top.innerHTML = '<div class="sm-tabs"><button type="button" data-t="story"'""",
    """top.innerHTML = '<div class="sm-tabs"><button type="button" data-t="world"' + (tab === "world" ? ' class="on"' : "") + '>3D World</button><button type="button" data-t="story"'""", "tabs")
rep("""'<span><b class="n"></b>Screen</span><span><b class="boss"></b>Big monster</span>' : "";""",
    """'<span><b class="n"></b>Screen</span><span><b class="boss"></b>Big monster</span>' : tab === "world" ? '<span><b style="background:#e8b84a;height:5px;vertical-align:2px"></b>Door between screens</span><span><b style="background:repeating-linear-gradient(90deg,#cfc6b0 0 4px,transparent 4px 7px);height:3px;vertical-align:3px"></b>Story jump</span>' : "";""", "legend")
rep("if (tab === b.dataset.t) return; tab = b.dataset.t;", "if (tab === b.dataset.t) return; if (window.World3D) World3D.unmount(); tab = b.dataset.t;", "switch")
rep("          pinch(sc);\n", "          if (tab !== \"world\") pinch(sc);\n", "pinch")
rep('          if (tab === "siege") { siegeView(sc); return box; }\n',
    '          if (tab === "siege") { siegeView(sc); return box; }\n          if (tab === "world") { if (window.World3D) World3D.mount(sc, window.__smData); return box; }\n', "mount")
rep("        function close() { closePic(); if (el) {", "        function close() { closePic(); if (window.World3D) World3D.unmount(); if (el) {", "close")

js = open(os.path.join(HERE, "world3d.js"), encoding="utf-8").read()
block = '<script id="world3dJs">\n' + js + "\n</script>\n"
if 'id="world3dJs"' in s:
    s = re.sub(r'<script id="world3dJs">.*?</script>\n', lambda m: block, s, count=1, flags=re.S)
else:
    assert s.count("</body></html>") == 1, "body"
    s = s.replace("</body></html>", block + "</body></html>")
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
