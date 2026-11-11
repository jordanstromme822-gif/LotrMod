# HD weapons (Graphics phase 6). Patches a Play Room page. Off by default.
# Run after hd2d-lighting.py and crisp-skin.py when those patches are on the page.
#
#   python3 hd-weapons.py in.html out.html
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
glsl = open(os.path.join(HERE, "hd-weapons.glsl"), encoding="utf-8").read()
js = open(os.path.join(HERE, "hd-weapons.js"), encoding="utf-8").read().rstrip("\n")
js = "\n".join(("  " + ln) if ln else "" for ln in js.split("\n"))

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a))
    s = s.replace(a, b)

if s.count("function hdwOn()") == 0:
    rep("  function makeSharpHD(gl) {",
        "  const HDW_GLSL = " + json.dumps(glsl) + ";\n" + js + "\n  function makeSharpHD(gl) {")
if s.count("hdWeaponsMake(") == 0:
    rep("blit = prog(BLIT);",
        "blit = prog(BLIT);\n      let hdW = null; try { hdW = hdWeaponsMake(gl, prog, tex, MVP, MVP_FLIP); } catch (e) { hdW = null; (window.__wideLog || (window.__wideLog = [])).push(\"hdw: \" + (e && e.message || e)); }")

DRAW = (
    "        if (useHd) { const mu = (lit && finP ? finP.u : blit.u).MVPMatrix; if (mu) gl.uniformMatrix4fv(mu, false, MVP); }\n"
    "        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);\n"
    "        if (useHd) { try { hd.present("
)
DRAW2 = (
    "        if (useHd) { const mu = (lit && finP ? finP.u : blit.u).MVPMatrix; if (mu) gl.uniformMatrix4fv(mu, false, MVP); }\n"
    "        if (hdW && hdwOn()) gl.bindSampler(0, hdW.nearest());\n"
    "        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);\n"
    "        if (hdW) gl.bindSampler(0, null);\n"
    "        if (hdW) { try { hdW.overlay({ heap: heap, off: off, stride: stride, sx: sx, sy: sy, w: w, h: h, dest: dest, ch: ch, useHd: !!(typeof useHd !== \"undefined\" && useHd), matrix: (typeof useHd !== \"undefined\" && useHd) ? MVP : MVP_FLIP }); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push(\"hdw: \" + (e && e.message || e)); } }\n"
    "        if (useHd) { try { hd.present("
)
if s.count(DRAW) == 1:
    rep(DRAW, DRAW2)
elif s.count("hdW.overlay(") != 1:
    raise SystemExit("hdw: final draw anchor not found")

# HD-2D bloom reads weapon emissive when that shader is already in the page.
OLD_U = "uniform sampler2D Texture, Raw, Glow, Normals, Tags, Lut;"
NEW_U = "uniform sampler2D Texture, Raw, Glow, Normals, Tags, Lut, WeaponEm; uniform float WeaponEmOn;"
if s.count(OLD_U) == 1:
    rep(OLD_U, NEW_U)
# json.dumps stores the shader with backslash-n newlines.
MARK = "vec3 we = textureLod(WeaponEm, uv, 0.0).rgb;"
OLD_BLOOM = "c += b * 0.2 * em * 0.2;\\n    }\\n  }"
NEW_BLOOM = ("c += b * 0.2 * em * 0.2;\\n    }\\n    if (WeaponEmOn > 0.5) {\\n"
            "      vec3 we = textureLod(WeaponEm, uv, 0.0).rgb;\\n"
            "      we += textureLod(WeaponEm, uv + vec2(GPx.x * 3.0, 0.0), 0.0).rgb + textureLod(WeaponEm, uv - vec2(GPx.x * 3.0, 0.0), 0.0).rgb;\\n"
            "      we += textureLod(WeaponEm, uv + vec2(0.0, GPx.y * 3.0), 0.0).rgb + textureLod(WeaponEm, uv - vec2(0.0, GPx.y * 3.0), 0.0).rgb;\\n"
            "      c += we * 0.28;\\n    }\\n  }")
if s.count(MARK) == 0 and s.count(OLD_BLOOM) == 1:
    rep(OLD_BLOOM, NEW_BLOOM)
OLD_BIND = "bind(1, env.raw || env.outs[0], api.lin); if (u.Raw) gl.uniform1i(u.Raw, 1);"
NEW_BIND = OLD_BIND + "\n    const wem = window.__hdWeaponEm || null;\n    bind(6, wem || api.dummy, api.lin); if (u.WeaponEm) gl.uniform1i(u.WeaponEm, 6); if (u.WeaponEmOn) gl.uniform1f(u.WeaponEmOn, wem ? 1 : 0);"
if s.count(OLD_BIND) == 1 and s.count("__hdWeaponEm") == 0:
    rep(OLD_BIND, NEW_BIND)

CHIP = '<button id="hdwSetup" class="chip" type="button" style="display:block;margin:8px auto 0" onclick="window.__toggleHdWeapons&&__toggleHdWeapons()">HD weapons: Off</button>\n'
if s.count('<button id="crispSetup"') == 1:
    rep('<button id="crispSetup"', CHIP + '<button id="crispSetup"')
elif s.count('<button id="hd2dSetup"') == 1:
    rep('<button id="hd2dSetup"', CHIP + '<button id="hd2dSetup"')
elif s.count('<button id="mapSetup"') == 1:
    rep('<button id="mapSetup"', CHIP + '<button id="mapSetup"')
else:
    raise SystemExit("hdw: no setup chip anchor")
open(out, "w", encoding="utf-8").write(s)
print("patched")
