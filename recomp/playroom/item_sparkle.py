# Items on the ground sparkle (Jordan, 2026-11-12: "make items on the ground sparkle a little bit to better see them").
# The page reads the game's entity list each frame (ground items: update fn 0x0802F131, state +0x63 == 3, x/y +0xAE/+0xB2,
# type +0x60), passes up to 16 item positions to the lighting pass, and the final pass draws a soft pulsing glow and a
# small four-point glint that flashes now and then over each item (each item on its own beat). Gear glints gold,
# food and herbs green, gems pale blue. Screen blend, so it only adds light; the HUD strip is left alone. Our own effect.
# Needs Rich lighting on. Test: window.__itemsDbg = [[x, y, type], ...] in game pixels of the shown picture.
# Usage: python3 item_sparkle.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
J = lambda t: t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

rep("uniform vec2 AuraP; uniform float AuraK;", "uniform vec2 AuraP; uniform float AuraK; uniform vec3 Items[16]; uniform int ItemN;")
GL = r'''  // ---- Items on the ground (2026-11-12): a soft pulse and a glint now and then, so they are easy to spot ----
  for (int i = 0; i < 16; i++) {
    if (i >= ItemN) break;
    vec2 d = p - Items[i].xy; if (dot(d, d) > 196.0) continue;
    float fi = float(i), ty = Items[i].z;
    vec3 ic = ty >= 25.0 ? vec3(1.0, 0.86, 0.5) : (ty == 13.0 || ty == 14.0) ? vec3(0.7, 0.9, 1.0) : vec3(0.72, 1.0, 0.62);
    float pulse = 0.55 + 0.45 * sin(Time * 2.6 + fi * 2.1);
    float a = exp(-dot(d, d) / 30.0) * 0.28 * pulse;
    float ph = Time * 0.45 + fi * 0.37, beat = floor(ph), fb = fract(ph);
    float fl = smoothstep(0.0, 0.08, fb) * (1.0 - smoothstep(0.08, 0.3, fb));   // a quick flash once every ~2 s
    vec2 gp = d - (vec2(hsh(vec2(beat, fi)), hsh(vec2(fi, beat + 3.0))) - 0.5) * 7.0;   // the glint lands on a new spot each time
    float r = 1.5 + 6.0 * fl;
    float star = exp(-abs(gp.x) * 2.2 / r) * exp(-gp.y * gp.y * 2.5) + exp(-abs(gp.y) * 2.2 / r) * exp(-gp.x * gp.x * 2.5);
    a += (star * 1.2 + exp(-dot(gp, gp) / 2.5) * 0.8) * fl;
    vec3 add = mix(ic, vec3(1.0), 0.35 * fl) * a * mix(1.0, 1.15, Night);
    c = 1.0 - (1.0 - clamp(c, 0.0, 1.0)) * (1.0 - clamp(add, 0.0, 1.0));
  }
'''
rep(J("  // ---- Gandalf's aura (2026-11-10)"), J(GL) + J("  // ---- Gandalf's aura (2026-11-10)"))

JS = r'''  // Items on the ground (2026-11-12): positions on the game picture of up to 16 items lying in the level.
  const itemsPos = (w, h) => {
    if (window.__itemsDbg) return window.__itemsDbg;
    try {
      const M = window.__wideM; if (!M || !M._rotk_iwram) return null;
      const H8 = M.HEAPU8, ib = M._rotk_iwram(), eb = M._rotk_ewram(), dv = new DataView(H8.buffer);
      if (H8[ib + 0x41B0] !== 1) return null;
      const at = (ptr) => ptr >= 0x2000000 && ptr < 0x2040000 ? eb + (ptr - 0x2000000) : 0;
      const r32 = (ptr) => { const o = at(ptr); return o ? dv.getUint32(o, true) : 0; };
      let p = dv.getUint32(ib + 0x3C00, true), n = 0; if (!at(p)) return null;
      while (n++ < 400) { const nx = r32(p); if (!at(nx)) break; p = nx; }
      const cx = dv.getInt32(ib + 0x20F8, true), cy = dv.getInt32(ib + 0x20FC, true), out = [];
      n = 0; while (at(p) && n++ < 400 && out.length < 16) {
        const o = at(p);
        if (dv.getUint32(o + 0x14, true) === 0x0802f131 && H8[o + 0x63] === 3) {
          const x = dv.getInt16(o + 0xAE, true) - cx + (w - 240) / 2, y = dv.getInt16(o + 0xB2, true) - cy + (h - 160) / 2 - 4;
          if (x > -16 && x < w + 16 && y > -16 && y < h + 16) out.push([x, y, H8[o + 0x60]]);
        }
        p = r32(p + 4);
      }
      return out;
    } catch (e) { return null; }
  };
'''
rep("  const ALIVE_GLSL = ", JS + "  const ALIVE_GLSL = ")
rep("          { const ap = auraPos(stride, h);",
    "          if (fu.ItemN) { const its = itemsPos(stride, h) || [], n = Math.min(16, its.length), a = new Float32Array(48);\n"
    "            for (let i = 0; i < n; i++) { a[i * 3] = its[i][0] - sx; a[i * 3 + 1] = its[i][1] - sy; a[i * 3 + 2] = its[i][2]; }\n"
    "            gl.uniform1i(fu.ItemN, n); if (fu['Items[0]']) gl.uniform3fv(fu['Items[0]'], a); }\n"
    "          { const ap = auraPos(stride, h);")
open(out, "w").write(s); print("ok sparkle")
