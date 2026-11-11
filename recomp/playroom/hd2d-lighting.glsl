// HD-2D lighting (Graphics phase 1). One screen pass over the picture the Play Room already drew
// (Sharp HD, then rich lighting / day-night / aura when those are on). Crisp pixels stay put:
// this pass only relights them. It does not blur the colour except a small bloom on emissive pixels.
//
// Picture UV: v.y = 0 is the top of the picture, the same space as the rich-lighting pass.
// The page draws this pass with MVP_FLIP and writes the previous pass into an offscreen target
// with the unflipped MVP, so Texture and Raw share that UV.
//
// Normals
//   NMode 0  luma fallback (always available). A wide height-from-luma read, flattened where the
//            neighbourhood is flat, so walls and the HUD do not shimmer like an emboss filter.
//   NMode 1  full-frame normal texture on Normals, same UV as the picture. RGB is a normal packed
//            to 0..1 (0.5 = 0), alpha is coverage, author +Y is up. The shader flips Y into this
//            picture (Y down). Set window.__hd2dNormalImage to an image or canvas.
//   NMode 2  skin/normals.png, same cell layout as skin/atlas.png (36 px cell, 2 px pad, 4x texels).
//            Tags + Lut are RGBA8 (no integer samplers). Tags are the skin-hook u32, little-endian
//            bytes in RGBA. Lut RG is the atlas cell index + 1, same key as skin/map.json.
//            Invalid, blended, or faded tags fall back to luma for that pixel.
//            Sampled only when the skin hook is already writing tags.
//
// Lights: LPos[i] = (uv.x, uv.y, radius in picture pixels, intensity), LCol[i] = rgb.
// Parts:  PPos[i] = (uv.x, uv.y, radius in picture pixels, intensity), PCol[i] = rgb.
//         The page fills these. window.__hd2dLights / window.__hd2dParts replace or extend them.
// ShadowCut > 0 (Living light's ShadeK is running) halves the shadow term so the two soft
// shadows do not stack.
#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
precision highp float;
in vec2 v; out vec4 o;
uniform sampler2D Texture, Raw, Glow, Normals, Tags, Lut, WeaponEm; uniform float WeaponEmOn;
uniform vec3 FogCol, NightTint;
uniform vec4 LPos[12], LCol[12], PPos[8], PCol[8];
uniform float Night, Sun, Fog, Vig, Time, HudY, Menu, Already, GlowOn, NMode, ShadowCut, HeroK, LN, PN, Dbg;
uniform float Cell, Pad, Per;
uniform vec2 GPx, GameSize, AtlasSize, HeroP;

float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
float satf(vec3 c){ float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)); return (mx - mn) / max(mx, 1e-4); }
float ch(float x){ return floor(x * 255.0 + 0.5); }
vec3 safeN(vec3 n){ float s = dot(n, n); return s > 0.04 ? n * inversesqrt(s) : vec3(0.0, 0.0, 1.0); }

vec3 lumaNormal(vec2 uv){
  // Two-and-a-half game pixels, not one: this follows a form (armour, bark, a stone edge),
  // and a flat wall stays camera-facing instead of crawling.
  float r = luma(textureLod(Raw, uv + vec2(GPx.x * 2.5, 0.0), 0.0).rgb);
  float l = luma(textureLod(Raw, uv - vec2(GPx.x * 2.5, 0.0), 0.0).rgb);
  float u = luma(textureLod(Raw, uv - vec2(0.0, GPx.y * 2.5), 0.0).rgb);
  float d = luma(textureLod(Raw, uv + vec2(0.0, GPx.y * 2.5), 0.0).rgb);
  float hx = r - l, hy = d - u, mag = abs(hx) + abs(hy);
  float z = mix(0.72, 3.4, 1.0 - smoothstep(0.018, 0.12, mag));
  return safeN(vec3(-hx * 2.5, -hy * 2.5, z));
}

// Authoring space is +Y up. Picture space is +Y down (v.y grows toward the HUD).
vec3 decodeN(vec3 rgb){ vec3 n = rgb * 2.0 - 1.0; n.y = -n.y; return safeN(n); }

vec4 atlasNormal(vec2 uv){
  if (AtlasSize.x < 2.0 || Per < 1.0) return vec4(0.0);
  vec2 gp = uv * GameSize;
  ivec2 ip = ivec2(clamp(floor(gp), vec2(0.0), GameSize - vec2(1.0)));
  vec2 f = fract(gp);
  vec4 tb = texelFetch(Tags, ip, 0);
  float b0 = ch(tb.r), b1 = ch(tb.g), b2 = ch(tb.b), b3 = ch(tb.a);
  if (b3 < 128.0) return vec4(0.0);                 // tag bit 31, valid
  if (mod(floor(b3 / 4.0), 4.0) > 0.5) return vec4(0.0); // bits 26 and 27, blend / fade: left to luma
  float slot = b0 + mod(b1, 16.0) * 256.0;
  float bank = floor(b1 / 16.0);
  float li = bank * 4096.0 + slot;
  ivec2 lp = ivec2(int(mod(li, 256.0)), int(floor(li / 256.0)));
  vec4 lb = texelFetch(Lut, lp, 0);
  float cell = ch(lb.r) + ch(lb.g) * 256.0;
  if (cell < 0.5) return vec4(0.0);
  float tx = mod(floor(b2 / 2.0), 8.0), ty = mod(floor(b2 / 16.0), 8.0);
  float hf = step(128.0, b2), vf = mod(b3, 2.0);
  float fx = hf > 0.5 ? 1.0 - f.x : f.x;
  float fy = vf > 0.5 ? 1.0 - f.y : f.y;
  float idx = cell - 1.0;
  vec2 cxy = vec2(mod(idx, Per), floor(idx / Per)) * Cell + Pad;
  vec2 nuv = (cxy + (vec2(tx, ty) + vec2(fx, fy)) * 4.0) / AtlasSize;
  vec4 t = textureLod(Normals, nuv, 0.0);
  if (t.a < 0.05) return vec4(0.0);
  vec3 n = t.rgb * 2.0 - 1.0;
  if (hf > 0.5) n.x = -n.x;
  if (vf > 0.5) n.y = -n.y;
  n.y = -n.y;
  return vec4(safeN(n), 1.0);
}

void main(){
  vec2 uv = v;
  vec3 scene = textureLod(Texture, uv, 0.0).rgb;
  // The bottom HUD strip stays the pixels the game drew. Bars and the lamp icon are not relit.
  if (uv.y >= HudY) { o = vec4(scene, 1.0); return; }
  vec3 raw = textureLod(Raw, uv, 0.0).rgb;
  vec3 n = vec3(0.0, 0.0, 1.0);
  if (NMode > 1.5) {
    vec4 an = atlasNormal(uv);
    n = an.w > 0.5 ? an.xyz : lumaNormal(uv);
  } else if (NMode > 0.5) {
    vec4 t = textureLod(Normals, uv, 0.0);
    n = t.a > 0.04 ? decodeN(t.rgb) : lumaNormal(uv);
  } else {
    n = lumaNormal(uv);
  }
  if (Dbg > 0.5) { o = vec4(n * 0.5 + 0.5, 1.0); return; }

  vec3 c = scene;
  // Key light from the top left (the same direction as the rich-lighting relief). Flat normals
  // sit in the middle of the wrap; only a real form swings the pixel.
  vec3 keyDir = normalize(vec3(-0.55, -0.72, 0.85));
  float facing = clamp(dot(n, keyDir) * 0.5 + 0.5, 0.0, 1.0);
  float form = mix(0.78, 1.16, facing);
  float amt = mix(0.85, 0.42, clamp(Already, 0.0, 1.0));
  amt *= mix(1.0, 0.35, clamp(Menu, 0.0, 1.0));
  amt *= mix(1.0, clamp(Sun * 6.0, 0.45, 1.0), 1.0 - clamp(Night, 0.0, 1.0));
  c *= mix(1.0, form, amt);
  // Night is actually dark. When rich lighting already graded the night, only a little more.
  float amb = mix(1.0, 0.58, clamp(Night, 0.0, 1.0) * mix(1.0, 0.45, clamp(Already, 0.0, 1.0)));
  amb = mix(amb, 1.0, clamp(Menu, 0.0, 1.0));
  c *= amb;
  vec3 keyTint = mix(vec3(1.0, 0.9, 0.72), mix(vec3(0.62, 0.7, 0.98), NightTint, 0.55), clamp(Night, 0.0, 1.0));
  c *= mix(vec3(1.0), keyTint, amt * 0.35);

  float sh = mix(1.0, 0.5, clamp(ShadowCut, 0.0, 1.0));
  float lRaw = luma(raw);
  if (Menu < 0.5) {
    // Soft shadow from the key. A hard colour jump (a silhouette against another material) keeps
    // a sharper edge; a broad gradient gets a weaker, softer one.
    float occ = 0.0;
    vec2 st = vec2(-2.4, -2.8) * GPx;
    for (int i = 1; i <= 4; i++) {
      vec3 s = textureLod(Raw, uv + st * float(i), 0.0).rgb;
      float dl = luma(s) - lRaw;
      float jump = length(s - raw);
      float sil = smoothstep(0.06, 0.2, jump);
      float soft = (1.0 - sil) * smoothstep(0.025, 0.1, max(dl, 0.0));
      occ += (sil * 0.62 + soft * 0.22) * smoothstep(0.02, 0.14, dl) * (1.2 - float(i) * 0.18);
    }
    occ = clamp(occ, 0.0, 1.0) * (1.0 - smoothstep(0.55, 0.85, lRaw) * satf(raw));
    c *= 1.0 - occ * 0.32 * sh * mix(0.65, 1.0, amt);
    if (HeroK > 0.001) {
      vec2 feet = HeroP + vec2(0.0, 14.0) * GPx;
      vec2 d = (uv - feet) / GPx;
      float blob = exp(-(d.x * d.x * 0.012 + d.y * d.y * 0.09));
      float edge = length(raw - textureLod(Raw, uv - vec2(0.0, GPx.y * 2.0), 0.0).rgb);
      c *= 1.0 - blob * 0.4 * HeroK * sh * mix(0.6, 1.0, smoothstep(0.04, 0.18, edge));
    }
  }

  vec3 lightRgb = vec3(0.0);
  float nearL = 0.0;
  if (Menu < 0.5) {
    for (int i = 0; i < 12; i++) {
      if (float(i) < LN) {
        vec4 L = LPos[i];
        float rad = max(L.z, 2.0);
        vec2 dpx = (uv - L.xy) / GPx;
        float dist = length(dpx);
        if (dist < rad * 1.7) {
          float att = exp(-dist * dist / (rad * rad * 0.5)) * L.w;
          vec3 Lp = safeN(vec3(dpx * vec2(-1.0), max(rad * 0.4, 8.0)));
          float wrapL = clamp(dot(n, Lp) * 0.55 + 0.45, 0.0, 1.0);
          lightRgb += LCol[i].rgb * att * wrapL;
          nearL = max(nearL, att);
        }
      }
    }
  }
  c += c * lightRgb * 0.7 + lightRgb * 0.06;

  // Depth-ish fog: thicker toward the top of the playfield (farther in this side view) and in
  // dark pixels, thinner on the hero and on anything emissive. Lamps bleed their colour into it.
  float distF = smoothstep(0.0, 0.9, 1.0 - uv.y);
  float dark = 1.0 - smoothstep(0.12, 0.62, luma(c));
  float em = max(smoothstep(0.6, 0.88, lRaw) * smoothstep(0.22, 0.5, satf(raw)), clamp(nearL, 0.0, 1.0));
  float heroNear = 0.0;
  if (HeroK > 0.001) {
    vec2 hd = (uv - HeroP) / GPx;
    heroNear = exp(-dot(hd, hd) / (26.0 * 26.0));
  }
  float fogK = max(Fog, 0.07) * mix(1.0, 1.25, clamp(Night, 0.0, 1.0));
  fogK *= mix(1.0, 0.6, clamp(Already, 0.0, 1.0));
  fogK *= (1.0 - clamp(Menu, 0.0, 1.0));
  float fogA = fogK * (0.28 + 0.72 * distF) * (0.32 + 0.68 * dark);
  fogA *= 1.0 - 0.72 * em;
  fogA *= 1.0 - 0.5 * heroNear;
  fogA = clamp(fogA, 0.0, 0.5);
  vec3 fogC = mix(FogCol, NightTint, clamp(Night, 0.0, 1.0) * 0.45);
  if (Menu < 0.5 && fogK > 0.01) {
    float band = sin(uv.x * 17.0 + (1.0 - uv.y) * 11.0 + Time * 0.07);
    float shaft = smoothstep(0.76, 0.97, band * 0.5 + 0.5);
    float air = smoothstep(0.16, 0.55, lRaw);
    c += fogC * shaft * distF * air * fogK * 0.7;
  }
  c = mix(c, fogC, fogA);
  c += lightRgb * fogA * 0.85;

  if (Menu < 0.5) {
    if (GlowOn > 0.5) {
      vec3 g = textureLod(Glow, uv, 0.0).rgb;
      float gk = max(g.r, max(g.g, g.b));
      c += g * smoothstep(0.02, 0.14, gk) * mix(0.5, 0.26, clamp(Already, 0.0, 1.0));
    } else if (em > 0.25) {
      vec2 o2 = GPx * 2.0;
      vec3 b = raw
        + textureLod(Raw, uv + vec2(o2.x, 0.0), 0.0).rgb
        + textureLod(Raw, uv - vec2(o2.x, 0.0), 0.0).rgb
        + textureLod(Raw, uv + vec2(0.0, o2.y), 0.0).rgb
        + textureLod(Raw, uv - vec2(0.0, o2.y), 0.0).rgb;
      c += b * 0.2 * em * 0.2;
    }
    if (WeaponEmOn > 0.5) {
      vec3 we = textureLod(WeaponEm, uv, 0.0).rgb;
      we += textureLod(WeaponEm, uv + vec2(GPx.x * 3.0, 0.0), 0.0).rgb + textureLod(WeaponEm, uv - vec2(GPx.x * 3.0, 0.0), 0.0).rgb;
      we += textureLod(WeaponEm, uv + vec2(0.0, GPx.y * 3.0), 0.0).rgb + textureLod(WeaponEm, uv - vec2(0.0, GPx.y * 3.0), 0.0).rgb;
      c += we * 0.28;
    }
  }

  if (Menu < 0.5) {
    for (int i = 0; i < 8; i++) {
      if (float(i) < PN) {
        vec4 P = PPos[i];
        vec2 dpx = (uv - P.xy) / GPx;
        float a = exp(-dot(dpx, dpx) / max(P.z * P.z, 0.64)) * P.w;
        if (a > 0.015) c += PCol[i].rgb * a;
      }
    }
  }

  // Cool violet shadow, warm key. Midtones keep a little more colour than the extremes.
  // Menus only take a hint of it, so the UI stays readable.
  float l = clamp(luma(c), 0.0, 1.0);
  vec3 graded = c * mix(vec3(0.84, 0.89, 1.08), vec3(1.08, 1.01, 0.86), smoothstep(0.22, 0.78, l));
  float mid = smoothstep(0.16, 0.42, l) * (1.0 - smoothstep(0.72, 0.94, l));
  graded = mix(vec3(luma(graded)), graded, 1.0 + 0.07 * mid);
  float gAmt = mix(0.82, 0.4, clamp(Already, 0.0, 1.0)) * mix(1.0, 0.18, clamp(Menu, 0.0, 1.0));
  c = mix(c, graded, gAmt);
  float vig = Vig * mix(1.0, 0.35, clamp(Already, 0.0, 1.0)) * mix(1.0, 0.3, clamp(Menu, 0.0, 1.0));
  c *= 1.0 - vig * smoothstep(0.34, 0.84, length((uv - 0.5) * vec2(1.0, 0.88)));
  o = vec4(clamp(c, 0.0, 1.0), 1.0);
}
#endif
