# Clean ground (Jordan, 2026-11-17: "Clean up particles on ground and overhaul shading and textures next ...
# Cluttered with leaves or rocks, I would like it look more modern and clean").
# Runs after shadows.py (needs its height map and tags). Our own effect over the game's picture, nothing from other games:
#  - A game-size "ground" pass smooths only the floor (the ground layer, not walls, trees, heroes, water or the HUD) with an
#    edge-keeping filter (Kuwahara): the busy specks of grit, pebbles and leaves merge into clean, even surfaces while
#    paving stones, paths and edges keep their shapes.
#  - Rain drops and other 1-pixel sprite specks are taken out of the picture (filled from the ground around them).
#  - The final pass draws the cleaned floor smoothly upscaled, and shades it with soft light from the same sun/moon that
#    casts the shadows, instead of the old pixel-sharp emboss that made every speck sparkle.
# Works in 1-player, P2 and online (same tags as the shadows). window.__gdOff = 1 turns it off, __gdDbg = 1 shows the mask.
# Usage: python3 ground.py in.html out.html   (in.html already patched by shadows.py)
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a)); s = s.replace(a, b)
J = lambda t: t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

GROUND = r'''#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
precision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture; uniform sampler2D Hm; uniform vec2 GPx; uniform float HudY;
float wet(vec3 c){ return smoothstep(0.13, 0.2, c.g - c.r) * smoothstep(0.13, 0.2, c.b - c.r) * (1.0 - smoothstep(0.06, 0.14, c.g - c.b)); }
float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
// ground pixel? (not scenery, not a sprite; rain specks count as ground so they get filled)
float gnd(ivec2 q){ float g = texelFetch(Hm, q, 0).g * 255.0; return g < 10.0 || (g > 30.0 && g < 50.0) ? 1.0 : 0.0; }
float spk(ivec2 q){ float g = texelFetch(Hm, q, 0).g * 255.0; return g > 30.0 && g < 50.0 ? 1.0 : 0.0; }
void main(){
  ivec2 ip = ivec2(floor(v / GPx)); ivec2 isz = ivec2(1.0 / GPx + 0.5);
  vec3 me = texelFetch(Texture, ip, 0).rgb;
  if (v.y > HudY || gnd(ip) < 0.5 || (wet(me) > 0.3 && spk(ip) < 0.5)) { o = vec4(me, 0.0); return; }   // not floor: unchanged (alpha 0)
  // Kuwahara, radius 2: of the four 3x3 corners around the pixel, take the calmest one's average (ground pixels only).
  vec3 best = me; float bv = 1e9;
  for (int qd = 0; qd < 4; qd++) {
    ivec2 d = ivec2(qd % 2 == 0 ? -1 : 1, qd < 2 ? -1 : 1);
    vec3 sm = vec3(0.0); vec3 sq = vec3(0.0); float n = 0.0;
    for (int j = 0; j < 3; j++) for (int i = 0; i < 3; i++) {
      ivec2 q = clamp(ip + ivec2(i, j) * d, ivec2(0), isz - 1);
      if (gnd(q) < 0.5 || spk(q) > 0.5) continue;
      vec3 c = texelFetch(Texture, q, 0).rgb; sm += c; sq += c * c; n += 1.0;
    }
    if (n < 3.0) continue;
    sm /= n; vec3 var = sq / n - sm * sm; float vv = var.r + var.g + var.b;
    if (vv < bv) { bv = vv; best = sm; }
  }
  // keep a little of the pixel's own value so stones keep their light/dark pattern, but none of a rain speck
  // keep some of the pixel's own value so stones keep their light/dark pattern (more on the decal layer: bodies, paths),
  // and keep dark outlines; none of a rain speck
  float g0 = texelFetch(Hm, ip, 0).g * 255.0; float keep = g0 > 2.0 && g0 < 10.0 ? 0.55 : 0.3;
  keep = max(keep, smoothstep(0.12, 0.3, luma(best) - luma(me)) * smoothstep(0.2, 0.08, luma(me)));
  vec3 cl = spk(ip) > 0.5 ? best : mix(best, me, keep);
  cl = mix(cl, vec3(luma(cl)), -0.08);   // a touch more colour, so cleaned ground doesn't look washed out
  o = vec4(clamp(cl, 0.0, 1.0), 1.0);
}
#endif
'''
rep("  const ALIVE_GLSL = ", "  const GROUND_GLSL = \"" + J(GROUND) + "\";\n  const ALIVE_GLSL = ")

# rain drops and other 1-pixel sprite specks: marked 40 in the height map (no shadow, filled by the ground pass)
rep("""          kk[y * w + x] = k;
        }""", """          kk[y * w + x] = k; { const t = y < yEnd ? u[b0 + (y + sy) * stride + x + sx] : 0; ob[y * w + x] = !(t >>> 31) ? 0 : ((t >>> 25) & 1) ? 1 : (t & 4095) >= 1536 ? 2 : (t & 4095) >= 512 && (t & 4095) < 1024 ? 3 : 0; }
        }""")
rep("const n = w * h; if (!hmB || hmB.length !== n * 2) { hmB = new Uint8Array(n * 2); kk = new Uint8Array(n); }",
    "const n = w * h; if (!hmB || hmB.length !== n * 2) { hmB = new Uint8Array(n * 2); kk = new Uint8Array(n); ob = new Uint8Array(n); }")
rep("""        return tall;
      };""", """        // 5. specks: sprite pixels 1 px wide with at most 6 rows (rain, drips, sparks on the floor)
        for (let x = 0; x < w; x++) {
          let y = 0;
          while (y < yEnd) {
            const i = y * w + x;
            if (ob[i] !== 1 || (x > 0 && ob[i - 1] === 1) || (x < w - 1 && ob[i + 1] === 1)) { y++; continue; }
            let e = y; while (e < yEnd && ob[e * w + x] === 1 && !(x > 0 && ob[e * w + x - 1] === 1) && !(x < w - 1 && ob[e * w + x + 1] === 1)) e++;
            const above = y > 0 && ob[(y - 1) * w + x] === 1, below = e < yEnd && ob[e * w + x] === 1;
            if (e - y <= 6 && !above && !below) for (let yy = y; yy < e; yy++) { const q = (yy * w + x) * 2; hmB[q] = 0; hmB[q + 1] = 40; }
            y = e;
          }
        }
        // 6. lone dots on the top text layer (rain splashes drawn there): 2 or fewer such pixels in their 3x3
        for (let y = 1; y < yEnd - 1; y++) for (let x = 1; x < w - 1; x++) {
          const o0 = ob[y * w + x], q0 = (y * w + x) * 2 + 1;
          if (o0 === 1 && hmB[q0] === 0) hmB[q0] = 20;        // see-through sprites, flames, spells: left alone
          if (o0 === 3 && hmB[q0] === 0) hmB[q0] = 5;         // decal layer (bodies, paths, rubble): cleaned more gently
          if (kk[y * w + x] === 1) {   // splash dots that land on the walk-behind layer
            let nk = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (kk[(y + dy) * w + x + dx] === 1) nk++;
            if (nk <= 3) { hmB[q0 - 1] = 0; hmB[q0] = 40; }
          }
          if (o0 !== 2) continue;
          let nb = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (ob[(y + dy) * w + x + dx] === 2) nb++;
          const q = (y * w + x) * 2; if (nb <= 5) { hmB[q] = 0; hmB[q + 1] = 40; } else if (hmB[q + 1] === 0) hmB[q + 1] = 20;   // 20: text/menus, left alone
        }
        return tall;
      };""")
rep("let shT = null, shF = null, hmT = null, hmB = null, kk = null, shOn = 0;",
    "let shT = null, shF = null, hmT = null, hmB = null, kk = null, ob = null, shOn = 0;\n"
    "      let gdP = null; try { if (glowP) gdP = prog(GROUND_GLSL); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push(\"ground: \" + (e && e.message || e)); }\n"
    "      let gdT = null, gdF = null, gdOn = 0, hmPre = 0;")
rep("        if (shT) { gl.deleteTexture(shT);",
    "        if (gdT) { gl.deleteTexture(gdT); gl.deleteFramebuffer(gdF); gdT = null; }\n"
    "        if (gdP) { gdT = tex(w, h, \"rgba\", gl.LINEAR); gdF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, gdF); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, gdT, 0); }\n"
    "        if (shT) { gl.deleteTexture(shT);")
# The ground pass runs on the game picture BEFORE Sharp HD, so the upscaler draws crisp edges of the cleaned floor.
rep("""        frame++;
        let srcTex = input;""", """        frame++;
        let srcTex = input; gdOn = 0; hmPre = 0;
        if (!plain && gdP && gdT && shP && hmT && !window.__gdOff && !window.__shOff && (cur.Clean || 0) > 0.01) {
          try {
            const tg = shadowTags();
            if (tg) {
              const hy = h > 100 ? 1 - 34 / h : 2;
              buildHm(tg[0], tg[1], heap, off, stride, sx, sy, w, h, h > 100 ? 34 : 0); hmPre = 1;
              gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, hmT); gl.bindSampler(1, null);
              gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RG, gl.UNSIGNED_BYTE, hmB);
              const du = gdP.u; gl.useProgram(gdP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, gdF); gl.viewport(0, 0, w, h);
              gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, input); gl.bindSampler(0, null); if (du.Texture) gl.uniform1i(du.Texture, 0);
              if (du.Hm) gl.uniform1i(du.Hm, 1);
              gl.uniformMatrix4fv(du.MVPMatrix, false, MVP); if (du.GPx) gl.uniform2f(du.GPx, 1 / w, 1 / h); if (du.HudY) gl.uniform1f(du.HudY, hy);
              gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); gdOn = 1; srcTex = gdT;
            }
          } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("ground: " + (e && e.message || e)); window.__gdOff = 1; }
        }""")
rep("buildHm(tg[0], tg[1], heap, off, stride, sx, sy, w, h, h > 100 ? 34 : 0);\n                gl.activeTexture",
    "if (!hmPre) buildHm(tg[0], tg[1], heap, off, stride, sx, sy, w, h, h > 100 ? 34 : 0);\n                gl.activeTexture")

# final pass: cleaned floor, smooth upscale, soft sun shading; the old pixel emboss and local contrast stay off the floor
rep("uniform sampler2D Shad; uniform float ShOn, ShDbg, Warm; uniform vec3 ShCol;",
    "uniform sampler2D Shad; uniform float ShOn, ShDbg, Warm; uniform vec3 ShCol; uniform sampler2D Gd; uniform float GdOn, GdDbg, Clean; uniform vec2 SunL;")
CLEAN = r'''  vec4 g = texture(Glow, v); vec3 c = c0;
  // ---- Clean ground (2026-11-17): the floor drawn from the cleaned game-size picture, smoothly upscaled, and shaded ----
  // ---- by soft light from the sun/moon side (SunL) instead of a pixel emboss. Edges against walls/heroes blend. ----
  float gm = 0.0;
  if (GdOn > 0.5 && v.y < HudY) {
    vec4 gd = textureLod(Gd, v, 0.0); gm = gd.a * Clean;
    if (gm > 0.002) {
      vec4 g1 = textureLod(Gd, v + vec2(GPx.x, 0.0), 0.0), g2 = textureLod(Gd, v - vec2(GPx.x, 0.0), 0.0), g3 = textureLod(Gd, v + vec2(0.0, GPx.y), 0.0), g4 = textureLod(Gd, v - vec2(0.0, GPx.y), 0.0);
      float ok = smoothstep(0.85, 1.0, min(min(g1.a, g2.a), min(g3.a, g4.a)));   // no slope at the floor's edges
      vec2 sl = vec2(luma(g1.rgb) - luma(g2.rgb), luma(g3.rgb) - luma(g4.rgb)) * ok;
      c *= mix(1.0, clamp(1.0 + 0.9 * dot(sl, SunL), 0.85, 1.15), clamp(gm, 0.0, 1.0)); c0 = c;
    }
  }
'''
rep(J("  vec4 g = texture(Glow, v); vec3 c = c0;\n"), J(CLEAN))
rep(J("  c *= clamp(1.0 - Relief * (1.0 - m) * (lx * 0.7 + ly), 0.75, 1.3);"), J("  c *= clamp(1.0 - Relief * (1.0 - m) * (1.0 - gm) * (lx * 0.7 + ly), 0.75, 1.3);"))
rep(J("  float k = clamp(1.0 + Clarity * (l - g.a) * 2.2, 0.55, 1.6);"), J("  float k = clamp(1.0 + Clarity * (1.0 - 0.75 * gm) * (l - g.a) * 2.2, 0.55, 1.6);"))
rep(J("  if (ShDbg > 0.5) {"), J("  if (GdDbg > 0.5) o = vec4(mix(o.rgb, vec3(0.0, 1.0, 0.3), gm * 0.5), 1.0);\n  if (ShDbg > 0.5) {"))

rep("          if (fu.Warm) gl.uniform1f(fu.Warm, cur.Warm || 0); if (fu.ShCol) gl.uniform3fv(fu.ShCol, cur.ShCol);",
    "          if (fu.Warm) gl.uniform1f(fu.Warm, cur.Warm || 0); if (fu.ShCol) gl.uniform3fv(fu.ShCol, cur.ShCol);\n"
    "          gl.activeTexture(gl.TEXTURE6); gl.bindTexture(gl.TEXTURE_2D, gdT); gl.bindSampler(6, linS); if (fu.Gd) gl.uniform1i(fu.Gd, 6);\n"
    "          if (fu.GdOn) gl.uniform1f(fu.GdOn, gdOn); if (fu.GdDbg) gl.uniform1f(fu.GdDbg, window.__gdDbg && gdOn ? 1 : 0); if (fu.Clean) gl.uniform1f(fu.Clean, cur.Clean || 0);\n"
    "          if (fu.SunL) { const dx = cur.SunDX || 0, dy = 1 + (cur.SunDY || 0), l = Math.hypot(dx, dy) || 1; gl.uniform2f(fu.SunL, -dx / l, -dy / l); }")

# looks: on everywhere in levels, off in menus
rep("SunDX: 0.2, SunDY: 0.3, Warm: 0.0, ShCol: [0.4, 0.45, 0.64] };", "SunDX: 0.2, SunDY: 0.3, Warm: 0.0, ShCol: [0.4, 0.45, 0.64], Clean: 0.9 };")
rep("menu: L({ SunSh: 0.0,", "menu: L({ Clean: 0.0, SunSh: 0.0,")
open(out, "w").write(s); print("ok ground")
