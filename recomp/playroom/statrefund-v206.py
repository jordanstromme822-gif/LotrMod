"""Play Room v206: attribute points can be taken back any time (Jordan, 2026-11-20: "stats placed should allow me to
unplace them whenever I want"). Page-only: adds recomp/playroom/statrefund-v206.js (see the notes at its top) in
front of the item text panel module.
Usage: statrefund-v206.py live.html out.html"""
import os, sys
src, out = sys.argv[1:3]
t = open(src).read()
assert '(function statRefund()' not in t
mark = '\n  (function itemPanel() {'
assert t.count(mark) == 1
js = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'statrefund-v206.js')).read()
i = t.index(mark)
t = t[:i] + '\n' + js.rstrip('\n') + t[i:]
open(out, 'w').write(t)
print('ok', len(js))
