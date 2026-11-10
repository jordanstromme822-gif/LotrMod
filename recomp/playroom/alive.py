# Living light (Jordan, 2026-11-10): "fire to bounce and spark, trees to feel alive and have depth, shadows natural,
# rounded where they should be round and sharp where it needs to be sharp". Our own effects, drawn by the page's
# lighting pass over the game's own picture (nothing from other games).
#
# New game-size pass (ALIVE) after the glow passes writes one map per picture:
#   R = tree canopy (green, leafy texture; flat grass and water score low)   G = flame pixels (bright, warm, brighter than around)
#   B = shadow softening factor / 2 (same-colour neighbours across a wide light step; 0.5 = no change)
#   A = soft cast shadow from canopy up-left of the pixel (sun from the top left)
# The final pass then: sways canopy texture and outline in gusty wind, adds heat shimmer above flames, lights tree rims
# and shades their undersides, moves dappled sun over leaves and through their shadows, softens shadow edges into a
# penumbra (colour edges stay sharp), makes each flame and each light pool flicker on its own, raises flickering
# tongues above flames and sends sparks up from them.
# Look keys FireK / TreeK / ShadeK (1 in play, 0 on menus). Tests: window.__aliveDbg = 1 shows the map; __aliveOff = 1.
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
J = lambda t: t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

def lod(t):
    # texture(S, uv) -> textureLod(S, uv, 0.0): fetches inside branches then really get skipped (no implicit derivatives),
    # which matters on phones and software GL. The maps have no mipmaps, so the result is the same.
    out, i = "", 0
    while True:
        j = t.find("texture(", i)
        if j < 0: return out + t[i:]
        depth, k = 0, j + 7
        while True:
            ch = t[k]
            if ch == "(": depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0: break
            k += 1
        out += t[i:j] + "textureLod(" + t[j + 8:k] + ", 0.0)"; i = k + 1

# ---------- 1. the game-size map pass ----------
ALIVE = r'''#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
precision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture; uniform sampler2D Glow; uniform vec2 GPx; uniform float HudY;
float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
float fol(vec3 c){ return smoothstep(0.02, 0.07, c.g - c.r) * smoothstep(0.03, 0.09, c.g - c.b) * smoothstep(0.1, 0.2, c.g); }
// Leaves: green with a big light/dark range close by (bright leaf clumps with near-black gaps between them).
// Grass and moss are textured too but their range is much smaller (measured on Fangorn: leaves 0.6-0.8, grass 0.35-0.45).
float canopy(vec2 uv){
  vec3 c = texture(Texture, uv).rgb; float fs = fol(c), l = luma(c), hi = l, lo = l;
  for (int i = 0; i < 8; i++) {
    float a = float(i) * 0.7854 + (i % 2 == 0 ? 0.0 : 0.2); float r = i % 2 == 0 ? 1.5 : 2.6;
    vec3 n = texture(Texture, uv + vec2(cos(a), sin(a)) * r * GPx).rgb; float ln = luma(n); hi = max(hi, ln); lo = min(lo, ln); fs += fol(n) + (ln < 0.14 ? 0.7 : 0.0);
  }
  return smoothstep(0.46, 0.62, hi - lo) * smoothstep(0.35, 0.6, fs / 9.0) * max(smoothstep(0.02, 0.06, fol(c)), 1.0 - smoothstep(0.12, 0.2, l));   // dark gaps between clumps count too
}
float flame(vec2 uv, float wide){
  vec3 c = texture(Texture, uv).rgb; float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));
  float core = smoothstep(0.62, 0.82, c.r) * smoothstep(0.45, 0.62, c.g) * smoothstep(0.3, 0.5, c.r - c.b)   // yellow-hot (red lava cracks stay calm)
    * smoothstep(0.35, 0.6, (mx - mn) / max(mx, 0.001)) * smoothstep(0.12, 0.26, luma(c) - wide);
  if (core < 0.01) return 0.0;
  // Real flames have orange in them; yellow-green leaf highlights (same yellow as a flame core) have green around them.
  float org = smoothstep(0.1, 0.22, c.r - c.g), gr = 0.0;
  for (int i = 0; i < 6; i++) {
    float a = float(i) * 1.0472; vec3 n = texture(Texture, uv + vec2(cos(a), sin(a)) * (i % 2 == 0 ? 1.5 : 2.5) * GPx).rgb;
    org = max(org, smoothstep(0.1, 0.22, n.r - n.g) * step(0.45, n.r)); gr += smoothstep(0.02, 0.08, n.g - n.r);
  }
  return core * org * (1.0 - smoothstep(1.0, 2.5, gr));
}
void main(){
  if (v.y > HudY) { o = vec4(0.0, 0.0, 0.5, 0.0); return; }
  vec4 g = texture(Glow, v); vec3 c = texture(Texture, v).rgb; float l0 = luma(c) + 0.03; vec3 ch0 = c / l0;
  float can = canopy(v), nb = 0.0;
  for (int i = 0; i < 4; i++) nb = max(nb, canopy(v + vec2(i < 2 ? 1.6 : -1.6, i % 2 == 0 ? 1.6 : -1.6) * GPx));
  float fz = flame(v, g.a);
  // Shadow edges: average light ratio of same-colour neighbours, only where the wide light field steps.
  float acc = 1.0, ws = 1.0;
  for (int i = 0; i < 12; i++) {
    float a = float(i) * 0.5236 + (i < 6 ? 0.0 : 0.26); float r = i % 2 == 0 ? 1.4 : 2.8;
    vec3 n = texture(Texture, v + vec2(cos(a), sin(a)) * r * GPx).rgb; float ln = luma(n) + 0.03;
    float sim = 1.0 - smoothstep(0.12, 0.32, length(n / ln - ch0)); float wt = sim * (r < 2.0 ? 1.0 : 0.55);
    acc += wt * clamp(ln / l0, 0.4, 2.2); ws += wt;
  }
  float gx = texture(Glow, v + vec2(2.5, 0.0) * GPx).a - texture(Glow, v - vec2(2.5, 0.0) * GPx).a;
  float gy = texture(Glow, v + vec2(0.0, 2.5) * GPx).a - texture(Glow, v - vec2(0.0, 2.5) * GPx).a;
  float S = mix(1.0, acc / ws, smoothstep(0.06, 0.14, length(vec2(gx, gy))) * (1.0 - can));
  // Soft cast shadow: canopy up and to the left (sun from the top left), a few spread taps for a soft edge.
  float cs = 0.0, cw = 0.0;
  for (int k = 0; k < 4; k++) {
    float t = 3.0 + float(k) * 2.4; vec2 off = vec2(-1.0, -0.75) * t + vec2(k % 2 == 0 ? 1.2 : -1.2, k % 3 == 0 ? -0.8 : 0.8);
    float w = 1.0 - float(k) / 5.0; cs += canopy(v + off * GPx) * w; cw += w;
  }
  o = vec4(max(can, nb * 0.6), fz, clamp(S * 0.5, 0.0, 1.0), cs / cw * (1.0 - can));
}
#endif
'''
rep("  function makeSharpHD(gl) {", "  const ALIVE_GLSL = \"" + J(ALIVE) + "\";\n  function makeSharpHD(gl) {")

# ---------- 2. final pass ----------
rep("uniform vec2 AuraP; uniform float AuraK;",
    "uniform vec2 AuraP; uniform float AuraK; uniform sampler2D Alive; uniform float FireK, TreeK, ShadeK, AliveOn, AliveDbg;")

SWAY = r'''vec2 p = v / GPx; vec4 A0 = AliveOn > 0.5 ? texture(Alive, v) : vec4(0.0, 0.0, 0.5, 0.0);
  vec3 c0 = texture(Texture, v).rgb; float warmNear = 0.0;
  // ---- Living trees (2026-11-10): canopies sway in gusts of wind (texture and outline), leaves flutter ----
  // ---- and the air shimmers above flames. ----
  if (AliveOn > 0.5) {
    vec3 Tw = texture(Torch, v + vec2(0.0, 8.0) * GPx).rgb; warmNear = step(0.0006, Tw.r - Tw.b * 0.85) * step(0.001, FireK);   // any flame within ~30 px?
  }
  if (AliveOn > 0.5 && (A0.r > 0.002 || warmNear > 0.5)) {
    float gust = 0.45 + 0.55 * smoothstep(-0.6, 1.0, sin(Time * 0.42 + p.x * 0.012 - p.y * 0.005));
    float wv = sin(Time * 1.7 + p.x * 0.04 + p.y * 0.018) * 0.65 + (vn(p * 0.07 + vec2(Time * 0.5, Time * 0.13)) - 0.5) * 1.1;
    float flut = vn(p * 0.2 + vec2(Time * 1.1, Time * 1.7)) - 0.5;   // leaf clumps flutter together, not pixel by pixel
    vec2 tw = vec2(wv * gust * 0.95 + flut * 0.4, wv * gust * 0.22 + flut * 0.3) * TreeK * step(0.002, A0.r);
    float hb = 0.0; if (warmNear > 0.5) for (int k = 1; k <= 4; k++) hb += texture(Alive, v + vec2(0.0, float(k) * 2.4) * GPx).g; hb = clamp(hb * 0.35, 0.0, 1.0) * FireK * (1.0 - A0.g);
    vec2 hw = vec2(sin(p.y * 1.25 + Time * 10.5) * 0.4, -0.3 - 0.3 * sin(Time * 7.0 + p.x)) * hb;
    vec2 sv = v + (tw + hw) * GPx;
    float k = max(A0.r * step(0.001, TreeK), hb);
    if (k > 0.01) c0 = mix(c0, texture(Texture, sv).rgb, clamp(k * 1.6, 0.0, 1.0));
  }
  vec4 g = texture(Glow, v); vec3 c = c0;'''
rep(J("vec3 c0 = texture(Texture, v).rgb; vec4 g = texture(Glow, v); vec3 c = c0;"), J(lod(SWAY).replace("textureLod(Texture, v, 0.0).rgb; float warmNear", "texture(Texture, v).rgb; float warmNear").replace("vec4 g = textureLod(Glow, v, 0.0)", "vec4 g = texture(Glow, v)")))

DEPTH = r'''
  // ---- Tree depth (2026-11-10): sunlit rims top-left, cool shaded undersides, dappled sun moving over the leaves ----
  // ---- and through their soft shadows on the ground. Shadow edges get a penumbra; colour edges stay sharp. ----
  float dap = 0.0;
  if (AliveOn > 0.5 && A0.r + A0.a > 0.002) dap = smoothstep(0.56, 0.86, vn(p * 0.13 + vec2(Time * 0.21, Time * 0.06)) * 0.75 + vn(p * 0.31 - vec2(Time * 0.35, 0.0)) * 0.25);
  if (AliveOn > 0.5 && TreeK > 0.001 && A0.r + A0.a > 0.002) {
    float day = 1.0 - Night * 0.8;
    float ul = texture(Alive, v - vec2(2.5, 2.2) * GPx).r, dr = texture(Alive, v + vec2(2.5, 2.2) * GPx).r;
    float rim = A0.r * (1.0 - ul), under = A0.r * (1.0 - dr) * (1.0 - rim);
    c *= 1.0 + TreeK * (rim * 0.3 * day - under * 0.22 + A0.r * dap * 0.16 * day);
    c += TreeK * rim * vec3(0.035, 0.03, -0.01) * day;
    c = mix(c, c * vec3(0.84, 0.92, 1.06), TreeK * under * 0.55);
    float sh = A0.a * TreeK * (1.0 - 0.5 * dap * day);
    c = mix(c, c * vec3(0.6, 0.65, 0.78), sh * 0.75);
  }
  if (AliveOn > 0.5 && ShadeK > 0.001) {
    float S = A0.b * 2.0; c *= mix(1.0, S, ShadeK);
    float sd = smoothstep(0.0, 0.25, g.a - luma(c)) * ShadeK;   // darker than its surroundings: lean cool, not grey
    c += vec3(-0.012, -0.004, 0.022) * sd * keepBlack;
  }
'''
rep(J("  c = mix(c, FogCol, Fog * (1.0 - 0.6 * l) * keepBlack);\n"), J("  c = mix(c, FogCol, Fog * (1.0 - 0.6 * l) * keepBlack);\n" + lod(DEPTH)))

# Light pools: each one flickers on its own and the light wavers a little, like a real flame.
rep(J("    vec3 T = texture(Torch, v).rgb;"),
    J("    vec3 T = texture(Torch, v + vec2(sin(Time * 5.1 + v.y * 19.0), cos(Time * 4.3 + v.x * 17.0)) * GPx * 2.2 * FireK).rgb;"))
rep(J("    float fl = 0.86 + 0.08 * sin(Time * 8.3 + v.x * 9.0) + 0.06 * sin(Time * 21.7 + v.y * 13.0);"),
    J("    float fl = mix(0.86 + 0.08 * sin(Time * 8.3 + v.x * 9.0) + 0.06 * sin(Time * 21.7 + v.y * 13.0),\n"
      "                   0.7 + 0.32 * vn(v * Aspect * 6.0 + vec2(Time * 4.6, Time * 1.9)) + 0.12 * vn(v * Aspect * 14.0 - vec2(Time * 11.0, Time * 7.0)), FireK);   // every pool its own flicker"))

FIRE = r'''  // ---- Living fire (2026-11-10): flames flicker and change colour, flickering tongues lick up above them and ----
  // ---- sparks rise, drift and wink out. Brighter at night. Screen blend, so it only adds light. ----
  if (AliveOn > 0.5 && FireK > 0.001 && (A0.g > 0.002 || warmNear > 0.5)) {
    float fn = vn(p * 0.22 + vec2(0.0, Time * 7.0)), fn2 = vn(p * 0.55 + vec2(Time * 3.0, Time * 13.0));
    c = mix(c, c * (0.82 + 0.42 * fn) + vec3(0.1, 0.05, 0.0) * fn2, A0.g * FireK);
    vec3 add = vec3(0.0); float tg = 0.0;
    if (warmNear > 0.5) {
    for (int k = 1; k <= 5; k++) { float fk = float(k); tg += texture(Alive, v + vec2((fn - 0.5) * 0.6 * fk, fk * 2.0) * GPx).g * (1.0 - fk / 6.5); }
    tg *= 0.6 * (1.0 - A0.g) * smoothstep(0.3, 0.72, vn(vec2(p.x * 0.4, p.y * 0.24 + Time * 5.5)));
    add += mix(vec3(1.0, 0.32, 0.05), vec3(1.0, 0.78, 0.32), clamp(tg * 1.6, 0.0, 1.0)) * tg;
    // Sparks: a stream of particles rises everywhere, but a particle only glows once it has passed through a flame,
    // and fades as it climbs away from it (up to about 22 game pixels), drifting sideways as it goes.
    for (int k = 0; k < 2; k++) {
      float cs = k == 0 ? 4.0 : 6.0, sp = k == 0 ? 19.0 : 13.0;
      vec2 q = vec2(p.x / cs, (p.y + Time * sp) / cs);
      vec2 ci = floor(q), cf = fract(q); float h = hsh(ci + float(k) * 31.0);
      if (h > 0.5) {
        float sway = sin(Time * 2.3 + h * 40.0 + q.y * 1.3) * 0.3;
        vec2 pp = vec2(0.5 + sway, hsh(ci + 5.3) * 0.6 + 0.2);
        vec2 dd = (cf - pp) * cs * vec2(1.0, 0.55);
        float sh = exp(-dot(dd, dd) / 0.5); if (sh < 0.02) continue;
        float src = 0.0;
        for (int j = 1; j <= 6; j++) { float fj = float(j); src = max(src, texture(Alive, v + vec2(-sway * cs * fj * 0.12, fj * 3.6) * GPx).g * (1.0 - fj / 7.5)); }
        float tw = 0.6 + 0.4 * sin(Time * 23.0 + h * 90.0);
        add += vec3(1.0, 0.62 + 0.3 * fract(h * 7.0), 0.25) * sh * tw * smoothstep(0.05, 0.4, src) * 1.8;
      }
    }
    }
    add *= FireK * mix(0.75, 1.05, Night);
    c = 1.0 - (1.0 - clamp(c, 0.0, 1.0)) * (1.0 - clamp(add, 0.0, 1.0));
  }
'''
rep(J("  // ---- Gandalf's aura"), J(lod(FIRE)) + J("  // ---- Gandalf's aura"))
rep(J("  o = vec4(clamp(mix(c0, c, Amount), 0.0, 1.0), 1.0);"),
    J("  o = vec4(clamp(mix(c0, c, Amount), 0.0, 1.0), 1.0);\n  if (AliveDbg > 0.5) o = vec4(A0.r, A0.g + A0.a, abs(A0.b * 2.0 - 1.0) * 3.0, 1.0);"))

# ---------- 3. looks: on while playing, off on menus ----------
rep("AO: 0.0, Ash: 0.0 };", "AO: 0.0, Ash: 0.0, FireK: 1.0, TreeK: 1.0, ShadeK: 1.0 };")
rep("menu: L({ Water: 0.0,", "menu: L({ FireK: 0.0, TreeK: 0.0, ShadeK: 0.0, Water: 0.0,")

# ---------- 4. render ----------
rep("catch (e) { glowP = null;", "catch (e) { glowP = null;")   # (anchor check only)
rep("      const cur = JSON.parse(JSON.stringify(LIGHT_LOOKS.looks.menu));",
    "      let aliveP = null; try { if (glowP) aliveP = prog(ALIVE_GLSL); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push(\"alive: \" + (e && e.message || e)); }\n"
    "      let aT = null, aF = null;\n"
    "      const cur = JSON.parse(JSON.stringify(LIGHT_LOOKS.looks.menu));")
rep("        tw = Math.max(1, Math.ceil(w / 8));",
    "        if (aT) { gl.deleteTexture(aT); gl.deleteFramebuffer(aF); aT = null; }\n"
    "        if (aliveP) { aT = tex(w, h, \"rgba\", gl.LINEAR); aF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, aF); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, aT, 0); }\n"
    "        tw = Math.max(1, Math.ceil(w / 8));")
rep("if (cur.Night > 0.01 || cur.TorchK > 0.01) {", "if (cur.Night > 0.01 || cur.TorchK > 0.01 || cur.FireK > 0.01) {")
# the map pass runs right after the light map (it needs the glow's wide luma in gT[1])
rep("""              gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            }
          }
          gl.bindSampler(0, null);
        }""", """              gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            }
          }
          if (aliveP && aT && !window.__aliveOff && (cur.FireK > 0.01 || cur.TreeK > 0.01 || cur.ShadeK > 0.01)) {
            const au = aliveP.u; gl.useProgram(aliveP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, aF); gl.viewport(0, 0, w, h);
            gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, gT[1]); gl.bindSampler(1, linS); if (au.Glow) gl.uniform1i(au.Glow, 1);
            gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, outs[0]); gl.bindSampler(0, linS); if (au.Texture) gl.uniform1i(au.Texture, 0);
            gl.uniformMatrix4fv(au.MVPMatrix, false, MVP); if (au.GPx) gl.uniform2f(au.GPx, 1 / w, 1 / h); if (au.HudY) gl.uniform1f(au.HudY, hudY);
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); gl.bindSampler(1, null); aliveOn = 1;
          } else aliveOn = 0;
          gl.bindSampler(0, null);
        }""")
rep("        const hudY = h > 100 ? 1 - 34 / h : 2;\n        if (lit) {", "        const hudY = h > 100 ? 1 - 34 / h : 2; let aliveOn = 0;\n        if (lit) {")
rep("gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, tT[0]);",
    "for (const k of [\"FireK\", \"TreeK\", \"ShadeK\"]) if (fu[k]) gl.uniform1f(fu[k], cur[k] || 0);\n"
    "          if (fu.AliveOn) gl.uniform1f(fu.AliveOn, aliveOn); if (fu.AliveDbg) gl.uniform1f(fu.AliveDbg, window.__aliveDbg ? 1 : 0);\n"
    "          gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, aT); gl.bindSampler(4, linS); if (fu.Alive) gl.uniform1i(fu.Alive, 4);\n"
    "          gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, tT[0]);")
open(out, "w").write(s); print("patched")
