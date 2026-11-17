# Shadow overhaul (Jordan, 2026-11-17: "Have we did any major work to shadows yet?" -> yes, a major one).
# Real cast shadows, drawn by the page's lighting pass over the game's own picture (our own effect, nothing from other games):
#  - Every hero, enemy and item casts a shadow from its own outline, and trees, cliffs, pillars and rocks cast theirs too.
#    The engine tags every pixel with the 8x8 tile that drew it (skin hook, rotk_skin_slot): sprite pixels have bit 25, and
#    the game always puts the "tall" scenery you can walk behind (tree crowns, cliffs, pillars, rock walls) on BG2, whose
#    tiles sit in character block 2 (tile slots 1024-1535; checked on 11 levels with the BG registers). The page builds a
#    height map from that: each tall pixel's height above its foot (the bottom of its run in the column).
#  - A game-size shadow pass projects every tall pixel onto the ground along the light direction (billboard shadows, like
#    HD-2D games do): sharp near the feet, softer further out, plus a soft contact shadow where things touch the ground.
#    Characters walking under a tree get the tree's shade.
#  - The sun moves with the day/night clock (play time): long shadows to the left in the morning, short at midday, long to
#    the right in the evening, with warm low sun at both ends. At night the moon casts faint cool shadows, and inside a
#    torch or fire's light pool shadows point away from that light. Caves and halls: torch shadows only; Mordor's hazy sky
#    gives faint ones.
# Works the same in 1-player, P2 and online (all use the one engine's tags of the shown game). Replaces Living light's old
# fixed tree-canopy shadow when tags are there. Tests: window.__shTagsDbg = Uint32Array of tags (bench), __shDbg = 1 shows
# the shadow map, __shOff = 1 turns it off.
# Usage: python3 shadows.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a)); s = s.replace(a, b)
J = lambda t: t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

# ---------- 1. the shadow pass (game size) ----------
SHADOW = r'''#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
precision highp float; in vec2 v; out vec4 o; uniform sampler2D Hm; uniform sampler2D Torch; uniform vec2 GPx, SunD;
uniform float SunK, TorchSh, TorchK, HudY;
// Hm: R = run length (1 = the foot pixel, height above the foot = R - 1), G = kind (100 = BG2 scenery, 200 = sprite)
vec2 hm(ivec2 q){ vec2 t = texelFetch(Hm, q, 0).rg * 255.0; return t; }
float tl(vec2 uv){ vec3 T = texture(Torch, uv).rgb; return max(T.r, max(T.g, T.b)); }
void main(){
  if (v.y > HudY) { o = vec4(0.0); return; }
  vec2 sz = 1.0 / GPx; ivec2 ip = ivec2(floor(v * sz)); ivec2 isz = ivec2(sz);
  vec2 me = hm(ip); float kind = me.g > 150.0 ? 2.0 : me.g > 50.0 ? 1.0 : 0.0;
  if (kind == 1.0) { o = vec4(0.0); return; }   // tall scenery doesn't shade itself
  // Sprites take shade where their feet stand (only from scenery, below); the ground takes it where it is.
  vec2 P = vec2(ip) + 0.5; if (kind == 2.0) P.y += me.r - 1.0;
  // Light direction here: the sun/moon, or away from the brightest nearby light pool.
  vec2 uv = P * GPx; float lt = tl(uv);
  vec2 gr = vec2(tl(uv + vec2(6.0, 0.0) * GPx) - tl(uv - vec2(6.0, 0.0) * GPx), tl(uv + vec2(0.0, 6.0) * GPx) - tl(uv - vec2(0.0, 6.0) * GPx));
  float wt = TorchSh * TorchK * (1.0 - exp(-max(lt - 0.004, 0.0) * 200.0)) * smoothstep(0.00004, 0.0004, length(gr));
  vec2 Dt = length(gr) > 1e-6 ? -normalize(gr) * vec2(1.35, 0.8) : vec2(0.0);
  float ws = SunK * (1.0 - 0.85 * wt); vec2 D = (SunD * ws + Dt * wt * 1.5) / max(ws + wt * 1.5, 1e-4); float k = clamp(max(ws, wt * 0.9), 0.0, 1.0);
  float sh = 0.0, hs = 0.0;
  if (k > 0.01) {
    // March back along the light: the caster pixel S whose foot + D * height lands here, for heights 0..62.
    float stp = 1.3 / max(1.0, max(abs(D.x), 1.0 + D.y) * 0.85);
    for (int i = 0; i < 48; i++) {
      float hh = float(i) * stp;
      vec2 S = P - vec2(D.x * hh, hh + D.y * hh); ivec2 iS = ivec2(floor(S));
      if (iS.x < 0 || iS.y < 0 || iS.x >= isz.x || iS.y >= isz.y) continue;
      vec2 q = hm(iS); if (q.r < 0.5) continue;
      if (q.g > 110.0 && q.g < 130.0) continue;   // cut wall/roof tops (see buildHm)
      float qk = q.g > 150.0 ? 2.0 : 1.0; if (kind == 2.0 && qk == 2.0) continue;   // sprites don't shade each other's bodies
      float m = 1.0 - smoothstep(stp * 0.6 + 0.6, stp * 0.6 + 2.0, abs(q.r - 1.0 - hh));
      if (m > sh) { sh = m; hs = hh; }
    }
    sh *= k;
  }
  // Contact shadow: feet (run starts) close by, in a flat ellipse. Light-independent, so it works at night and indoors.
  float ao = 0.0;
  if (kind == 0.0) {
    for (int i = 0; i < 12; i++) {
      float a = float(i) * 0.5236 + (i % 2 == 0 ? 0.0 : 0.26); float r = i < 6 ? 2.2 : 4.5;
      ivec2 q = ip + ivec2(floor(vec2(cos(a) * r * 1.6, sin(a) * r * 0.7 - 1.0) + 0.5));
      if (q.x < 0 || q.y < 0 || q.x >= isz.x || q.y >= isz.y) continue;
      vec2 f = hm(q); ao += (f.r > 0.5 && f.r < 3.5 && (f.g < 110.0 || f.g > 130.0) ? 1.0 : 0.0) * (i < 6 ? 0.2 : 0.11);
    }
  }
  o = vec4(clamp(sh, 0.0, 1.0), clamp(hs / 64.0, 0.0, 1.0), clamp(ao, 0.0, 1.0), kind * 0.5);
}
#endif
'''
rep("  const ALIVE_GLSL = ", "  const SHADOW_GLSL = \"" + J(SHADOW) + "\";\n  const ALIVE_GLSL = ")

# ---------- 2. final pass: apply it ----------
rep("uniform vec2 AuraP; uniform float AuraK;",
    "uniform vec2 AuraP; uniform float AuraK; uniform sampler2D Shad; uniform float ShOn, ShDbg, Warm; uniform vec3 ShCol;")
rep("float sh = A0.a * TreeK * (1.0 - 0.5 * dap * day);", "float sh = A0.a * TreeK * (1.0 - 0.3 * ShOn) * (1.0 - 0.5 * dap * day);")
# Living light's leafy-canopy shadow (bushes and trees drawn on the ground layer) now falls along the same sun direction.
rep("uniform sampler2D Glow; uniform vec2 GPx; uniform float HudY;", "uniform sampler2D Glow; uniform vec2 GPx; uniform float HudY; uniform vec2 SunD;")
rep("vec2 off = vec2(-1.0, -0.75) * t + vec2(", "vec2 off = -vec2(SunD.x, SunD.y + 0.45) * (0.75 + 0.35 * length(SunD)) * t + vec2(")
rep("if (au.HudY) gl.uniform1f(au.HudY, hudY);", "if (au.HudY) gl.uniform1f(au.HudY, hudY); if (au.SunD) gl.uniform2f(au.SunD, cur.SunDX, cur.SunDY);")
# sunlit glow doesn't shine inside a shadow
# a light pool doesn't light what is in its own shadow (torch shadows read clearly at night)
rep("lt = ((1.0 - exp(-max(tm - 0.005, 0.0) * 90.0)) * 1.6) * TorchK * fl;", "lt = ((1.0 - exp(-max(tm - 0.005, 0.0) * 90.0)) * 1.6) * TorchK * fl * (1.0 - 0.8 * shAmt);")
rep(J("  vec3 gw = g.rgb * GlowK * GlowTint;"), J("  vec3 gw = g.rgb * GlowK * GlowTint * (1.0 - 0.8 * shAmt);"))
APPLY = r'''  // ---- Cast shadows (2026-11-17): heroes, enemies, trees, cliffs and pillars cast shadows along the light; soft further ----
  // ---- from the caster, sharp at the feet; cool blue-violet, not grey. Low sun warms the lit ground. ----
  float shAmt = 0.0;
  if (ShOn > 0.5 && v.y < HudY) {
    vec4 s0 = textureLod(Shad, v, 0.0);
    float rr = 0.6 + s0.g * 4.0;   // penumbra grows with the caster's height
    float sb = s0.r * 0.4 + (textureLod(Shad, v + vec2(rr, 0.35 * rr) * GPx, 0.0).r + textureLod(Shad, v - vec2(rr, 0.35 * rr) * GPx, 0.0).r
      + textureLod(Shad, v + vec2(-0.35 * rr, rr) * GPx, 0.0).r + textureLod(Shad, v + vec2(0.35 * rr, -rr) * GPx, 0.0).r) * 0.15;
    float ao = s0.b * (1.0 - 0.5 * sb);
    c = mix(c, c * ShCol, clamp(sb, 0.0, 1.0)); shAmt = clamp(sb + ao * 0.5, 0.0, 1.0);
    c *= 1.0 - 0.38 * ao;
    c *= 1.0 + Warm * (1.0 - sb) * vec3(0.07, 0.025, -0.05);
  }
'''
rep(J("  // ---- Moods (Jordan, 2026-11-10"), J(APPLY) + J("  // ---- Moods (Jordan, 2026-11-10"))
rep(J("  if (AliveDbg > 0.5) o = "), J("  if (ShDbg > 0.5) { vec4 s0 = textureLod(Shad, v, 0.0); o = vec4(s0.r, s0.b, s0.a, 1.0); }\n  if (AliveDbg > 0.5) o = "))

# ---------- 3. looks: shadow strength, and the sun moving with the day ----------
rep("FireK: 1.0, TreeK: 1.0, ShadeK: 1.0 };", "FireK: 1.0, TreeK: 1.0, ShadeK: 1.0, SunSh: 0.85, TorchSh: 1.0, SunDX: 0.2, SunDY: 0.3, Warm: 0.0, ShCol: [0.4, 0.45, 0.64] };")
rep("menu: L({ FireK: 0.0,", "menu: L({ SunSh: 0.0, TorchSh: 0.0, FireK: 0.0,")
for g, k in (("Lava", 0.3), ("Wasteland", 0.3), ("Mordor", 0.3), ('"Dwarf halls"', 0.0), ("Caves", 0.0)):
    rep("      %s: L({ Night:" % g, "      %s: L({ SunSh: %s, Night:" % (g, k))
rep("const NIGHT = { Night: 0.9,", "const NIGHT = { SunSh: 0.4, ShCol: [0.36, 0.42, 0.62], Night: 0.9,")
rep('''      const k = nightness(); if (k <= 0) return day;
      return blend(day, g === "Helm's Deep" ? looks["Helm's Deep"] : NIGHT, k);''',
'''      const k = nightness(); const lk = k <= 0 ? day : blend(day, g === "Helm's Deep" ? looks["Helm's Deep"] : NIGHT, k);
      return Object.assign({}, lk, sunNow(k));''')
rep("    const cycled = (n) => {", '''    // The sun follows the clock (2026-11-17): shadow direction per unit of height. Morning: long, to the left;
    // midday: short, down and a little right (the art's own top-left light); evening: long, to the right. The moon
    // crosses the night sky the same way. Low sun warms the lit ground (Warm).
    const sunNow = (k) => {
      const t = ((typeof window.__sunT === "number" ? window.__sunT : playT) + 15) % 480, day = t < 255, u = day ? Math.min(1, t / 255) : Math.min(1, (t - 240) / 240);
      const s = Math.sin(Math.PI * u), dx = 0.2 - 1.15 * Math.cos(Math.PI * u), dy = 0.3 + 0.12 * (1 - s);
      return { SunDX: dx, SunDY: dy, Warm: day ? (1 - s) * (1 - s) * (1 - k) * 0.9 : 0 };
    };
    const cycled = (n) => {''')
rep("return { looks, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled,", "return { looks, sunNow, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled,")
# fixed looks (Mordor, caves...) keep a fixed high sun direction
rep("      if (FIXED[g]) return looks[g];", "      if (FIXED[g]) return Object.assign({}, looks[g], { SunDX: 0.25, SunDY: 0.32, Warm: 0 });")

# ---------- 4. render ----------
BUILD_JS = r'''      const buildHm = (u, b0, heap, off, stride, sx, sy, w, h, hudRows) => {
        const n = w * h; if (!hmB || hmB.length !== n * 2) { hmB = new Uint8Array(n * 2); kk = new Uint8Array(n); }
        const yEnd = h - hudRows; let tall = 0;
        // 1. what each pixel is: 2 = sprite, 1 = walk-behind scenery (BG2: tile slots 1024-1535), 0 = ground
        for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
          let k = 0;
          if (y < yEnd) {
            const i = (y + sy) * stride + x + sx, t = u[b0 + i];
            if (t >>> 31) {
              if ((t >>> 25) & 1) {
                if (!((t >>> 26) & 1)) {   // see-through sprites, flames and spells cast no shadow
                  const pi = off + i * 3, r = heap[pi], g = heap[pi + 1], bb = heap[pi + 2], mx = Math.max(r, g, bb), mn = Math.min(r, g, bb);
                  k = (mx > 215 && mx - mn > 0.55 * mx) || (r > 200 && bb < 90 && r - bb > 130 && g > 60) ? 0 : 2;
                }
              } else { const sl = t & 4095; k = sl >= 1024 && sl < 1536 ? 1 : 0; }
            }
          }
          kk[y * w + x] = k;
        }
        // 2. runs up each column from the foot (gaps of up to 2 pixels bridged); R = run length, G = kind
        for (let x = 0; x < w; x++) {
          let run = 0, kind = 0, gap = 0, bot = -1, thin = true;
          const end = (top) => {   // rain and other 1-pixel-wide sprite bits shorter than 14 rows cast nothing
            if (kind === 2 && thin && run < 14) for (let yy = bot; yy >= top; yy--) { const q = (yy * w + x) * 2; hmB[q] = 0; hmB[q + 1] = 0; }
          };
          for (let y = h - 1; y >= 0; y--) {
            const o = (y * w + x) * 2, k = kk[y * w + x];
            if (k) {
              if (k === kind && gap <= 2) run += gap + 1; else { if (kind) end(y + 1 + gap); run = 1; kind = k; bot = y; thin = true; }
              gap = 0; hmB[o] = run > 255 ? 255 : run; hmB[o + 1] = k * 100; tall++;
              if (k === 2 && thin && ((x > 0 && kk[y * w + x - 1] === 2) || (x < w - 1 && kk[y * w + x + 1] === 2))) thin = false;
            } else {
              if (kind && ++gap > 2) { end(y + gap); kind = 0; run = 0; }
              hmB[o] = 0; hmB[o + 1] = 0;
            }
          }
          if (kind) end(0);
        }
        // 3. A long straight bottom edge (12+ feet in a row) is where a wall or roof top was cut onto the walk-behind
        // layer, not a real foot: those runs don't cast (else wall tops throw hard boxes onto their own wall faces).
        // Small breaks (rain, a sprite in front) and 1-pixel steps still count as one edge.
        const foot = (x, y) => y >= 0 && y < h && hmB[(y * w + x) * 2] === 1 && hmB[(y * w + x) * 2 + 1] === 100;
        const near = (x, y) => foot(x, y) || foot(x, y - 1) || foot(x, y + 1);
        const flag = (x, y) => { for (let yy = y, g = 0; yy >= 0; yy--) { const q = (yy * w + x) * 2; if (hmB[q + 1] === 100) { hmB[q + 1] = 120; g = 0; } else if (hmB[q + 1] === 0 && g < 2) g++; else break; } };
        for (let y = 0; y < yEnd; y++) {
          let x = 0;
          while (x < w) {
            if (!foot(x, y)) { x++; continue; }
            let e = x + 1, last = x; while (e < w && e - last <= 3) { if (near(e, y)) last = e; e++; }
            let ex = 0; for (let xx = x; xx <= last; xx++) if (foot(xx, y)) ex++;   // straight: most feet on this exact row
            // and the picture carries on across the edge (a wall face below a cut top), unlike a pillar or tree standing on the ground
            let dIn = 0, dOut = 0;
            if (last - x >= 11 && ex >= 0.75 * (last - x + 1) && y >= 1 && y + 1 < yEnd) for (let xx = x; xx <= last; xx++) if (foot(xx, y)) {
              const a = off + ((y + sy - 1) * stride + xx + sx) * 3, b = a + stride * 3, c = b + stride * 3;
              for (let ch = 0; ch < 3; ch++) { dIn += Math.abs(heap[a + ch] - heap[b + ch]); dOut += Math.abs(heap[b + ch] - heap[c + ch]); }
            }
            if (last - x >= 11 && ex >= 0.75 * (last - x + 1) && dOut <= 1.5 * dIn + 12 * ex) for (let xx = x; xx <= last; xx++) for (const dy of [-1, 0, 1]) if (foot(xx, y + dy)) flag(xx, y + dy);
            x = last + 1;
          }
        }
        // 4. thin slivers of the same cut top (1-3 px columns whose foot sits off the edge row) follow their neighbours
        for (let x = 0; x < w; x++) {
          let y = yEnd - 1;
          while (y >= 0) {
            if (hmB[(y * w + x) * 2 + 1] !== 100) { y--; continue; }
            let top = y, nb = 0;
            while (top >= 0 && hmB[(top * w + x) * 2 + 1] === 100) {
              for (let dx = -3; dx <= 3; dx++) { const xx = x + dx; if (dx && xx >= 0 && xx < w && hmB[(top * w + xx) * 2 + 1] === 120) { nb++; break; } }
              top--;
            }
            if (nb >= 0.4 * (y - top)) for (let yy = y; yy > top; yy--) hmB[(yy * w + x) * 2 + 1] = 121;
            y = top;
          }
        }
        return tall;
      };
'''
rep("      let aT = null, aF = null;\n",
    "      let aT = null, aF = null;\n"
    "      let shP = null; try { if (glowP) shP = prog(SHADOW_GLSL); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push(\"shadow: \" + (e && e.message || e)); }\n"
    "      let shT = null, shF = null, hmT = null, hmB = null, kk = null, shOn = 0;\n"
    "      // Height map for the shadow pass, from the engine's tile tags of the shown picture (see SHADOW_GLSL).\n"
    "      const shadowTags = () => {\n"
    "        if (window.__shTagsDbg) return [window.__shTagsDbg, 0];\n"
    "        const M = window.__wideM; if (!M || !M._rotk_skin_slot || !M._rotk_skin) return null;\n"
    "        if (!M.__shTagOn) { M._rotk_skin(1); M.__shTagOn = 1; return null; }\n"
    "        const ptr = M._rotk_skin_slot(WideHost.front); if (!ptr) return null;\n"
    "        return [new Uint32Array(M.HEAPU8.buffer), ptr >> 2];\n"
    "      };\n" + BUILD_JS)
rep("        if (aliveP) { aT = tex(w, h, \"rgba\", gl.LINEAR);",
    "        if (shT) { gl.deleteTexture(shT); gl.deleteFramebuffer(shF); gl.deleteTexture(hmT); shT = null; }\n"
    "        if (shP) { shT = tex(w, h, \"rgba\", gl.LINEAR); shF = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, shF); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, shT, 0);\n"
    "          hmT = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, hmT); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RG8, w, h, 0, gl.RG, gl.UNSIGNED_BYTE, null);\n"
    "          for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.NEAREST], [gl.TEXTURE_MAG_FILTER, gl.NEAREST], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v); }\n"
    "        if (aliveP) { aT = tex(w, h, \"rgba\", gl.LINEAR);")
# the pass runs after the light map (it reads the light pools for torch shadows)
rep("""              gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            }
          }
          gl.bindSampler(0, null);
        }""", """              gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
            }
          }
          shOn = 0;
          if (shP && shT && !window.__shOff && (cur.SunSh > 0.01 || cur.TorchSh > 0.01)) {
            try {
              const tg = shadowTags();
              if (tg) {
                buildHm(tg[0], tg[1], heap, off, stride, sx, sy, w, h, h > 100 ? 34 : 0);
                gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, hmT); gl.bindSampler(0, null); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
                gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RG, gl.UNSIGNED_BYTE, hmB);
                const su = shP.u; gl.useProgram(shP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, shF); gl.viewport(0, 0, w, h);
                if (su.Hm) gl.uniform1i(su.Hm, 0);
                gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, tT[0]); gl.bindSampler(1, linS); if (su.Torch) gl.uniform1i(su.Torch, 1);
                gl.uniformMatrix4fv(su.MVPMatrix, false, MVP); if (su.GPx) gl.uniform2f(su.GPx, 1 / w, 1 / h); if (su.HudY) gl.uniform1f(su.HudY, hudY);
                if (su.SunD) gl.uniform2f(su.SunD, cur.SunDX, cur.SunDY);
                if (su.SunK) gl.uniform1f(su.SunK, cur.SunSh); if (su.TorchSh) gl.uniform1f(su.TorchSh, cur.TorchSh);
                if (su.TorchK) gl.uniform1f(su.TorchK, (cur.Night > 0.01 || cur.TorchK > 0.01 || cur.FireK > 0.01) ? Math.max(cur.TorchK, cur.Night) : 0);
                gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); gl.bindSampler(1, null); shOn = 1;
              }
            } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("shadow: " + (e && e.message || e)); window.__shOff = 1; }
          }
          gl.bindSampler(0, null);
        }""")
rep("gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, tT[0]); gl.bindSampler(3, linS); if (fu.Torch) gl.uniform1i(fu.Torch, 3);",
    "gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, tT[0]); gl.bindSampler(3, linS); if (fu.Torch) gl.uniform1i(fu.Torch, 3);\n"
    "          gl.activeTexture(gl.TEXTURE5); gl.bindTexture(gl.TEXTURE_2D, shT); gl.bindSampler(5, linS); if (fu.Shad) gl.uniform1i(fu.Shad, 5);\n"
    "          if (fu.ShOn) gl.uniform1f(fu.ShOn, shOn); if (fu.ShDbg) gl.uniform1f(fu.ShDbg, window.__shDbg && shOn ? 1 : 0);\n"
    "          if (fu.Warm) gl.uniform1f(fu.Warm, cur.Warm || 0); if (fu.ShCol) gl.uniform3fv(fu.ShCol, cur.ShCol);")
open(out, "w").write(s); print("ok shadows")
