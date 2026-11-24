# Play Room v259: two more torches on level 112 (Rohan hills shrine), on the back colonnade flanking the fountain, so the
# whole shrine is lit at night, not just the front row. Same iron sconce, lit at dusk and night. The back pillars are
# shorter than the front ones, so their plates sit 5 px lower (found by matching the pillar art: back pillars at
# map (428,185) and (683,185)). Usage: python3 torches-v259.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p, encoding='utf-8').read()
old = 'const TORCHES = { 112: [[340, 372, 1, "L"], [515, 372, 1, "L"], [769, 372, 2, "L"]] };'
new = 'const TORCHES = { 112: [[340, 372, 1, "L"], [515, 372, 1, "L"], [769, 372, 2, "L"], [428, 185, 1, "L"], [683, 185, 1, "L"]] };'
assert s.count(old) == 1; s = s.replace(old, new)
open(out, 'w', encoding='utf-8').write(s); print('ok v259 torches')
