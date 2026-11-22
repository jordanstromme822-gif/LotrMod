# Play Room v240: in the 3D World, the screen names and banners hide while MOVE (arrange) is on, so they don't
# cover the screens you're dragging (the start-up hint bubble goes too). They come back on DONE or when MOVE is tapped off.
# Usage: python3 world3d-v240.py index.html|world3d.js
import sys
p = sys.argv[1]; s = open(p).read()
old = """      const mb = ctl.querySelector('[data-c="move"]'); mb.classList.toggle("on", arrOn); arrBar.classList.toggle("on", arrOn);\n"""
new = old + """      labLayer.style.display = arrOn ? "none" : "";\n"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
old = """else if (c === "move") { arrOn = !arrOn; arrUi(); if (arrOn) showCard(-1); return; }"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, """else if (c === "move") { arrOn = !arrOn; arrUi(); if (arrOn) { showCard(-1); help.style.display = "none"; } return; }""")
open(p, "w").write(s)
