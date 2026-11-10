// Crisp skin (Graphics phase 2). Same tag lookup as the skin pass: one u32 per game pixel,
// FNV-1a key into an atlas cell of 36 (2 px pad, 32 px of 4x art). The page draws this into a
// 4x (or 3x) target with the atlas filter set to nearest, so each authored texel stays a hard pixel.
// Unreplaced pixels are the game's own texels, also nearest. ScaleFX does not run on this path.
#if defined(VERTEX)
in vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;
void main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }
#else
in vec2 v; out vec4 o;
uniform sampler2D Texture; uniform highp usampler2D Tags; uniform highp usampler2D Lut; uniform sampler2D Atlas;
uniform vec2 GameSize; uniform vec2 AtlasSize; uniform float Per; uniform float Mix;
void main(){
  vec4 c = textureLod(Texture, v, 0.0); o = vec4(c.rgb, 1.0);
  vec2 pos = v * GameSize; ivec2 ip = ivec2(floor(pos)); vec2 f = fract(pos);
  uint t = texelFetch(Tags, ip, 0).r;
  if ((t >> 31u) == 0u || (t & (3u << 26u)) != 0u) return;
  uint li = ((t >> 12u) & 15u) * 4096u + (t & 4095u);
  uint cell = texelFetch(Lut, ivec2(int(li & 255u), int(li >> 8u)), 0).r;
  if (cell == 0u) return;
  cell -= 1u;
  float tx = float((t >> 17u) & 7u), ty = float((t >> 20u) & 7u);
  float fx = ((t >> 23u) & 1u) == 1u ? 1.0 - f.x : f.x;
  float fy = ((t >> 24u) & 1u) == 1u ? 1.0 - f.y : f.y;
  uint per = uint(Per);
  vec2 cxy = vec2(float(cell % per), float(cell / per)) * 36.0 + 2.0;
  vec2 uv = (cxy + (vec2(tx, ty) + vec2(fx, fy)) * 4.0) / AtlasSize;
  vec4 a = textureLod(Atlas, uv, 0.0);
  o.rgb = mix(c.rgb, a.rgb, a.a * Mix);
}
#endif
