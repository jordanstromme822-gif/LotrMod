#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
precision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture; uniform sampler2D Glow; uniform sampler2D Base;
uniform vec3 ShadowTint, HiTint, GlowTint, FogCol, Gain, WaterCol; uniform float Sat, GlowK, Clarity, Vig, Fog, Lift, Amount, Sun, Relief, Water, Time; uniform vec2 Px, GPx;
float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
// Water: clear blue or teal (green and blue well above red), not sky (sky's green is close to red) and not grass.
float wet(vec3 c){ return smoothstep(0.09, 0.17, c.g - c.r) * smoothstep(0.09, 0.17, c.b - c.r) * (1.0 - smoothstep(0.06, 0.14, c.g - c.b)); }
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
void main(){
  vec3 c0 = texture(Texture, v).rgb; vec4 g = texture(Glow, v); vec3 c = c0;
  // ---- Water (Jordan, 2026-11-10: "the water still looks bad") ----
  float m = 0.0;
  if (Water > 0.0) {
    m = wet(texture(Base, v).rgb);
    if (m > 0.01) {
      float t = Time; vec2 gp = v / GPx;                       // game pixels
      // Shore: any dry pixel within ~3 game pixels.
      float s = 1.0;
      for (int i = 0; i < 8; i++) { float a = float(i) * 0.785398; s = min(s, wet(texture(Base, v + vec2(cos(a), sin(a)) * GPx * 2.0).rgb)); }
      float shore = 1.0 - s;
      // Refraction shimmer: the water's own texture, gently wobbling and blurred so the tiled ripple pattern melts away.
      vec2 off = vec2(sin(gp.y * 0.21 + t * 1.7) + sin((gp.x + gp.y) * 0.13 - t * 1.1), cos(gp.x * 0.17 + t * 1.3) + sin((gp.x - gp.y) * 0.11 + t * 0.9)) * GPx * 0.9;
      vec3 sharp = texture(Texture, v + off).rgb;
      vec2 vo = v + off * 1.5; vec2 e = GPx * 1.3;
      vec3 soft = (texture(Base, vo + vec2(e.x, e.y)).rgb + texture(Base, vo + vec2(-e.x, e.y)).rgb + texture(Base, vo + vec2(e.x, -e.y)).rgb + texture(Base, vo + vec2(-e.x, -e.y)).rgb) * 0.25;
      vec3 w = mix(sharp, soft, 0.8);
      float wl = luma(w);
      // Deeper, richer body colour; darker away from the shore.
      vec3 body = mix(w, WaterCol * (0.55 + 0.9 * wl), 0.55) * mix(0.8, 1.05, shore);
      // Moving light bands and sparkles on the crests.
      float band = pow(0.5 + 0.5 * sin(dot(gp, vec2(0.08, 0.12)) + t * 1.4 + sin(gp.x * 0.05 - t * 0.5) * 2.0), 6.0);
      float band2 = pow(0.5 + 0.5 * sin(dot(gp, vec2(-0.11, 0.07)) - t * 1.1), 8.0);
      body += vec3(0.75, 0.9, 1.0) * (band * 0.10 + band2 * 0.07);
      vec2 cell = floor(gp / 4.0); float h = hash(cell); vec2 fc = fract(gp / 4.0) - 0.5;
      float tw = max(0.0, sin(t * (2.0 + h * 3.0) + h * 40.0)); tw = pow(tw, 24.0) * step(0.85, h) * smoothstep(0.22, 0.0, length(fc));
      body += vec3(1.0) * tw * 0.6;
      // White foam along the shore, breathing in and out.
      float foamN = 0.5 + 0.5 * sin(gp.x * 0.7 + gp.y * 0.9 + t * 2.2) * sin(gp.y * 0.5 - t * 1.6);
      body = mix(body, vec3(0.92, 0.96, 1.0), shore * shore * (0.12 + 0.22 * foamN));
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
