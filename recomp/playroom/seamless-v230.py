#!/usr/bin/env python3
"""Play Room v230 "One big level" (Jordan, 2026-11-20: "Interconnect each level in a 3Dimensional way so it feels
like traveling from each characters start to finish is seamless with no black screens in between"; 2026-11-21: "I want
them to feel like one big level, no line or cut scene, just cohesive movement between maps").

  seamless-v230.py in.html out.html

- seamless.js goes in as its own <script id="seamlessJs"> (replaced whole if it is there already). It wraps
  GbrHost.draw: when the hero takes a door, instead of the game's fade to black, load and fade in, the next screen's
  map picture is joined on past the door and the view scrolls straight on, at the game's zoom, to where the hero comes
  in (v229 flew over the 3D World instead: lift, tilt, gold road).
- The level-load turbo (EWRAM 0x0203FFF1) also runs while window.__seamTurbo is set (from v229; kept if present).
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

rep('H.st("turbo", flag && performance.now() - ffSince < 4000 ? 1 : 0);',
    'H.st("turbo", (flag && performance.now() - ffSince < 4000) || window.__seamTurbo ? 1 : 0);   // v229: also during a door flight',
    "turbo")

js = open(os.path.join(HERE, "seamless.js"), encoding="utf-8").read()
block = '<script id="seamlessJs">\n' + js + "\n</script>\n"
if 'id="seamlessJs"' in s:
    s = re.sub(r'<script id="seamlessJs">.*?</script>\n', lambda m: block, s, count=1, flags=re.S)
else:
    assert s.count("</body></html>") == 1, "body"
    s = s.replace("</body></html>", block + "</body></html>")
open(dst, "w", encoding="utf-8").write(s)
print("ok", len(s))
