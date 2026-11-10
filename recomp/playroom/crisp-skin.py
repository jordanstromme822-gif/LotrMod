# Crisp skin (Graphics phase 2). Patches a Play Room page. Run it after hd2d-lighting.py when
# that patch is present, and after tools/skin/patch_skin.py when that patch is present.
# It does not edit those scripts.
#
#   python3 crisp-skin.py in.html out.html
#
# Off by default (localStorage rotk-crisp). While off, ScaleFX and the existing skin pass stay
# as they are. While on, ScaleFX is skipped and the picture is a nearest integer scale (4x, or
# 3x if rotk-crisp-scale is "3"). A skin/atlas.png pack, when present, is drawn into that buffer
# with nearest filtering instead of the 3x linear skin pass.
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
glsl = open(os.path.join(HERE, "crisp-skin.glsl"), encoding="utf-8").read()
js = open(os.path.join(HERE, "crisp-skin.js"), encoding="utf-8").read().rstrip("\n")
js = "\n".join(("  " + ln) if ln else "" for ln in js.split("\n"))

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a))
    s = s.replace(a, b)

rep("  function makeSharpHD(gl) {",
    "  const CRISP_GLSL = " + json.dumps(glsl) + ";\n" + js + "\n  function makeSharpHD(gl) {")
rep("const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);",
    "const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);\n"
    "      let crisp = null; try { crisp = crispMake(gl, prog, tex, MVP, blit); } catch (e) { crisp = null; (window.__wideLog || (window.__wideLog = [])).push(\"crisp: \" + (e && e.message || e)); }")
rep("        for (let i = 0; i < (plain ? 0 : 6); i++) {",
    "        const crispS = (!plain && crisp) ? crisp.scale() : 0;\n"
    "        for (let i = 0; i < (plain ? 0 : (crispS ? 1 : 6)); i++) {")

PIC = (
    "        let crispPic = null;\n"
    "        if (crispS) { try { crispPic = crisp.draw(heap, stride, sx, sy, w, h, input, crispS); } catch (e) { crispPic = null; (window.__wideLog || (window.__wideLog = [])).push(\"crisp: \" + (e && e.message || e)); } }\n"
)
SKIN_LINE = '        let hiTex = outs[5]; if (!plain) { try { hiTex = skinPass(heap, stride, sx, sy, w, h, outs[5]); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("skin: " + (e && e.message || e)); SKIN.on = false; } }'
LIT_ANCHOR = "        gl.bindSampler(2, null);\n        let lit = false;"
BARE_BLIT = "        gl.useProgram(blit.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, plain ? input : outs[5]);"
if s.count(SKIN_LINE) == 1:
    rep(SKIN_LINE, PIC +
        '        let hiTex = crispPic || outs[5]; if (!plain && !crispPic) { try { hiTex = skinPass(heap, stride, sx, sy, w, h, outs[5]); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("skin: " + (e && e.message || e)); SKIN.on = false; } }')
elif s.count(LIT_ANCHOR) == 1:
    rep(LIT_ANCHOR, PIC + LIT_ANCHOR)
    rep("gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, outs[5]); gl.uniform1i(fu.Texture, 0);",
        "gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, crispPic || outs[5]); gl.uniform1i(fu.Texture, 0);")
    rep("gl.bindTexture(gl.TEXTURE_2D, plain ? input : outs[5]);",
        "gl.bindTexture(gl.TEXTURE_2D, plain ? input : (crispPic || outs[5]));")
elif s.count(BARE_BLIT) == 1:
    rep(BARE_BLIT, PIC + "        gl.useProgram(blit.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, plain ? input : (crispPic || outs[5]));")
else:
    raise SystemExit("crisp: no picture anchor (skin hiTex, rich-lighting lit, or Sharp HD blit)")

# Glow reads the picture just drawn, so a pack's torches bloom. Off, crispPic is null and this stays outs[0].
GLOW_SRC = "gl.bindTexture(gl.TEXTURE_2D, i ? gT[0] : outs[0]);"
if s.count(GLOW_SRC) == 1:
    rep(GLOW_SRC, "gl.bindTexture(gl.TEXTURE_2D, i ? gT[0] : (crispPic || outs[0]));")

# HD-2D, when this page has it: light the crisp buffer, and read normals while this pass owns the skin hook.
old_present = "outs: outs, gT: gT }"
new_present = "outs: outs, gT: gT, raw: crispPic }"
if s.count(old_present) == 1 and s.count("raw: crispPic") == 0 and s.count("raw: (typeof crispPic") == 0:
    rep(old_present, new_present)
old_raw = "bind(1, env.outs[0], api.lin); if (u.Raw) gl.uniform1i(u.Raw, 1);"
new_raw = "bind(1, env.raw || env.outs[0], api.lin); if (u.Raw) gl.uniform1i(u.Raw, 1);"
if s.count(old_raw) == 1:
    rep(old_raw, new_raw)
old_hook = 'if (localStorage.getItem("rotk-skin") !== "1") return false;'
new_hook = 'if (localStorage.getItem("rotk-skin") !== "1" && !window.__crispHook) return false;'
if s.count(old_hook) == 1:
    rep(old_hook, new_hook)

CHIP = '<button id="crispSetup" class="chip" type="button" style="display:block;margin:8px auto 0" onclick="window.__toggleCrisp&&__toggleCrisp()">Crisp skin: Off</button>\n'
if s.count('<button id="hd2dSetup"') == 1:
    rep('<button id="hd2dSetup"', CHIP + '<button id="hd2dSetup"')
elif s.count('<button id="mapSetup"') == 1:
    rep('<button id="mapSetup"', CHIP + '<button id="mapSetup"')
else:
    raise SystemExit("crisp: no setup-screen chip anchor (hd2dSetup or mapSetup)")
open(out, "w", encoding="utf-8").write(s)
print("patched")
