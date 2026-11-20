# v220 grid menus answer the d-pad all four ways, and Bonus Maps' Choose Your Path is one screen (Jordan, 2026-11-20).
# The work is in hd-menus.js; this marks the HD Backpack's own presses (window.__padOwn) so the page's d-pad handling
# leaves them alone, and swaps in hd-menus.js.
#   python3 grid-v220.py in.html out.html
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
a = """    window.__gameTextSeq = (H8, ew) => H8[ew + 0x3F991];
    const gi = (id, v) => { try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} };"""
b = """    window.__gameTextSeq = (H8, ew) => H8[ew + 0x3F991];
    const gi = (id, v) => { window.__padOwn = (window.__padOwn || 0) + 1; try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} window.__padOwn--; };"""
if b not in s:
    assert s.count(a) == 1, "backpack gi"; s = s.replace(a, b)
open(out, "w", encoding="utf-8").write(s)
subprocess.check_call([sys.executable, os.path.join(HERE, "hd-menus-v215.py"), out, out])
print("ok grid v220")
