"""Play Room v235 (Jordan, 2026-11-21): "Can we do everything possible to get better resolution and make the game feel modern".
Usage: sharp-v235.py in.html out.html   (in.html = live page, v234 seamless bridge; page only, same engines, game file and files).

What was in the way (read from the v233/v234 page):
- The HD picture (ScaleFX 3x + lighting) was drawn on a canvas capped at 1280 wide and at 3 canvas pixels per game pixel
  (v195), and the browser stretched that canvas to the screen with a soft bilinear blur. On an iPhone held sideways the
  game area is ~2500 screen pixels wide, so every HD pixel was smeared over ~2.6 screen pixels.
- The slow check dropped to Low, then to raw pixels (blurred by the browser) whenever the game ran under 40 pictures a
  second for 8 s. In Moria the iPhone is held back by the game engine itself (~41-49/s, see feel-v223), so a dip there
  threw the HD picture away for the rest of the session although drawing less did not make anything faster.
Changes (no options, best quality on):
1. Full screen resolution: the canvas is the game area in the screen's own pixels (up to 2880 on the long side). The
   heavy lighting pass still runs at 3x game size (same cost as before), into its own texture; then one light pass
   scales it to the screen with Catmull-Rom (5 taps; sharp, no blur) plus contrast-adaptive sharpening (CAS-style,
   4 taps, clamped so there are no halos).
2. Smarter slow check: a quality step down is now a trial. Full res -> 3x canvas -> Low -> raw pixels, one step at a time;
   if the picture rate didn't get at least 10% better (or reach 40/s) after 8 s, the step is undone and not tried again.
Works in 1-player, P2 and online (all use WideHost + makeSharpHD). window.__upOff = true draws the old way (tests);
window.__sharpK (0-1, default 0.35) is the sharpening amount.
"""
import sys
src, out = sys.argv[1:3]
t = open(src, encoding="utf-8").read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)

UP = ("#if defined(VERTEX)\\nin vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;\\n"
      "void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }\\n#else\\n"
      "precision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture; uniform vec2 TexSize; uniform float Up; uniform float Sharp;\\n"
      "vec3 T(vec2 p){ return texture(Texture, p).rgb; }\\n"
      "vec3 cr(vec2 uv){ vec2 sp = uv * TexSize, t1 = floor(sp - 0.5) + 0.5, f = sp - t1;\\n"
      "  vec2 w0 = f * (-0.5 + f * (1.0 - 0.5 * f)), w1 = 1.0 + f * f * (-2.5 + 1.5 * f), w2 = f * (0.5 + f * (2.0 - 1.5 * f)), w3 = f * f * (-0.5 + 0.5 * f);\\n"
      "  vec2 w12 = w1 + w2, a = (t1 - 1.0) / TexSize, b = (t1 + w2 / w12) / TexSize, c = (t1 + 2.0) / TexSize;\\n"
      "  float k0 = w12.x * w0.y, k1 = w0.x * w12.y, k2 = w12.x * w12.y, k3 = w3.x * w12.y, k4 = w12.x * w3.y;\\n"
      "  return (T(vec2(b.x, a.y)) * k0 + T(vec2(a.x, b.y)) * k1 + T(b) * k2 + T(vec2(c.x, b.y)) * k3 + T(vec2(b.x, c.y)) * k4) / (k0 + k1 + k2 + k3 + k4); }\\n"
      "void main(){ vec2 px = 1.0 / TexSize; vec3 c = Up > 1.02 ? cr(v) : T(v);\\n"
      "  vec3 n = T(v - vec2(0.0, px.y)), s = T(v + vec2(0.0, px.y)), e = T(v + vec2(px.x, 0.0)), w = T(v - vec2(px.x, 0.0));\\n"
      "  vec3 mn = min(min(min(n, s), min(e, w)), c), mx = max(max(max(n, s), max(e, w)), c);\\n"
      "  vec3 amp = sqrt(clamp(min(mn, 2.0 - mx) / max(mx, vec3(1e-4)), 0.0, 1.0)), k = -amp * mix(0.125, 0.2, Sharp);\\n"
      "  vec3 r = (c + k * (n + s + e + w)) / (1.0 + 4.0 * k);\\n"
      "  o = vec4(clamp(r, mn, mx), 1.0); }\\n#endif\\n")

# ---- shader + its program ----
rep('''      const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);''',
    '''      const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);
      // v235: the 3x HD picture is scaled to the screen's own pixels here (Catmull-Rom + contrast-adaptive sharpening).
      const UPSCALE = "''' + UP + '''";
      let upP = null; try { upP = prog(UPSCALE); } catch (e) { upP = null; (window.__wideLog || (window.__wideLog = [])).push("upscale: " + (e && e.message || e)); }''')

# ---- its 3x texture ----
rep('''      let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0, gT = [], gF = [], tT = [], tF = [], tw = 1, th = 1;''',
    '''      let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0, gT = [], gF = [], tT = [], tF = [], tw = 1, th = 1, upT = null, upF = null;''')
rep('''        for (const t of gT) gl.deleteTexture(t); for (const f of gF) gl.deleteFramebuffer(f); gT = []; gF = [];''',
    '''        if (upT) { gl.deleteTexture(upT); gl.deleteFramebuffer(upF); upT = upF = null; }
        if (upP) { upT = tex(w * 3, h * 3, "rgba", gl.LINEAR); upF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, upF); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, upT, 0);
          if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) { gl.deleteTexture(upT); gl.deleteFramebuffer(upF); upT = upF = null; (window.__wideLog || (window.__wideLog = [])).push("upscale: framebuffer"); } }
        for (const t of gT) gl.deleteTexture(t); for (const f of gF) gl.deleteFramebuffer(f); gT = []; gF = [];''')

# ---- final lighting pass goes into the 3x texture, then the upscale pass draws it on the canvas ----
rep('''        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;
        gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);
        if (lit) {''',
    '''        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;
        const up = !plain && !!upF && !window.__upOff;   // v235
        if (up) { gl.bindFramebuffer(gl.FRAMEBUFFER, upF); gl.viewport(0, 0, w * 3, h * 3); }
        else {
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);
        }
        if (lit) {''')
rep('''          gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, hiTex); gl.uniform1i(fu.Texture, 0);
          gl.uniformMatrix4fv(fu.MVPMatrix, false, MVP_FLIP);''',
    '''          gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, hiTex); gl.uniform1i(fu.Texture, 0);
          gl.uniformMatrix4fv(fu.MVPMatrix, false, up ? MVP : MVP_FLIP);''')
rep('''        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);
        }
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      };''',
    '''        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, up ? MVP : MVP_FLIP);
        }
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        if (up) {   // v235: 3x picture -> screen pixels, sharp
          for (let i = 0; i < 10; i++) gl.bindSampler(i, null);
          gl.bindFramebuffer(gl.FRAMEBUFFER, null);
          gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
          gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);
          const uu = upP.u; gl.useProgram(upP.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, upT);
          if (uu.Texture) gl.uniform1i(uu.Texture, 0); gl.uniformMatrix4fv(uu.MVPMatrix, false, MVP_FLIP);
          if (uu.TexSize) gl.uniform2f(uu.TexSize, w * 3, h * 3); if (uu.Up) gl.uniform1f(uu.Up, dest[2] / (w * 3));
          if (uu.Sharp) gl.uniform1f(uu.Sharp, typeof window.__sharpK === "number" ? window.__sharpK : 0.35);
          gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        }
      };''')

# ---- canvas at full screen resolution ----
rep('''const cap = window.__gfxLow && window.__gfxLow() ? 860 : 1280, k = Math.min(1, cap / Math.max(W, H));''',
    '''const cap = window.__gfxLow && window.__gfxLow() ? 860 : window.__fullRes ? 2880 : 1280, k = Math.min(1, cap / Math.max(W, H));''')
rep('''  window.__gfxLow = () => !!window.__gfxLowMem;''',
    '''  if (window.__fullRes === undefined) window.__fullRes = true;   // v235: HD picture at the screen's own resolution (the slow check may step down)
  window.__gfxLow = () => !!window.__gfxLowMem;''')

# ---- slow check: each step down is a trial ----
rep('''            this.slow = !this.plain && fps < 40 ? (this.slow || 0) + 1 : 0;
            if (this.slow >= 2 && window.__gfxLow && !window.__gfxLow()) { window.__gfxSet(true, true); this.slow = 0; (window.__wideLog || (window.__wideLog = [])).push("graphics low, fps " + fps.toFixed(1)); }
            else if (this.slow >= 2) { this.plain = true; this.fitDue = true; (window.__wideLog || (window.__wideLog = [])).push("sharp off, fps " + fps.toFixed(1)); }''',
    '''            // v235: a step down is a trial. Tiers: 0 full screen resolution, 1 3x canvas, 2 Low, 3 raw pixels. If drawing less
            // didn't make the game faster (the engine itself is the limit, e.g. Moria on an iPhone), the step is undone.
            const LG = window.__wideLog || (window.__wideLog = []);
            const setTier = (k) => { this.tier = k; window.__fullRes = k === 0; if (window.__gfxSet && (k >= 2) !== !!(window.__gfxLow && window.__gfxLow())) window.__gfxSet(k >= 2, true); this.plain = k >= 3; this.fitDue = true; };
            if (this.tier === undefined) this.tier = window.__fullRes ? 0 : 1;
            this.noStep = this.noStep || {};
            if (this.tryN !== undefined) {
              this.tryN++; this.trySum += fps;
              if (this.tryN >= 2) {
                const after = this.trySum / this.tryN;
                if (after < 40 && after < this.tryFps * 1.1) { this.noStep[this.tier - 1] = 1; setTier(this.tier - 1); LG.push("graphics step undone (" + this.tryFps.toFixed(1) + " -> " + after.toFixed(1) + "/s), tier " + this.tier); }
                else LG.push("graphics step kept (" + this.tryFps.toFixed(1) + " -> " + after.toFixed(1) + "/s), tier " + this.tier);
                this.tryN = undefined; this.slow = 0;
              }
            } else {
              this.slow = fps < 40 ? (this.slow || 0) + 1 : 0;
              if (this.slow >= 2 && this.tier < 3 && !this.noStep[this.tier]) { this.tryFps = fps; this.tryN = 0; this.trySum = 0; this.slow = 0; setTier(this.tier + 1); LG.push("graphics step down to tier " + this.tier + ", fps " + fps.toFixed(1)); }
            }''')
open(out, "w", encoding="utf-8").write(t)
print("ok", len(t))
