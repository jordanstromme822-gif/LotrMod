// HD weapons (Graphics phase 6). One device-resolution pass over the picture already drawn.
// A fragment whose game tile is in the weapons map is replaced by the 128px cell, filtered
// in linear mip space. Every other fragment is discarded, so pixel tiles stay as they were.
//
// Flips are tag bits 23 and 24, the same bits crisp-skin.glsl uses. Affine OBJ are not tagged
// by the skin hook, so they are not replaced here either.
//
// Atlas files are straight alpha. The page premultiplies the colour atlas on upload.
// Normals are tangent space, +X right, +Y up, +Z toward the viewer, un-flipped.
// Material: R metalness, G roughness, B edge mask, A emissive.
#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
precision highp float;
in vec2 v; out vec4 o;
uniform highp usampler2D Tags;
uniform sampler2D WLut, Atlas, Nrm, Mat;
uniform vec2 GameSize, AtlasSize;
uniform float Cell, Pad, Scale, Mode;
uniform vec3 KeyDir, KeyCol;
uniform vec4 LPos[4];
uniform vec3 LCol[4];
uniform float LN;

float ch(float x){ return floor(x * 255.0 + 0.5); }
float Dggx(float NoH, float a){ float a2 = a * a; float d = NoH * NoH * (a2 - 1.0) + 1.0; return a2 / max(3.14159 * d * d, 1e-4); }
float Gitem(float Nd, float a){ float k = (a + 1.0) * (a + 1.0) / 8.0; return Nd / max(Nd * (1.0 - k) + k, 1e-4); }
vec3 envCol(vec3 R){
  float up = clamp(-R.y * 0.5 + 0.55, 0.0, 1.0);
  vec3 sky = mix(vec3(0.05, 0.045, 0.06), vec3(0.20, 0.24, 0.32), up);
  sky += vec3(0.28, 0.18, 0.08) * pow(clamp(dot(normalize(R), normalize(KeyDir)), 0.0, 1.0), 12.0);
  return sky;
}

void main(){
  vec2 du = dFdx(v), dv = dFdy(v);
  vec2 gp = v * GameSize;
  ivec2 ip = ivec2(clamp(floor(gp), vec2(0.0), GameSize - vec2(1.0)));
  vec2 f = fract(gp);
  uint t = texelFetch(Tags, ip, 0).r;
  if ((t >> 31u) == 0u || (t & (3u << 26u)) != 0u) discard;
  uint li = ((t >> 12u) & 15u) * 4096u + (t & 4095u);
  vec4 lb = texelFetch(WLut, ivec2(int(li & 255u), int(li >> 8u)), 0);
  float col = ch(lb.r), row = ch(lb.g);
  if (col < 0.5) discard;
  col -= 1.0; row -= 1.0;
  float tx = float((t >> 17u) & 7u), ty = float((t >> 20u) & 7u);
  float hf = float((t >> 23u) & 1u), vf = float((t >> 24u) & 1u);
  float fx = hf > 0.5 ? 1.0 - f.x : f.x;
  float fy = vf > 0.5 ? 1.0 - f.y : f.y;
  vec2 pxy = vec2(col, row) * Cell + Pad + vec2(tx, ty) * Scale + vec2(fx, fy) * Scale;
  vec2 auv = pxy / AtlasSize;
  float sxf = hf > 0.5 ? -1.0 : 1.0, syf = vf > 0.5 ? -1.0 : 1.0;
  vec2 adx = vec2(du.x * GameSize.x * sxf, du.y * GameSize.y * syf) * Scale / AtlasSize;
  vec2 ady = vec2(dv.x * GameSize.x * sxf, dv.y * GameSize.y * syf) * Scale / AtlasSize;
  vec4 alb = textureGrad(Atlas, auv, adx, ady);
  if (alb.a < 0.02) discard;
  if (Mode > 0.5) {
    vec4 m = textureGrad(Mat, auv, adx, ady);
    o = vec4(alb.rgb * m.a * 1.4, 1.0);
    return;
  }
  vec3 albedo = alb.rgb / max(alb.a, 1e-3);
  vec3 n = textureGrad(Nrm, auv, adx, ady).rgb * 2.0 - 1.0;
  if (hf > 0.5) n.x = -n.x;
  if (vf > 0.5) n.y = -n.y;
  n.y = -n.y;
  n = normalize(n);
  vec4 m = textureGrad(Mat, auv, adx, ady);
  float metal = clamp(m.r, 0.0, 1.0);
  float rough = clamp(m.g, 0.045, 1.0);
  float edge = clamp(m.b, 0.0, 1.0);
  float emit = clamp(m.a, 0.0, 1.0);
  rough = mix(rough, rough * 0.45, edge);
  vec3 V = vec3(0.0, 0.0, 1.0);
  vec3 F0 = mix(vec3(0.04), albedo, metal);
  vec3 acc = vec3(0.0);
  vec3 Ld = normalize(KeyDir);
  float NoL = clamp(dot(n, Ld), 0.0, 1.0);
  vec3 H = normalize(Ld + V);
  float NoH = clamp(dot(n, H), 0.0, 1.0);
  float NoV = max(dot(n, V), 0.08);
  float HoV = clamp(dot(H, V), 0.0, 1.0);
  float a = rough * rough;
  vec3 F = F0 + (1.0 - F0) * pow(1.0 - HoV, 5.0);
  float spec = Dggx(NoH, a) * Gitem(NoV, a) * Gitem(NoL, a);
  acc += (albedo * (1.0 - metal) * (1.0 - F) + F * spec) * KeyCol * NoL;
  for (int i = 0; i < 4; i++) {
    if (float(i) >= LN) break;
    vec4 Lp = LPos[i];
    vec2 dpx = (v - Lp.xy) / max(vec2(1.0 / GameSize.x, 1.0 / GameSize.y), vec2(1e-6));
    float dist = length(dpx);
    float rad = max(Lp.z, 4.0);
    if (dist > rad * 1.6) continue;
    float att = exp(-dist * dist / (rad * rad * 0.55)) * Lp.w;
    vec3 Ldir = normalize(vec3(-dpx.x, -dpx.y, rad * 0.35));
    float nl = clamp(dot(n, Ldir), 0.0, 1.0);
    vec3 Hh = normalize(Ldir + V);
    float nh = clamp(dot(n, Hh), 0.0, 1.0);
    float hv = clamp(dot(Hh, V), 0.0, 1.0);
    vec3 Ff = F0 + (1.0 - F0) * pow(1.0 - hv, 5.0);
    float sp = Dggx(nh, a) * Gitem(NoV, a) * Gitem(nl, a);
    acc += (albedo * (1.0 - metal) * (1.0 - Ff) + Ff * sp) * LCol[i] * nl * att;
  }
  vec3 R = reflect(vec3(0.0, 0.0, -1.0), n);
  acc += envCol(R) * F0 * mix(0.15, 0.85, metal) * (1.0 - rough);
  vec3 emissive = albedo * emit * 1.6;
  acc += emissive;
  o = vec4(acc * alb.a, alb.a);
}
#endif
