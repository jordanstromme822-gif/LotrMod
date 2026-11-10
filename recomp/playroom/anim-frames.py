# Extra frames (Graphics phase 4). Patches a Play Room page that already has crisp-skin.
# Off by default (localStorage rotk-anim). Does not edit alive.py or tools/colorplan/.
#
#   python3 anim-frames.py in.html out.html
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
js = open(os.path.join(HERE, "anim-frames.js"), encoding="utf-8").read().rstrip("\n")
js = "\n".join(("  " + ln) if ln else "" for ln in js.split("\n"))

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a))
    s = s.replace(a, b)

if s.count("function animOn()") == 0:
    rep("  function makeSharpHD(gl) {", js + "\n  function makeSharpHD(gl) {")
OLD = "lut[li] = CRISP.map.get(k) || 0;"
NEW = ("let cell = CRISP.map.get(k) || 0;\n"
       "      if (cell && window.__rotkAnimCell) { const alt = window.__rotkAnimCell(k, cell); if (alt) cell = alt; }\n"
       "      lut[li] = cell;")
if s.count(OLD) == 1:
    rep(OLD, NEW)
elif s.count("let cell = CRISP.map.get(k) || 0;") != 1:
    raise SystemExit("anim: crisp LUT line not found")
CHIP = '<button id="animSetup" class="chip" type="button" style="display:block;margin:8px auto 0" onclick="window.__toggleAnim&&__toggleAnim()">Extra frames: Off</button>\n'
if s.count('<button id="crispSetup"') == 1:
    rep('<button id="crispSetup"', CHIP + '<button id="crispSetup"')
elif s.count('<button id="hd2dSetup"') == 1:
    rep('<button id="hd2dSetup"', CHIP + '<button id="hd2dSetup"')
elif s.count('<button id="mapSetup"') == 1:
    rep('<button id="mapSetup"', CHIP + '<button id="mapSetup"')
else:
    raise SystemExit("anim: no setup chip anchor")
open(out, "w", encoding="utf-8").write(s)
print("patched")
