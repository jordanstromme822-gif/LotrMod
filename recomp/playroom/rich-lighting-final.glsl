#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
precision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture; uniform sampler2D Glow; uniform sampler2D Base;
uniform vec3 ShadowTint, HiTint, GlowTint, FogCol, Gain, WaterCol; uniform float Sat, GlowK, Clarity, Vig, Fog, Lift, Amount, Sun, Relief, Water, Time; uniform vec2 Px, GPx;
float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
// Water: clear blue or teal (green and blue well above red), not sky (sky's green is close to red) and not grass.
float paleF(vec3 c){ return smoothstep(0.03, 0.08, c.g - c.r) * smoothstep(-0.01, 0.05, c.b - c.r) * smoothstep(0.42, 0.56, luma(c)); }   // pale teal: cloud reflections (grey stone has green = red)
float wet(vec3 c){ return smoothstep(0.13, 0.2, c.g - c.r) * smoothstep(0.13, 0.2, c.b - c.r) * (1.0 - smoothstep(0.06, 0.14, c.g - c.b)); }
void main(){
  vec3 c0 = texture(Texture, v).rgb; vec4 g = texture(Glow, v); vec3 c = c0;
  // ---- Water (Jordan, 2026-11-10: "the water still looks bad"; v152: no motion, it flickered) ----
  // Calm and steady: the tiled zigzag is blurred away and the water gets a deeper colour. Nothing moves on its own,
  // nothing is added at the edges (v151's shore foam made a white rim round enemies), and the pale cloud reflections
  // count as water when water surrounds them, so they stay soft instead of looking like stone.
  float m = 0.0;
  if (Water > 0.0) {
    vec3 b0 = texture(Base, v).rgb; m = wet(b0);
    float pale = paleF(b0);
    float cloud = 0.0; vec3 wsum = vec3(0.0); float wn = 0.0;
    if (m > 0.01 || pale > 0.01) {
      // Two rings of water samples: how much water is around, and its colour (used to paint over cloud reflections).
      float near = 0.0;
      for (int i = 0; i < 16; i++) {
        float a = float(i) * 0.785398 + (i < 8 ? 0.0 : 0.39); float r = i < 8 ? 4.0 : 8.0;
        vec3 sb = texture(Base, v + vec2(cos(a), sin(a)) * GPx * r).rgb; float pw = paleF(sb); float ww = max(wet(sb), pw * 0.8);
        if (i < 8) near += ww; float cw = wet(sb) * (1.0 - pw); wsum += sb * cw; wn += cw;
      }
      near *= 0.125;
      // Clouds removed from the water (Jordan, 2026-11-10): pale pixels with water around them become that water.
      cloud = pale * smoothstep(0.45, 0.75, near) * smoothstep(0.5, 2.0, wn);
      m = max(m * smoothstep(0.2, 0.5, near + m * 0.3), cloud);
    }
    if (cloud > 0.01) { vec3 wc = wsum / max(wn, 0.001); c = mix(c, wc, cloud); }
    if (m > 0.01) {
      vec3 sb0 = texture(Base, v).rgb; float w0 = 0.2 * max(wet(sb0), 0.05); vec3 soft = sb0 * w0; float sw = w0;
      for (int i = 0; i < 8; i++) { float a = float(i) * 0.785398 + 0.39; float r = (i % 2 == 0) ? 1.4 : 2.6; vec3 sb = texture(Base, v + vec2(cos(a), sin(a)) * GPx * r).rgb; float ww = 0.1 * max(wet(sb), 0.05); soft += sb * ww; sw += ww; }
      soft /= sw; if (cloud > 0.01) soft = mix(soft, wsum / max(wn, 0.001), cloud);
      vec3 w = mix(c, soft, 0.88); float wl = luma(w);
      vec3 body = mix(w, WaterCol * (0.55 + 0.9 * wl), 0.5);
      c = mix(c, body, m * Water);
    }
  }
  float l = luma(c);
  float lx = luma(texture(Texture, v + vec2(Px.x, 0.0)).rgb) - luma(texture(Texture, v - vec2(Px.x, 0.0)).rgb);
  float ly = luma(texture(Texture, v + vec2(0.0, Px.y)).rgb) - luma(texture(Texture, v - vec2(0.0, Px.y)).rgb);
  c *= clamp(1.0 - Relief * (1.0 - m) * (lx * 0.7 + ly), 0.75, 1.3);         // light from the top left: raised edges catch it
  float k = clamp(1.0 + Clarity * (l - g.a) * 2.2, 0.55, 1.6); c *= mix(k, 1.0, m * 0.7);   // shadows sink, edges catch light
  float d = smoothstep(0.0, 0.55, g.a); c *= mix(0.82, 1.0, mix(1.0, d, Clarity));            // dark areas stay dark (depth)
  l = clamp(luma(c), 0.0, 1.0); float keepBlack = smoothstep(0.0, 0.1, l);
  c += (ShadowTint * (1.0 - l) * (1.0 - l) + HiTint * l * l) * keepBlack;
  c = mix(vec3(luma(c)), c, Sat); c = c * Gain + Lift * (1.0 - c) * keepBlack;
  vec2 q = v - 0.5; c *= 1.0 + Sun * (0.35 - v.y * 0.5 - v.x * 0.2);
  c = mix(c, FogCol, Fog * (1.0 - 0.6 * l) * keepBlack);
  vec3 gw = g.rgb * GlowK * GlowTint; c = 1.0 - (1.0 - clamp(c, 0.0, 1.0)) * (1.0 - clamp(gw, 0.0, 1.0));
  c *= 1.0 - Vig * smoothstep(0.3, 0.78, length(q * vec2(1.0, 0.9)));
  o = vec4(clamp(mix(c0, c, Amount), 0.0, 1.0), 1.0);
}
#endif
