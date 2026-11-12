#!/usr/bin/env python3
"""Play Room page patch (Jordan, 2026-11-11): Frodo's crossbow traps get their own faint light, so they are easy to
spot. The page reads the crossbow list the ROM code keeps (tools/orcslots/crossbow.c: XB at EWRAM 0x0203F360,
[player][3] entries of {object, timer, shots, cd}; XN counts at 0x0203F390) and passes up to 6 positions to the
lighting pass (the same place as Gandalf's aura): a soft warm glow on the ground around each trap, breathing slowly,
a little stronger at night. Solo Wide engine only (the lighting pass reads its memory), like the aura.
Usage: trapglow_v171.py in.html out.html path/to/orcslots.sym"""
import sys
src, dst, sym = sys.argv[1:4]
s = open(src).read()
syms = dict((l.split()[0], int(l.split()[1], 16)) for l in open(sym))
XBU = syms["xb_update"] | 1          # a Thumb function pointer, as crossbow.c stores it

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:60], s.count(old)); s = s.replace(old, new)

# shader: uniforms, then the glow just before the HUD mix (screen blend, so it only adds light)
rep("uniform vec2 AuraP; uniform float AuraK;", "uniform vec2 AuraP; uniform float AuraK; uniform vec3 TrapP[6];")
rep("  c = mix(c, cPre, hud);",
    "  // ---- Frodo's crossbow traps (2026-11-11): a faint warm light on the ground around each one ----\\n"
    "  for (int i = 0; i < 6; i++) {\\n"
    "    if (TrapP[i].z < 0.001) continue;\\n"
    "    vec2 d = (v - TrapP[i].xy) / GPx; float r = length(d * vec2(1.0, 1.7));\\n"
    "    float br = 0.85 + 0.15 * sin(Time * 2.2 + float(i) * 1.7);\\n"
    "    float a = (exp(-r * r / 260.0) * 0.55 + exp(-r * r / 30.0) * 0.25) * br * TrapP[i].z * mix(0.9, 1.3, Night);\\n"
    "    c = mix(c, c * vec3(1.18, 1.0, 0.72), clamp(a, 0.0, 1.0));   // warm the ground under it (shows on pale stone too)\\n"
    "    vec3 tc = vec3(1.0, 0.72, 0.34) * a * 0.55;\\n"
    "    c = 1.0 - (1.0 - clamp(c, 0.0, 1.0)) * (1.0 - clamp(tc, 0.0, 1.0));\\n"
    "  }\\n"
    "  c = mix(c, cPre, hud);")

# JS: where the traps are on the game picture
rep("  let auraK = 0;",
    "  // Frodo's crossbow traps (tools/orcslots/crossbow.c): list at EWRAM 0x0203F360 ([player][3] x 8 bytes), counts at 0x0203F390;\n"
    "  // a live one still has its update (xb_update 0x%08X) at + 0x14 and is not dying (+ 0x62 = 4). Position like the aura's.\n"
    "  const trapPos = (w, h) => {\n"
    "    const out = [];\n"
    "    try {\n"
    "      const M = window.__wideM; if (!M || !M._rotk_iwram || !M._rotk_ewram) return out;\n"
    "      const H8 = M.HEAPU8, ib = M._rotk_iwram(), eb = M._rotk_ewram(), dv = new DataView(H8.buffer);\n"
    "      if (H8[ib + 0x41B0] !== 1) return out;\n"
    "      const cx = dv.getInt32(ib + 0x20F8, true), cy = dv.getInt32(ib + 0x20FC, true);\n"
    "      for (let p = 0; p < 2; p++) for (let k = 0; k < Math.min(3, H8[eb + 0x3F390 + p]); k++) {\n"
    "        const ptr = dv.getUint32(eb + 0x3F360 + p * 24 + k * 8, true);\n"
    "        if (ptr < 0x2000000 || ptr >= 0x2040000) continue;\n"
    "        const o = eb + (ptr - 0x2000000);\n"
    "        if (dv.getUint32(o + 0x14, true) !== 0x%08X || H8[o + 0x62] === 4) continue;\n"
    "        out.push([dv.getInt16(o + 0xAE, true) - cx + (w - 240) / 2, dv.getInt16(o + 0xB2, true) - cy + (h - 160) / 2 - 3]);\n"
    "      }\n"
    "    } catch (e) {}\n"
    "    return out;\n"
    "  };\n"
    "  const trapU = new Float32Array(18);\n"
    "  let auraK = 0;" % (XBU, XBU))
rep("if (fu.AuraP) gl.uniform2f(fu.AuraP, (lp[0] - sx) / w, (lp[1] - sy) / h); }",
    "if (fu.AuraP) gl.uniform2f(fu.AuraP, (lp[0] - sx) / w, (lp[1] - sy) / h); }\n"
    "          if (fu[\"TrapP[0]\"]) { const tp = window.__trapOff ? [] : trapPos(stride, h); trapU.fill(0);\n"
    "            tp.slice(0, 6).forEach((q, i) => { trapU[3 * i] = (q[0] - sx) / w; trapU[3 * i + 1] = (q[1] - sy) / h; trapU[3 * i + 2] = 1; });\n"
    "            gl.uniform3fv(fu[\"TrapP[0]\"], trapU); }")
open(dst, "w").write(s)
print("trap glow patched, xb_update 0x%08X" % XBU)
