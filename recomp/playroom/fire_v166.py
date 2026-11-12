# v166 fix for an already-patched page (Jordan, 2026-11-11: "Everything is on fire now"): swaps the v164 flame
# detector in ALIVE_GLSL for the stricter one now in alive.py. Usage: python3 fire_v166.py in.html out.html
import sys, re
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
J = lambda t: t.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
src = open(__file__.replace("fire_v166.py", "alive.py")).read()
new = src[src.index("float flame(vec2 uv, float wide){"):src.index("void main(){", src.index("float flame(vec2 uv, float wide){"))]
a = s.index("float flame(vec2 uv, float wide){"); b = s.index("void main(){", a)
assert s.count("float flame(vec2 uv, float wide){") == 1
s = s[:a] + J(new) + s[b:]

# 2. Light pools: only pools lit by a real flame get the strong fire flicker and waver. Others (autumn trees, gold,
#    bright spells) keep the gentle v163 flicker. The ALIVE map now runs before the light map, and the light map
#    carries how much flame is in each pool in its alpha.
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
rep('uniform int Extract; uniform float Thr;\\n" +', 'uniform int Extract; uniform float Thr; uniform sampler2D Alive; uniform float AliveOn;\\n" +')
rep('return vec4(c * b, 0.0); }', 'return vec4(c * b, AliveOn > 0.5 ? texture(Alive, uv).g : 0.0); }')
a = s.index("          if (aliveP && aT && !window.__aliveOff"); b = s.index("          } else aliveOn = 0;\n", a) + len("          } else aliveOn = 0;\n")
blk = s[a:b]; s = s[:a] + s[b:]
L = "          // Light map for the moods:"
rep(L, blk + L)
rep("          if (cur.Night > 0.01 || cur.TorchK > 0.01 || cur.FireK > 0.01) {\n",
    "          if (cur.Night > 0.01 || cur.TorchK > 0.01 || cur.FireK > 0.01) {\n"
    "            gl.useProgram(glowP.p); if (gu.AliveOn) gl.uniform1f(gu.AliveOn, aliveOn);\n"
    "            if (aliveOn) { gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, aT); gl.bindSampler(4, linS); if (gu.Alive) gl.uniform1i(gu.Alive, 4); }\n")
rep(J("vec3 Tw = textureLod(Torch, v + vec2(0.0, 8.0) * GPx, 0.0).rgb; warmNear = step(0.0006, Tw.r - Tw.b * 0.85)"), J("warmNear = step(0.0001, textureLod(Torch, v + vec2(0.0, 8.0) * GPx, 0.0).a)"))
rep(J("vec3 T = texture(Torch, v + vec2(sin(Time * 5.1 + v.y * 19.0), cos(Time * 4.3 + v.x * 17.0)) * GPx * 2.2 * FireK).rgb;"),
    J("float fz = FireK * smoothstep(0.0001, 0.0012, texture(Torch, v).a);   // v166: how much of this pool comes from a real flame\n"
      "    vec3 T = texture(Torch, v + vec2(sin(Time * 5.1 + v.y * 19.0), cos(Time * 4.3 + v.x * 17.0)) * GPx * 2.2 * fz).rgb;"))
rep(J("v * Aspect * 14.0 - vec2(Time * 11.0, Time * 7.0)), FireK);"), J("v * Aspect * 14.0 - vec2(Time * 11.0, Time * 7.0)), fz);"))
# 3. Fewer, surer flame pixels: tongues a bit taller to make up for it.
rep(J("tg *= 0.6 * (1.0 - A0.g)"), J("tg *= 0.9 * (1.0 - A0.g)"))
open(out, "w").write(s); print("ok v166")
