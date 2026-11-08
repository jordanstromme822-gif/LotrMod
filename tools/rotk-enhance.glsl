/*
	Return of the King Play Room: scene enhance pass (runs on the game's own pixels, before SABR).
	- Environment: gentle vibrance, local contrast (unsharp mask) and a little depth in the shadows.
	- Water: the game's pools are low-saturation teal (green and blue above red). Those pixels get
	  clearer, cooler colour and stronger highlights, so the pools read as water. HUD and characters
	  are left almost untouched because they are saturated or not teal.
*/
#if defined(VERTEX)
#if __VERSION__ >= 130
#define COMPAT_VARYING out
#define COMPAT_ATTRIBUTE in
#else
#define COMPAT_VARYING varying
#define COMPAT_ATTRIBUTE attribute
#endif
#ifdef GL_ES
#define COMPAT_PRECISION mediump
#else
#define COMPAT_PRECISION
#endif
COMPAT_ATTRIBUTE vec4 VertexCoord;
COMPAT_ATTRIBUTE vec4 COLOR;
COMPAT_ATTRIBUTE vec4 TexCoord;
COMPAT_VARYING vec4 COL0;
COMPAT_VARYING vec4 TEX0;
uniform mat4 MVPMatrix;
void main()
{
    gl_Position = MVPMatrix * VertexCoord;
    COL0 = COLOR;
    TEX0.xy = TexCoord.xy;
}
#elif defined(FRAGMENT)
#if __VERSION__ >= 130
#define COMPAT_VARYING in
#define COMPAT_TEXTURE texture
out vec4 FragColor;
#else
#define COMPAT_VARYING varying
#define FragColor gl_FragColor
#define COMPAT_TEXTURE texture2D
#endif
#ifdef GL_ES
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
#define COMPAT_PRECISION mediump
#else
#define COMPAT_PRECISION
#endif
uniform COMPAT_PRECISION vec2 TextureSize;
uniform sampler2D Texture;
COMPAT_VARYING vec4 TEX0;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void main()
{
    vec2 px = 1.0 / TextureSize;
    vec2 uv = TEX0.xy;
    vec3 c = COMPAT_TEXTURE(Texture, uv).rgb;
    vec3 n = COMPAT_TEXTURE(Texture, uv + vec2(0.0, -px.y)).rgb;
    vec3 s = COMPAT_TEXTURE(Texture, uv + vec2(0.0,  px.y)).rgb;
    vec3 e = COMPAT_TEXTURE(Texture, uv + vec2( px.x, 0.0)).rgb;
    vec3 w = COMPAT_TEXTURE(Texture, uv + vec2(-px.x, 0.0)).rgb;
    vec3 blur = (n + s + e + w) * 0.25;

    // Local contrast: brings out stone, grass and wood texture.
    vec3 col = c + (c - blur) * 0.35;

    // Water: low-saturation teal (g and b above r).
    float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));
    float sat = (mx - mn) / max(mx, 0.001);
    float teal = smoothstep(0.02, 0.07, c.g - c.r) * smoothstep(-0.02, 0.03, c.b - c.r) * (1.0 - smoothstep(0.35, 0.5, sat));
    float lw = luma(c);
    vec3 base = mix(c, blur, 0.4);                                   // smoother surface
    base = mix(vec3(luma(base)), base, 1.35);                         // richer tint
    vec3 water = base * vec3(0.92, 1.03, 1.12);                       // cooler, clearer
    water += vec3(0.75, 0.9, 1.0) * max(luma(c - blur), 0.0) * 2.2;  // brighter ripples / glints
    water = mix(water, water * (0.85 + 0.35 * lw), 0.5);             // deeper darks, brighter tops
    col = mix(col, water, teal * 0.85);

    // Vibrance: more colour in dull pixels, little in already-bright ones.
    float l = luma(col);
    float vib = 0.28 * (1.0 - sat);
    col = mix(vec3(l), col, 1.0 + vib);

    // Gentle S-curve for depth.
    col = clamp(col, 0.0, 1.0);
    col = mix(col, col * col * (3.0 - 2.0 * col), 0.22);

    FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
#endif
