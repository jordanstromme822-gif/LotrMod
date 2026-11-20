#!/usr/bin/env python3
"""Play Room v203 (Jordan, 2026-11-20: "Add in an animation of him bending over to set the trap during the trap setting
delay"). Apply after bolt-trap-v202.py.

  bolt-trap-crouch-v203.py in.html out.html

Frodo's cast (state 10) plays the game's 12-frame cast animation (entries 0x08059514-0x08059554, one per direction,
1 tick a frame); frame 3 is a low bend in every direction. When a new Bolt Trap crossbow shows up (not Quick Drop),
the page puts him back on frame 3 and sets the frame timer (+0x20) to the set-up time left minus the 8 ticks the rest
of the animation takes, so he stays bent over the trap while it is being set and gets up as it arms. The cast state
lasts until the animation ends, so he doesn't walk off meanwhile. Same write path as v202 (online: travels with the
buttons; one-game P2: both players).
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:90]!r}")
    s = s.replace(old, new)

rep('''                if (r8(e + 6) === 10 && cd > 0 && want > cd) btWrite(e + 7, Math.min(255, want));''',
'''                if (r8(e + 6) === 10 && cd > 0 && want > cd) btWrite(e + 7, Math.min(255, want));
                // v203: Frodo stays bent over the trap (cast animation frame 3) for the set-up time
                const an = r32(hero + 0x24), left = Math.max(cd, want);
                if (r8(hero + 0x62) === 10 && an >= 0x08059514 && an <= 0x08059554 && (an & 15) === 4 && r8(hero + 0x23) <= 8 && left > 9) {
                  btWrite(hero + 0x23, 3); btWrite(hero + 0x20, Math.min(255, left - 8));
                }''')

# ---- v203 (Jordan: "Make trap look nicer"): the redrawn bronze ballista (tools/xbbig/xbart.py) and its V-shaped string ----
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
art = open(os.path.join(ROOT, "tools", "xbbig", "xbbig.bin"), "rb").read()
meta = json.load(open(os.path.join(ROOT, "tools", "xbbig", "xbbig.json")))
assert len(art) == 8192 and len(meta["bow"][0]) == 6
s, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x95000\); // v202: crossbow trap 1\.5x, 32x32 sprites \(tools/xbbig/xbbig\.py\)',
               lambda m: 'game.set(hexBytes("%s"), 0x95000); // v203: crossbow trap, bronze ballista, 32x32 sprites (tools/xbbig/xbart.py)' % art.hex(), s)
assert k == 1
s, k = re.subn(r"const XB_TIP = \[.*?\], XB_BOW = \[.*?\];\n",
               lambda m: "const XB_TIP = %s, XB_BOW = %s;   // v203: bow = string end, nock, string end\n" % (json.dumps(meta["tip"]), json.dumps(meta["bow"])), s, flags=re.S)
assert k == 1
rep("        out.push([x0 + t[0], y0 + t[1], x0 + b[0], y0 + b[1], x0 + b[2], y0 + b[3]]);",
    "        out.push([x0 + t[0], y0 + t[1], x0 + b[0], y0 + b[1], x0 + b[4], y0 + b[5], x0 + b[2], y0 + b[3]]);")
rep("trapTU = new Float32Array(24), trapSU = new Float32Array(24);", "trapTU = new Float32Array(24), trapSU = new Float32Array(24), trapNU = new Float32Array(12);")
rep("trapTU.fill(0); trapSU.fill(0);", "trapTU.fill(0); trapSU.fill(0); trapNU.fill(0);")
rep("trapSU.set([(q[2] - sx) / w, (q[3] - sy) / h, (q[4] - sx) / w, (q[5] - sy) / h], 4 * i); });",
    "trapSU.set([(q[2] - sx) / w, (q[3] - sy) / h, (q[4] - sx) / w, (q[5] - sy) / h], 4 * i); trapNU.set([(q[6] - sx) / w, (q[7] - sy) / h], 2 * i); });")
rep('if (fu["TrapS[0]"]) gl.uniform4fv(fu["TrapS[0]"], trapSU); }', 'if (fu["TrapS[0]"]) gl.uniform4fv(fu["TrapS[0]"], trapSU); if (fu["TrapN[0]"]) gl.uniform2fv(fu["TrapN[0]"], trapNU); }')
rep("uniform vec4 TrapT[6]; uniform vec4 TrapS[6];", "uniform vec4 TrapT[6]; uniform vec4 TrapS[6]; uniform vec2 TrapN[6];", 2)
OLD = ("    vec2 a0 = TrapS[i].xy, a1 = TrapS[i].zw, ab = (a1 - a0) / GPx, ap = (v - a0) / GPx;\\n"
       "    float tt = clamp(dot(ap, ab) / max(dot(ab, ab), 0.0001), 0.0, 1.0); vec2 q2 = ap - ab * tt;\\n"
       "    float sg = (exp(-dot(q2, q2) / 0.9) * 0.32 + exp(-dot(q2, q2) / 6.0) * 0.16) * mix(1.0, 1.3, Night);\\n")
NEW = ("    vec2 nk = TrapN[i], a0 = TrapS[i].xy, a1 = TrapS[i].zw;\\n"
       "    vec2 ab = (nk - a0) / GPx, ap = (v - a0) / GPx; vec2 q2 = ap - ab * clamp(dot(ap, ab) / max(dot(ab, ab), 0.0001), 0.0, 1.0);\\n"
       "    vec2 cb = (nk - a1) / GPx, cp = (v - a1) / GPx; vec2 q3 = cp - cb * clamp(dot(cp, cb) / max(dot(cb, cb), 0.0001), 0.0, 1.0);\\n"
       "    float dq = min(dot(q2, q2), dot(q3, q3));\\n"
       "    float sg = (exp(-dq / 0.9) * 0.32 + exp(-dq / 6.0) * 0.16) * mix(1.0, 1.3, Night);\\n")
rep(OLD, NEW, 2)
open(dst, "w", encoding="utf-8").write(s)
print("v203 ballista patched")
