"""Play Room v195: smoother HD picture (Jordan, 2026-11-18: "optimize the code to make the game run smoother and more efficient").
Usage: smooth-v195.py playroom-live.html out.html (page only, same engines and game file).

Measured first (real page in headless Chromium, each pass timed with a 1-pixel read after it; Jordan's iPhone play log):
- iPhone 2-player with Sharp HD: 43-46 pictures a second, then the page's slow check dropped to plain pixels (56-60/s).
  So on the phone the HD picture passes are what costs the frames, not the game engine.
- The last lighting pass (LIGHT_FINAL, ~25 texture reads + noise per pixel) ran at the canvas size (up to 1280 wide,
  ~4.3 screen pixels per game pixel) although its main input, the ScaleFX + skin picture, is only 3 pixels per game pixel.
  It was ~45% of all picture work; the "alive" pass (wind, fire, tree shadows) ~20%: it evaluated canopy() (9 reads)
  9 times per pixel, ~110 reads per pixel.
Changes (no look switched off, nothing to pick):
1. The WebGL canvas is never bigger than 3 canvas pixels per game pixel on each axis (uniform when the picture keeps its
   shape); the browser stretches it to the screen like before (a 320x240 view on a sideways phone: 1280 -> 960 wide). The HD picture has 3x detail, so nothing is lost;
   the final pass does ~45% less work on a phone. Impact effects keep their full screen-size canvas.
2. canopy() is computed once per game pixel into its own texture; the alive pass reads that texture at the same
   offsets (bilinear) instead of re-evaluating canopy 9 times. ~70% fewer reads in that pass.
Works in 1-player, P2 and online (all use WideHost + makeSharpHD)."""
import sys
src, out = sys.argv[1:3]
t = open(src).read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)

# ---- 1. canvas at most 3 pixels per game pixel (sharp only) ----
rep('''      this._gfx = !!(window.__gfxLow && window.__gfxLow()); if (this.sharp && !this.plain) { const cap = window.__gfxLow && window.__gfxLow() ? 860 : 1280, k = Math.min(1, cap / Math.max(W, H)); W = Math.max(1, Math.round(W * k)); H = Math.max(1, Math.round(H * k)); }''',
    '''      this._gfx = !!(window.__gfxLow && window.__gfxLow()); if (this.sharp && !this.plain) { const cap = window.__gfxLow && window.__gfxLow() ? 860 : 1280, k = Math.min(1, cap / Math.max(W, H)); W = Math.max(1, Math.round(W * k)); H = Math.max(1, Math.round(H * k)); }
      // v195: the HD picture has 3 pixels per game pixel; drawing the last lighting pass bigger only costs time (the browser stretches the canvas).
      this.fullW = W; this.fullH = H;
      if (this.sharp && !this.plain && this._sw > 0 && this._sh > 0 && !window.__fullRes) { if (this.keepAspect) { const k3 = Math.min(1, Math.max(3 * this._sw / W, 3 * this._sh / H)); W = Math.max(1, Math.round(W * k3)); H = Math.max(1, Math.round(H * k3)); } else { W = Math.min(W, 3 * this._sw); H = Math.min(H, 3 * this._sh); } }''')
rep('''        if (this.fitDue !== false || this._gfx !== !!(window.__gfxLow && window.__gfxLow())) this.fit();
        const CW = this.canvas.width, CH = this.canvas.height;
        let sx = 0, sy = 0, sw = w, sh = h;
        if (native && w >= 240 && h >= 160) { sx = (w - 240) >> 1; sy = (h - 160) >> 1; sw = 240; sh = 160; }''',
    '''        let sx = 0, sy = 0, sw = w, sh = h;
        if (native && w >= 240 && h >= 160) { sx = (w - 240) >> 1; sy = (h - 160) >> 1; sw = 240; sh = 160; }
        if (this.fitDue !== false || this._gfx !== !!(window.__gfxLow && window.__gfxLow()) || this._sw !== sw || this._sh !== sh || this._fr !== !!window.__fullRes) { this._sw = sw; this._sh = sh; this._fr = !!window.__fullRes; this.fit(); }
        const CW = this.canvas.width, CH = this.canvas.height;''')
rep('''        if (window.__fxView) window.__fxView(w, h, sx, sy, sw, sh, dest, CW, CH, this.canvas);''',
    '''        if (window.__fxView) { const on = this.sharp && !this.plain && this.fullW, fx = on ? this.fullW / CW : 1, fy = on ? this.fullH / CH : 1;   // v195: effects stay at full screen size
          window.__fxView(w, h, sx, sy, sw, sh, fx === 1 && fy === 1 ? dest : [dest[0] * fx, dest[1] * fy, dest[2] * fx, dest[3] * fy], Math.round(CW * fx), Math.round(CH * fy), this.canvas); }''')

# ---- 2. canopy once per game pixel ----
i0 = t.index('  const ALIVE_GLSL = "'); i1 = t.index('\n', i0)
line = t[i0:i1]
import json
js = line[line.index('= ') + 2:].rstrip().rstrip(';')
g = json.loads(js)
hdr = g[:g.index('float flame(')]                      # vertex part, uniforms, luma, fol, canopy
can = hdr + 'void main(){ o = vec4(canopy(v), 0.0, 0.0, 1.0); }\n#endif\n'
g2 = g.replace('uniform vec2 SunD;', 'uniform vec2 SunD; uniform sampler2D Can;', 1)
body = g2[g2.rindex('void main(){'):]
nb = body.replace('float can = canopy(v), nb = 0.0;', 'float can = textureLod(Can, v, 0.0).r, nb = 0.0;')
nb = nb.replace('nb = max(nb, canopy(v + vec2(i < 2 ? 1.6 : -1.6, i % 2 == 0 ? 1.6 : -1.6) * GPx));', 'nb = max(nb, textureLod(Can, v + vec2(i < 2 ? 1.6 : -1.6, i % 2 == 0 ? 1.6 : -1.6) * GPx, 0.0).r);')
nb = nb.replace('cs += canopy(v + off * GPx) * w;', 'cs += textureLod(Can, v + off * GPx, 0.0).r * w;')
assert nb.count('canopy(') == 0 and nb.count('textureLod(Can') == 3, nb.count('canopy(')
g2 = g2[:g2.rindex('void main(){')] + nb
t = t[:i0] + '  const ALIVE_GLSL = ' + json.dumps(g2) + ';\n  const CANOPY_GLSL = ' + json.dumps(can) + ';' + t[i1:]

rep('''      let aliveP = null; try { if (glowP) aliveP = prog(ALIVE_GLSL); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("alive: " + (e && e.message || e)); }
      let aT = null, aF = null;''',
    '''      let aliveP = null; try { if (glowP) aliveP = prog(ALIVE_GLSL); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("alive: " + (e && e.message || e)); }
      let canP = null; try { if (aliveP) canP = prog(CANOPY_GLSL); } catch (e) { aliveP = null; (window.__wideLog || (window.__wideLog = [])).push("canopy: " + (e && e.message || e)); }
      let aT = null, aF = null, cT = null, cF = null;''')
rep('''        if (aT) { gl.deleteTexture(aT); gl.deleteFramebuffer(aF); aT = null; }''',
    '''        if (aT) { gl.deleteTexture(aT); gl.deleteFramebuffer(aF); aT = null; }
        if (cT) { gl.deleteTexture(cT); gl.deleteFramebuffer(cF); cT = null; }''')
rep('''        if (aliveP) { aT = tex(w, h, "rgba", gl.LINEAR); aF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, aF); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, aT, 0); }''',
    '''        if (aliveP) { aT = tex(w, h, "rgba", gl.LINEAR); aF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, aF); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, aT, 0);
          cT = tex(w, h, "rgba", gl.LINEAR); cF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, cF); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, cT, 0); }''')
rep('''            const au = aliveP.u; gl.useProgram(aliveP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, aF); gl.viewport(0, 0, w, h);''',
    '''            { const cu = canP.u; gl.useProgram(canP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, cF); gl.viewport(0, 0, w, h);   // v195: canopy once per game pixel
              gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, outs[0]); gl.bindSampler(0, linS); if (cu.Texture) gl.uniform1i(cu.Texture, 0);
              gl.uniformMatrix4fv(cu.MVPMatrix, false, MVP); if (cu.GPx) gl.uniform2f(cu.GPx, 1 / w, 1 / h);
              gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); }
            const au = aliveP.u; gl.useProgram(aliveP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, aF); gl.viewport(0, 0, w, h);
            gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, cT); gl.bindSampler(2, linS); if (au.Can) gl.uniform1i(au.Can, 2);''')
rep('''            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); gl.bindSampler(1, null); aliveOn = 1;''',
    '''            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); gl.bindSampler(1, null); gl.bindSampler(2, null); aliveOn = 1;''')

# ---- 3. water, soft shadow edges and clean-ground slope once per game pixel (PRELIGHT) ----
# All their reads come from game-size pictures (Base = ScaleFX pass 0, Shad, Gd), so they are worked out once per game
# pixel and the last pass reads 3 smoothly scaled results instead of ~35 reads per screen pixel.
i0 = t.index('  const LIGHT_FINAL = "'); i1 = t.index('\n', i0)
line = t[i0:i1]
F = json.loads(line[line.index('= ') + 2:].rstrip().rstrip(';'))
F2 = F
def frep(a, b):
    global F2
    assert F2.count(a) == 1, (a[:80], F2.count(a)); F2 = F2.replace(a, b)
frep('uniform sampler2D Alive;', 'uniform sampler2D Alive; uniform sampler2D Pre0; uniform sampler2D Pre1; uniform sampler2D Pre2;')
gs = F2.index('  if (GdOn > 0.5 && v.y < HudY) {'); ge = F2.index('  // ---- Water')
F2 = F2[:gs] + """  if (GdOn > 0.5 && v.y < HudY) {
    vec4 p2 = textureLod(Pre2, v, 0.0); gm = p2.b * Clean;
    if (gm > 0.002) { c *= mix(1.0, 0.85 + 0.3 * p2.a, clamp(gm, 0.0, 1.0)); c0 = c; }
  }
""" + F2[ge:]
ws = F2.index('  float m = 0.0;\n  if (Water > 0.0) {'); we = F2.index('  float l = luma(c);')
F2 = F2[:ws] + """  float m = 0.0;
  if (Water > 0.0) {
    vec4 w0 = textureLod(Pre0, v, 0.0), w1 = textureLod(Pre1, v, 0.0); m = w0.a; float cloud = w1.a;
    if (cloud > 0.01) c = mix(c, w1.rgb, cloud);
    if (m > 0.01) { vec3 w = mix(c, w0.rgb, 0.88); float wl = luma(w); vec3 body = mix(w, WaterCol * (0.55 + 0.9 * wl), 0.5); c = mix(c, body, m * Water); }
  }
""" + F2[we:]
ss = F2.index('    vec4 s0 = textureLod(Shad, v, 0.0);\n    float rr'); se = F2.index('    float ao = s0.b * (1.0 - 0.5 * sb);'); se = F2.index('\n', se) + 1
F2 = F2[:ss] + '    vec4 ps = textureLod(Pre2, v, 0.0); float sb = ps.r, ao = ps.g;   // v195: worked out per game pixel (PRELIGHT)\n' + F2[se:]
hd = F[:F.index('#else')]
PRE = hd + """#else
precision highp float; in vec2 v; layout(location = 0) out vec4 o0; layout(location = 1) out vec4 o1; layout(location = 2) out vec4 o2;
uniform sampler2D Base; uniform sampler2D Shad; uniform sampler2D Gd; uniform vec2 GPx, SunL; uniform float Water, ShOn, GdOn;
float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
float paleF(vec3 c){ return smoothstep(0.03, 0.08, c.g - c.r) * smoothstep(-0.01, 0.05, c.b - c.r) * smoothstep(0.42, 0.56, luma(c)); }
float wet(vec3 c){ return smoothstep(0.13, 0.2, c.g - c.r) * smoothstep(0.13, 0.2, c.b - c.r) * (1.0 - smoothstep(0.06, 0.14, c.g - c.b)); }
void main(){
  vec3 b0 = texture(Base, v).rgb; vec3 wc = b0, soft = b0; float m = 0.0, cloud = 0.0;
  if (Water > 0.0) {
    m = wet(b0); float pale = paleF(b0); vec3 wsum = vec3(0.0); float wn = 0.0;
    if (m > 0.01 || pale > 0.01) {
      float near = 0.0;
      for (int i = 0; i < 16; i++) {
        float a = float(i) * 0.785398 + (i < 8 ? 0.0 : 0.39); float r = i < 8 ? 4.0 : 8.0;
        vec3 sb = texture(Base, v + vec2(cos(a), sin(a)) * GPx * r).rgb; float pw = paleF(sb); float ww = max(wet(sb), pw * 0.8);
        if (i < 8) near += ww; float cw = wet(sb) * (1.0 - pw); wsum += sb * cw; wn += cw;
      }
      near *= 0.125;
      cloud = pale * smoothstep(0.45, 0.75, near) * smoothstep(0.5, 2.0, wn);
      m = max(m * smoothstep(0.2, 0.5, near + m * 0.3), cloud);
    }
    if (cloud > 0.01) wc = wsum / max(wn, 0.001);
    if (m > 0.01) {
      float w0 = 0.2 * max(wet(b0), 0.05); vec3 sf = b0 * w0; float sw = w0;
      for (int i = 0; i < 8; i++) { float a = float(i) * 0.785398 + 0.39; float r = (i % 2 == 0) ? 1.4 : 2.6; vec3 sb = texture(Base, v + vec2(cos(a), sin(a)) * GPx * r).rgb; float ww = 0.1 * max(wet(sb), 0.05); sf += sb * ww; sw += ww; }
      soft = sf / sw; if (cloud > 0.01) soft = mix(soft, wsum / max(wn, 0.001), cloud);
    }
  }
  float sb = 0.0, ao = 0.0;
  if (ShOn > 0.5) {
    vec4 s0 = textureLod(Shad, v, 0.0);
    float rr = 0.6 + s0.g * 4.0;
    sb = s0.r * 0.4 + (textureLod(Shad, v + vec2(rr, 0.35 * rr) * GPx, 0.0).r + textureLod(Shad, v - vec2(rr, 0.35 * rr) * GPx, 0.0).r
      + textureLod(Shad, v + vec2(-0.35 * rr, rr) * GPx, 0.0).r + textureLod(Shad, v + vec2(0.35 * rr, -rr) * GPx, 0.0).r) * 0.15;
    ao = s0.b * (1.0 - 0.5 * sb);
  }
  float ga = 0.0, gf = 1.0;
  if (GdOn > 0.5) {
    vec4 gd = textureLod(Gd, v, 0.0); ga = gd.a;
    if (ga > 0.0001) {
      vec4 g1 = textureLod(Gd, v + vec2(GPx.x, 0.0), 0.0), g2 = textureLod(Gd, v - vec2(GPx.x, 0.0), 0.0), g3 = textureLod(Gd, v + vec2(0.0, GPx.y), 0.0), g4 = textureLod(Gd, v - vec2(0.0, GPx.y), 0.0);
      float ok = smoothstep(0.85, 1.0, min(min(g1.a, g2.a), min(g3.a, g4.a)));
      vec2 sl = vec2(luma(g1.rgb) - luma(g2.rgb), luma(g3.rgb) - luma(g4.rgb)) * ok;
      gf = clamp(1.0 + 0.9 * dot(sl, SunL), 0.85, 1.15);
    }
  }
  o0 = vec4(soft, m); o1 = vec4(wc, cloud); o2 = vec4(clamp(sb, 0.0, 1.0), clamp(ao, 0.0, 1.0), ga, (gf - 0.85) / 0.3);
}
#endif
"""
t = t[:i1] + '\n  const LIGHT_FINAL2 = ' + json.dumps(F2) + ';\n  const PRELIGHT_GLSL = ' + json.dumps(PRE) + ';' + t[i1:]
rep('''      let canP = null;''', '''      let preP = null, fin2 = null, pT = [], pF = null;
      try { if (glowP) { preP = prog(PRELIGHT_GLSL); fin2 = prog(LIGHT_FINAL2); } } catch (e) { preP = fin2 = null; (window.__wideLog || (window.__wideLog = [])).push("prelight: " + (e && e.message || e)); }
      let canP = null;''')
rep('''        if (cT) { gl.deleteTexture(cT); gl.deleteFramebuffer(cF); cT = null; }''', '''        if (cT) { gl.deleteTexture(cT); gl.deleteFramebuffer(cF); cT = null; }
        for (const q of pT) gl.deleteTexture(q); pT = []; if (pF) { gl.deleteFramebuffer(pF); pF = null; }
        if (preP) { pF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, pF);
          for (let i = 0; i < 3; i++) { const q = tex(w, h, "rgba", gl.LINEAR); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0 + i, gl.TEXTURE_2D, q, 0); pT.push(q); }
          gl.drawBuffers([gl.COLOR_ATTACHMENT0, gl.COLOR_ATTACHMENT1, gl.COLOR_ATTACHMENT2]);
          if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) { preP = null; (window.__wideLog || (window.__wideLog = [])).push("prelight: framebuffer"); } }''')
rep('''          gl.bindSampler(0, null);
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);''', '''          // v195: water, soft shadow edges and ground slope once per game pixel (read by LIGHT_FINAL2)
          if (preP && pF && !window.__preOff) {
            const pu = preP.u; gl.useProgram(preP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, pF); gl.viewport(0, 0, w, h);
            gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, outs[0]); gl.bindSampler(0, linS); if (pu.Base) gl.uniform1i(pu.Base, 0);
            gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, shT); gl.bindSampler(1, linS); if (pu.Shad) gl.uniform1i(pu.Shad, 1);
            gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, gdT); gl.bindSampler(2, linS); if (pu.Gd) gl.uniform1i(pu.Gd, 2);
            gl.uniformMatrix4fv(pu.MVPMatrix, false, MVP); if (pu.GPx) gl.uniform2f(pu.GPx, 1 / w, 1 / h);
            if (pu.Water) gl.uniform1f(pu.Water, cur.Water); if (pu.ShOn) gl.uniform1f(pu.ShOn, shOn); if (pu.GdOn) gl.uniform1f(pu.GdOn, gdOn);
            if (pu.SunL) { const dx = cur.SunDX || 0, dy = 1 + (cur.SunDY || 0), l = Math.hypot(dx, dy) || 1; gl.uniform2f(pu.SunL, -dx / l, -dy / l); }
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); gl.bindSampler(1, null); gl.bindSampler(2, null); preOn = 1;
          }
          gl.bindSampler(0, null);
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);''')
rep('''        const hudY = h > 100 ? 1 - 34 / h : 2; let aliveOn = 0;''', '''        const hudY = h > 100 ? 1 - 34 / h : 2; let aliveOn = 0, preOn = 0;''')
rep('''          const fu = finP.u; gl.useProgram(finP.p);''', '''          const FP = preOn ? fin2 : finP, fu = FP.u; gl.useProgram(FP.p);
          if (preOn) for (let i = 0; i < 3; i++) { gl.activeTexture(gl.TEXTURE7 + i); gl.bindTexture(gl.TEXTURE_2D, pT[i]); gl.bindSampler(7 + i, linS); if (fu["Pre" + i]) gl.uniform1i(fu["Pre" + i], 7 + i); }''')

open(out, 'w').write(t)
print('ok', len(t))
