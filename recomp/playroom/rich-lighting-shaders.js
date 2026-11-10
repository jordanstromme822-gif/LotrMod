  // Rich lighting (Jordan, 2026-11-10: "huge upgrade to textures, character details, scene details, coloring"), step 1:
  // after Sharp HD, a glow pass (bright warm pixels like lava, fire and torches spill light), deeper shadows from
  // wide-area local contrast, and a colour grade picked from the level's look (woods, lava, snow, caves...).
  // window.__rotkLook holds the target look; the page eases toward it so level changes blend. Off with rotk-light=0.
  const LIGHT_GLOW = "#if defined(VERTEX)\nin vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;\nvoid main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }\n#else\nprecision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture; uniform vec2 TextureSize; uniform vec2 Dir; uniform int Extract; uniform float Thr;\n" +
    "vec4 tap(vec2 uv){ vec4 t = texture(Texture, uv); if (Extract == 0) return t; vec3 c = t.rgb; float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));\n" +
    "  float warm = clamp((c.r - c.b) * 1.6 + (c.r - c.g) * 0.6, 0.0, 1.0); float sat = (mx - mn) / max(mx, 0.001);\n" +
    "  float b = smoothstep(Thr, Thr + 0.3, mx) * (0.25 + 0.75 * warm) * (0.4 + 0.6 * sat) + smoothstep(0.88, 1.0, mx) * 0.18;\n" +
    "  return vec4(c * b, dot(c, vec3(0.299, 0.587, 0.114))); }\n" +
    "void main(){ vec2 d = Dir / TextureSize; vec4 s = tap(v) * 0.2270270;\n" +
    "  s += (tap(v + d * 1.3846) + tap(v - d * 1.3846)) * 0.3162162; s += (tap(v + d * 3.2308) + tap(v - d * 3.2308)) * 0.0702703; o = s; }\n#endif\n";
  const LIGHT_FINAL = "#if defined(VERTEX)\nin vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;\nvoid main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }\n#else\nprecision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture; uniform sampler2D Glow;\n" +
    "uniform vec3 ShadowTint, HiTint, GlowTint, FogCol, Gain; uniform float Sat, GlowK, Clarity, Vig, Fog, Lift, Amount, Sun, Relief; uniform vec2 Px;\n" +
    "float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }\n" +
    "void main(){ vec3 c0 = texture(Texture, v).rgb; vec4 g = texture(Glow, v); vec3 c = c0; float l = luma(c);\n" +
    "  float lx = luma(texture(Texture, v + vec2(Px.x, 0.0)).rgb) - luma(texture(Texture, v - vec2(Px.x, 0.0)).rgb);\n" +
    "  float ly = luma(texture(Texture, v + vec2(0.0, Px.y)).rgb) - luma(texture(Texture, v - vec2(0.0, Px.y)).rgb);\n" +
    "  c *= clamp(1.0 - Relief * (lx * 0.7 + ly), 0.75, 1.3);\n" +              // light from the top left: raised edges catch it
    "  float k = clamp(1.0 + Clarity * (l - g.a) * 2.2, 0.55, 1.6); c *= k;\n" +              // shadows sink, edges catch light
    "  float d = smoothstep(0.0, 0.55, g.a); c *= mix(0.82, 1.0, mix(1.0, d, Clarity));\n" +      // dark areas stay dark (depth)
    "  l = clamp(luma(c), 0.0, 1.0); float keepBlack = smoothstep(0.0, 0.1, l); c += (ShadowTint * (1.0 - l) * (1.0 - l) + HiTint * l * l) * keepBlack;\n" +
    "  c = mix(vec3(luma(c)), c, Sat); c = c * Gain + Lift * (1.0 - c) * keepBlack;\n" +
    "  vec2 q = v - 0.5; float sun = 1.0 + Sun * (0.35 - v.y * 0.5 - v.x * 0.2); c *= sun;\n" +
    "  c = mix(c, FogCol, Fog * (1.0 - 0.6 * l) * keepBlack);\n" +
    "  vec3 gw = g.rgb * GlowK * GlowTint; c = 1.0 - (1.0 - clamp(c, 0.0, 1.0)) * (1.0 - clamp(gw, 0.0, 1.0));\n" +
    "  c *= 1.0 - Vig * smoothstep(0.3, 0.78, length(q * vec2(1.0, 0.9)));\n" +
    "  o = vec4(clamp(mix(c0, c, Amount), 0.0, 1.0), 1.0); }\n#endif\n";
