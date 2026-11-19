# Play Room v199: the movement feel (smooth walk start, hobbit leg speed; tools/feel) in every engine. The feel wrapper
# moves to ROM 0x8A000 (feel-v194-p2-crashes.py's page changes) and the one engine is regenerated with it as
# [[extra_func]] (recomp/link/feelfuncs.py, engine ?v=199), so 1-player, one-game P2 and online all run it compiled.
# One-game P2 (player 1 inside game 0) gets the hook too.
# Usage: python3 feel-v199.py in.html out.html tools/feel/feel.bin   (feel.bin built at 0x0808A000)
import os, subprocess, sys
src, dst, feel = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(here, "feel-v194-p2-crashes.py"), src, dst, feel], check=True)
s = open(dst).read()
rep = [("      for (let p = 0; p < (net ? 2 : 1); p++) {                      // online: both heroes (both are people)",
        "      const one = !net && !!(M._rotk_link_is_one && M._rotk_link_is_one());   // v199: one-game P2 is player 1 in game 0\n"
        "      for (let p = 0; p < (net || one ? 2 : 1); p++) {               // online: both heroes (both are people); one-game P2 too (smooth start, legs)")]
for a, b in rep:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
assert s.count('"?v=190"') == 2
s = s.replace('"?v=190"', '"?v=199"')
open(dst, "w").write(s)
print("v199 page ok")
