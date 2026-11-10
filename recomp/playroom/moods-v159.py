# Valheim-style moods (Jordan 2026-11-10): torch-light pools, night grade, drifting mist, corner shading, ash; colourful
# attacks light the dark around them. Patches the live Play Room page in place (lighting code from v150).
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
J = lambda t: t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

# 1. glow program: Extract 2 = coloured light emitters (bright + saturated, any hue) boxed 8x8 down to 1/8 size;
#    Extract 3 = wide 17-tap blur along Dir (one texel steps, so no ghost copies).
rep('void main(){ vec2 d = Dir / TextureSize; vec4 s = tap(v) * 0.2270270;',
    'uniform vec2 SrcPx; uniform float HudY;\\n" +\n'
    '    "vec4 em(vec2 uv){ vec3 c = texture(Texture, uv).rgb; float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)); float sat = (mx - mn) / max(mx, 0.001);\\n" +\n'
    '    "  float b = smoothstep(Thr, Thr + 0.14, mx) * smoothstep(0.45, 0.75, sat) * (1.0 - step(HudY, uv.y)); return vec4(c * b, 0.0); }\\n" +\n'
    '    "void main(){ if (Extract == 2) { vec4 e = vec4(0.0); for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++) e += em(v + SrcPx * vec2(float(x) * 2.0 - 3.0, float(y) * 2.0 - 3.0)); o = e / 16.0; return; }\\n" +\n'
    '    "  if (Extract == 3) { vec2 dd = Dir / TextureSize; vec4 e = vec4(0.0); float ws = 0.0; for (int i = -8; i <= 8; i++) { float wt = exp(-float(i * i) / 40.0); e += texture(Texture, v + dd * float(i)) * wt; ws += wt; } o = e / ws; return; }\\n" +\n'
    '    "  vec2 d = Dir / TextureSize; vec4 s = tap(v) * 0.2270270;')

# 2. final pass: uniforms + noise, then the mood block before the glow is screened on.
rep('uniform vec2 Px, GPx;\\nfloat luma(vec3 c)',
    J('uniform vec2 Px, GPx;\nuniform sampler2D Torch; uniform vec3 NightTint, TorchCol, MistCol; uniform float Night, TorchK, Mist, AO, Ash, HudY; uniform vec2 Aspect;\n'
      'float hsh(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }\n'
      'float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(hsh(i), hsh(i + vec2(1.0, 0.0)), f.x), mix(hsh(i + vec2(0.0, 1.0)), hsh(i + vec2(1.0, 1.0)), f.x), f.y); }\n') + 'float luma(vec3 c)')
MOOD = '''  // ---- Moods (Jordan, 2026-11-10, Valheim-style mock-up approved): night grade, flickering light pools from torches, fire
  // and bright colourful attacks (each lights its surroundings in its own colour), corner shading, drifting mist, falling ash.
  // The HUD strip at the bottom is left alone so health and bars stay readable.
  float mx0 = max(c0.r, max(c0.g, c0.b)), sat0 = (mx0 - min(c0.r, min(c0.g, c0.b))) / max(mx0, 0.001);
  float hud = step(HudY, v.y) * smoothstep(0.55, 0.75, sat0) * step(0.3, mx0) * (1.0 - step(max(c0.r, c0.b) + 0.04, c0.g));   // HUD frame, lamp, orb and bars are bright and colourful; stone around them is not
  float lt = 0.0; vec3 cPre = c;
  if ((Night > 0.001 || TorchK > 0.001)) {
    vec3 T = texture(Torch, v).rgb;
    float fl = 0.86 + 0.08 * sin(Time * 8.3 + v.x * 9.0) + 0.06 * sin(Time * 21.7 + v.y * 13.0);
    float tm = max(T.r, max(T.g, T.b)); vec3 hue = mix(vec3(1.0, 0.72, 0.42), T / max(tm, 1e-5), 0.45);   // flames warm, attacks keep some of their colour
    lt = ((1.0 - exp(-max(tm - 0.005, 0.0) * 90.0)) * 1.6) * TorchK * fl; vec3 L = hue * lt;
    vec3 nc = mix(c, vec3(luma(c)), 0.45) * NightTint; nc *= 1.0 - 0.35 * smoothstep(0.35, 0.9, luma(nc));   // bright stone dims more, so night stays night
    c = mix(c, nc, Night * (1.0 - 0.85 * clamp(lt, 0.0, 1.0))) + (c * L * TorchCol + L * 0.08) * (1.0 - 0.8 * smoothstep(0.35, 0.85, luma(c)));   // already-bright things (lava) are not lit again   // inside a pool the warm light wins over the night tint
  }
  if (AO > 0.001) c *= mix(1.0, 0.45 + 0.55 * smoothstep(0.02, 0.36, g.a), AO);
  if (Mist > 0.001) {
    vec2 mp = v * Aspect * 2.6;
    float n = vn(mp + vec2(Time * 0.045, Time * 0.011)) * 0.6 + vn(mp * 2.3 + vec2(-Time * 0.07, Time * 0.02)) * 0.4;
    float mm = Mist * (0.35 + 0.65 * v.y) * smoothstep(0.3, 0.8, n) * (1.0 - clamp(lt, 0.0, 1.0) * 0.6);
    c = mix(c, MistCol * (0.75 + 0.5 * n), mm);
  }
  if (Ash > 0.001) {
    for (int k = 0; k < 2; k++) {
      float sc = k == 0 ? 16.0 : 28.0;
      vec2 ap = v * Aspect * sc + vec2(sin(Time * 0.6 + float(k) * 2.0) * 0.9, -Time * (k == 0 ? 1.0 : 0.65));
      vec2 ci = floor(ap), cf = fract(ap); float hr = hsh(ci + float(k) * 17.0);
      if (hr > 0.6) {
        vec2 pp = vec2(hsh(ci + 3.1), hsh(ci + 7.7)) * 0.7 + 0.15;
        float a = (1.0 - smoothstep(0.02, k == 0 ? 0.1 : 0.08, length(cf - pp))) * Ash * (0.75 + 0.25 * sin(Time * 3.0 + hr * 40.0));
        vec3 ac = hr > 0.95 ? vec3(1.0, 0.5, 0.18) * 1.3 : vec3(0.78, 0.75, 0.72);   // grey ash with a few glowing embers
        c = mix(c, ac, a * (k == 0 ? 0.85 : 0.6));
      }
    }
  }
  c = mix(c, cPre, hud);
'''
rep('  vec3 gw = g.rgb * GlowK * GlowTint; c = 1.0', J(MOOD) + '  vec3 gw = g.rgb * GlowK * GlowTint; c = 1.0')

# 3. looks: new values on every look (off by default) and the mood looks.
rep("Thr: 0.55, Water: 1.0, WaterCol: [0.16, 0.42, 0.62] };",
    "Thr: 0.55, Water: 1.0, WaterCol: [0.16, 0.42, 0.62],\n"
    "      Night: 0.0, NightTint: [1.0, 1.0, 1.0], TorchK: 0.0, TorchCol: [1.0, 0.8, 0.6], LThr: 0.84, Mist: 0.0, MistCol: [0.55, 0.62, 0.72], AO: 0.0, Ash: 0.0 };")
rep("      level: base,",
    "      // Moods (Jordan, 2026-11-10): misty night at Helm's Deep, ash and red sky over Mordor, torch-lit halls and caves.\n"
    "      \"Helm's Deep\": L({ Night: 0.9, NightTint: [0.36, 0.42, 0.56], TorchK: 1.0, TorchCol: [1.0, 0.72, 0.45], Mist: 0.6, MistCol: [0.36, 0.42, 0.52], AO: 0.45, Vig: 0.42, Sun: 0.0, GlowK: 1.3, Sat: 1.1, ShadowTint: [-0.01, 0.0, 0.04], HiTint: [0.03, 0.02, 0.0], Gain: [1.02, 1.02, 1.03] }),\n"
    "      Mordor: L({ Night: 0.55, NightTint: [0.78, 0.5, 0.45], TorchK: 0.9, TorchCol: [1.0, 0.7, 0.45], Ash: 0.8, Mist: 0.22, MistCol: [0.3, 0.12, 0.08], AO: 0.4, Vig: 0.4, Sun: 0.0, GlowK: 1.25, GlowTint: [1.0, 0.55, 0.25], ShadowTint: [0.04, 0.0, -0.01], HiTint: [0.04, 0.0, -0.01], Gain: [1.04, 0.97, 0.92] }),\n"
    "      level: base,")
for g, add in [("Lava", "Night: 0.3, NightTint: [0.85, 0.55, 0.5], TorchK: 0.3, Ash: 0.7, AO: 0.35, "),
               ("Wasteland", "Night: 0.4, NightTint: [0.8, 0.58, 0.52], TorchK: 0.8, Ash: 0.55, AO: 0.35, "),
               ("\"Dwarf halls\"", "Night: 0.35, NightTint: [0.7, 0.72, 0.85], TorchK: 1.0, AO: 0.4, "),
               ("Caves", "Night: 0.35, NightTint: [0.68, 0.72, 0.85], TorchK: 1.0, AO: 0.4, ")]:
    rep("      %s: L({ " % g, "      %s: L({ %s" % (g, add))
rep('["Ruins", [121]]];\n    const byLevel', '["Ruins", [121]], ["Helm\'s Deep", [46, 47]], ["Mordor", [6, 7, 8, 10, 12, 13, 58]]];\n    const byLevel')

# 4. render: two quarter-size light maps, built when the look has night or torch light.
rep("let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0, gT = [], gF = [];",
    "let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0, gT = [], gF = [], tT = [], tF = [], tw = 1, th = 1;")
rep("""        if (glowP) for (let i = 0; i < 2; i++) {
          const t = tex(w, h, "rgba", gl.LINEAR), fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); gT.push(t); gF.push(fb);
        }""", """        if (glowP) for (let i = 0; i < 2; i++) {
          const t = tex(w, h, "rgba", gl.LINEAR), fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); gT.push(t); gF.push(fb);
        }
        for (const t of tT) gl.deleteTexture(t); for (const f of tF) gl.deleteFramebuffer(f); tT = []; tF = [];
        tw = Math.max(1, Math.ceil(w / 8)); th = Math.max(1, Math.ceil(h / 8));
        if (glowP) for (let i = 0; i < 2; i++) {
          const t = tex(tw, th, "float", gl.LINEAR), fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); tT.push(t); tF.push(fb);
        }""")
rep("""            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
          }
          gl.bindSampler(0, null);
        }""", """            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
          }
          // Light map for the moods: coloured emitters boxed down to 1/8 size, then blurred wide (about 32 game pixels).
          if (cur.Night > 0.01 || cur.TorchK > 0.01) {
            if (gu.SrcPx) gl.uniform2f(gu.SrcPx, 1 / w, 1 / h); if (gu.HudY) gl.uniform1f(gu.HudY, hudY);
            const steps = [[outs[0], 0, 0, 2], [tT[0], 1, 0, 3], [tT[1], 0, 1, 3]];
            for (let i = 0; i < 3; i++) {
              const [src, dx, dy, ex] = steps[i];
              gl.bindFramebuffer(gl.FRAMEBUFFER, tF[i & 1]); gl.viewport(0, 0, tw, th);
              gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, src); gl.bindSampler(0, linS);
              gl.uniform2f(gu.TextureSize, tw, th); gl.uniform2f(gu.Dir, dx, dy); gl.uniform1i(gu.Extract, ex); gl.uniform1f(gu.Thr, cur.LThr);
              gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            }
          }
          gl.bindSampler(0, null);
        }""")
# HUD strip: the bottom 34 rows of the 240-row game picture.
rep("        if (lit) {\n          ease();", "        const hudY = h > 100 ? 1 - 34 / h : 2;\n        if (lit) {\n          ease();")
rep("""          if (fu.Px) gl.uniform2f(fu.Px, 1.2 / w, 1.2 / h);""", """          if (fu.Px) gl.uniform2f(fu.Px, 1.2 / w, 1.2 / h);
          for (const k of ["NightTint", "TorchCol", "MistCol"]) if (fu[k]) gl.uniform3fv(fu[k], cur[k]);
          for (const k of ["Night", "TorchK", "Mist", "AO", "Ash"]) if (fu[k]) gl.uniform1f(fu[k], cur[k]);
          if (fu.HudY) gl.uniform1f(fu.HudY, hudY); if (fu.Aspect) gl.uniform2f(fu.Aspect, w / h, 1);
          gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, tT[0]); gl.bindSampler(3, linS); if (fu.Torch) gl.uniform1i(fu.Torch, 3);""")
open(out, "w").write(s); print("patched")
