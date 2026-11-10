# Gandalf's aura (Jordan, 2026-11-10: Hollow Knight-style feel for Gandalf, our own effect): a soft blue-white glow
# round Gandalf, thin wisps rising through it and small motes drifting up and fading. Drawn by the page's lighting
# pass over the game's own Gandalf sprite, only while Gandalf (hero id 3) is played; stronger at night.
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
J = lambda t: t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
rep("uniform float Night, TorchK, Mist, AO, Ash, HudY; uniform vec2 Aspect;",
    "uniform float Night, TorchK, Mist, AO, Ash, HudY; uniform vec2 Aspect; uniform vec2 AuraP; uniform float AuraK;")
AURA = '''  // ---- Gandalf's aura (2026-11-10): glow, rising wisps, drifting motes (screen blend, so it only adds light) ----
  if (AuraK > 0.001) {
    vec2 d = (v - AuraP) / GPx; float r2 = dot(d, d);
    float a = exp(-r2 / 420.0) * 0.3 * smoothstep(4.0, 12.0, length(d * vec2(1.0, 0.6)));   // soft halo, clear over his body so the sprite stays sharp
    float band = smoothstep(26.0, 14.0, length(d * vec2(1.0, 0.7))) * smoothstep(8.0, 13.0, length(d * vec2(1.0, 0.6)));
    float wn = vn(vec2(d.x * 0.2 + sin(d.y * 0.09 + Time * 1.3) * 0.7, d.y * 0.13 + Time * 1.6));
    float wl = 1.0 - abs(wn - 0.62) / 0.05; a += clamp(wl, 0.0, 1.0) * band * 0.45;   // thin lines where the noise crosses one level
    for (int i = 0; i < 7; i++) {
      float fi = float(i), ph = fract(Time * 0.32 + fi * 0.143);
      vec2 mp = vec2(sin(fi * 2.4 + Time * (0.7 + fi * 0.05)) * (7.0 + fi * 1.6), 10.0 - ph * 42.0);
      float md = length(d - mp); a += exp(-md * md / 1.6) * sin(ph * 3.14159) * 0.9;
    }
    vec3 ac = vec3(0.72, 0.84, 1.0) * a * AuraK * mix(0.65, 1.0, Night);
    c = 1.0 - (1.0 - clamp(c, 0.0, 1.0)) * (1.0 - clamp(ac, 0.0, 1.0));
  }
'''
rep("  c = mix(c, cPre, hud);", J(AURA) + "  c = mix(c, cPre, hud);")
rep("  function makeSharpHD(gl) {", """  // Gandalf's aura: where Gandalf stands on the game picture (centre of his body), or null when he isn't being played.
  // Hero object = [player block 0x03003C00], x/y whole pixels at +0xAE/+0xB2, camera at 0x030020F8/0x030020FC, hero id at
  // player block + 0x19F (3 = Gandalf). The wide view adds (width - 240) / 2 on the left and (height - 160) / 2 on top.
  let auraK = 0;
  const auraPos = (w, h) => {
    try {
      const M = window.__wideM; if (!M || !M._rotk_iwram) return null;
      const H8 = M.HEAPU8, ib = M._rotk_iwram(), dv = new DataView(H8.buffer), P = ib + 0x3C00;
      if (H8[ib + 0x41B0] !== 1 || (H8[P + 0x19F] !== 3 && !window.__auraAny)) return null;
      const ptr = dv.getUint32(P, true);
      const o = ptr >= 0x2000000 && ptr < 0x2040000 ? M._rotk_ewram() + (ptr - 0x2000000) : ptr >= 0x3000000 && ptr < 0x3008000 ? ib + (ptr - 0x3000000) : 0;
      if (!o) return null;
      return [dv.getInt16(o + 0xAE, true) - dv.getInt32(ib + 0x20F8, true) + (w - 240) / 2, dv.getInt16(o + 0xB2, true) - dv.getInt32(ib + 0x20FC, true) + (h - 160) / 2 - 16];
    } catch (e) { return null; }
  };
  function makeSharpHD(gl) {""")
rep("if (fu.HudY) gl.uniform1f(fu.HudY, hudY);",
    "if (fu.HudY) gl.uniform1f(fu.HudY, hudY);\n          { const ap = auraPos(stride, h); auraK += ((ap ? 1 : 0) - auraK) * 0.08; if (ap) window.__auraLast = ap; const lp = ap || window.__auraLast || [0, 0];\n            if (fu.AuraK) gl.uniform1f(fu.AuraK, auraK > 0.01 ? auraK : 0); if (fu.AuraP) gl.uniform2f(fu.AuraP, (lp[0] - sx) / w, (lp[1] - sy) / h); }")
open(out, "w").write(s); print("patched")
