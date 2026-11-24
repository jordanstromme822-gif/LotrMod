# Play Room v260: an upright front-mounted torch bracket ("F") for flat-fronted piers seen head-on, where the leaning side
# sconce would look wrong: a riveted iron wall plate, a tapered cup and an iron basket (two rings and side straps) holding
# the torch upright, a soft cast shadow on the stone, and a soot plume above. Placed on the two outer piers of the parapet
# in the Court of Kings (level 63, Minas Tirith citadel), flanking the White Tree: the Citadel is kept and guarded, so both
# are lit at dusk and night, unlit with charred heads by day. Sprite data from tools/torch/compose.py (front()) ->
# torch-mounted-v260.json (L and R unchanged from v258). Usage: python3 torches-v260.py in.html torch-mounted-v260.json out.html
import json, re, sys
p, data, out = sys.argv[1], sys.argv[2], sys.argv[3]; s = open(p, encoding='utf-8').read()
M = json.load(open(data))
i = s.index('    const MOUNT = '); j = s.index(';\n', i)
s = s[:i] + '    const MOUNT = ' + json.dumps(M, separators=(',', ':')) + s[j:]
old = '[428, 185, 1, "L"], [683, 185, 1, "L"]] };'
new = '[428, 185, 1, "L"], [683, 185, 1, "L"]], 63: [[388, 300, 1, "F"], [668, 300, 1, "F"]] };'
assert s.count(old) == 1; s = s.replace(old, new)
s = s.replace('"L" = on a left face leaning left / "R" = right face leaning right].', '"L" = on a left face leaning left / "R" = right face leaning right / "F" = upright on a flat front face].')
# The light pass only half-detects a flame against pale stone (its emitter test wants a bright, saturated pixel that differs
# from the stone 7 px away), so at night those flames were graded down like the wall. For "F" torches the glow tints pale
# stone warm orange near the flame instead of brightening it to white: the light pass then sees a lit patch and keeps it.
def rep(a, b):
    global s; assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("const glow = (X, Y, r, g, b, rad, k) => {", "const glow = (X, Y, r, g, b, rad, k, pale) => {")
rep("const L = Math.exp(-d) * k, i = at(X + x, Y + y); if (i < 0) continue; keep(i);\n",
    "const L = Math.exp(-d) * k, i = at(X + x, Y + y); if (i < 0) continue; keep(i);\n"
    "        if (pale && heap[i] * 0.3 + heap[i + 1] * 0.59 + heap[i + 2] * 0.11 > 185) { const a = Math.min(0.9, L * 2.0); heap[i] = heap[i] * (1 - a) + 255 * a; heap[i + 1] = heap[i + 1] * (1 - a) + 128 * a; heap[i + 2] = heap[i + 2] * (1 - a) + 34 * a; continue; }   // pale stone: warm tint, not white\n")
rep('if (on && kind === 1) glow(X + fx, Y + fy + 3, 1.0, 0.32, 0.06, 24, 0.55 * fl);', 'if (on && kind === 1) glow(X + fx, Y + fy + 3, 1.0, 0.32, 0.06, 24, 0.55 * fl, side === "F");')
open(out, 'w', encoding='utf-8').write(s); print('ok v260 torches')
