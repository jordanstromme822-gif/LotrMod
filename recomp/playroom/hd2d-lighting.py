# HD-2D lighting (Graphics phase 1). Patches a Play Room page that already has the v162 stack
# (rich lighting, moods, day/night, Gandalf's aura). Run it after those, and after alive.py if
# that patch is present: it does not rewrite their shader strings.
#
#   python3 hd2d-lighting.py in.html out.html
#
# Adds an off-by-default setup chip ("HD-2D lighting", key H, localStorage rotk-hd2d).
# While the toggle is off the new pass is not compiled and the existing picture path is unchanged.
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
p, out = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
glsl = open(os.path.join(HERE, "hd2d-lighting.glsl"), encoding="utf-8").read()
js = open(os.path.join(HERE, "hd2d-lighting.js"), encoding="utf-8").read().rstrip("\n")
js = "\n".join(("  " + ln) if ln else "" for ln in js.split("\n"))

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a))
    s = s.replace(a, b)

rep("  function makeSharpHD(gl) {",
    "  const HD2D_GLSL = " + json.dumps(glsl) + ";\n" + js + "\n  function makeSharpHD(gl) {")
rep("      let glowP = null, finP = null, linS = null;",
    "      let glowP = null, finP = null, linS = null;\n"
    "      let hd = null; try { hd = hd2dMake(gl, prog, tex, MVP, MVP_FLIP, blit); } catch (e) { hd = null; (window.__wideLog || (window.__wideLog = [])).push(\"hd2d: \" + (e && e.message || e)); }")
rep("""        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;
        gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);""",
    """        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;
        let useHd = !!(hd && !plain && dest[2] > 1 && dest[3] > 1 && hd.prepare());
        if (useHd) {
          try {
            gl.bindFramebuffer(gl.FRAMEBUFFER, hd.begin(dest[2], dest[3]));
            gl.viewport(0, 0, dest[2], dest[3]);
            gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
          } catch (e) { useHd = false; hd.bad = 1; (window.__wideLog || (window.__wideLog = [])).push("hd2d: " + (e && e.message || e)); }
        }
        if (!useHd) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);
        }""")
rep("""        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);
        }
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);""",
    """        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);
        }
        if (useHd) { const mu = (lit && finP ? finP.u : blit.u).MVPMatrix; if (mu) gl.uniformMatrix4fv(mu, false, MVP); }
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        if (useHd) { try { hd.present({ cw: cw, ch: ch, dest: dest, w: w, h: h, hudY: hudY, lit: lit, cur: cur, heap: heap, off: off, stride: stride, sx: sx, sy: sy, outs: outs, gT: gT, raw: (typeof crispPic !== "undefined" ? crispPic : null) }); } catch (e) { if (!hd.said) { hd.said = 1; (window.__wideLog || (window.__wideLog = [])).push("hd2d: " + (e && e.message || e)); } hd.bad = 1; try { hd.blit(cw, ch, dest); } catch (e2) {} } }""")
CHIP = '<button id="hd2dSetup" class="chip" type="button" style="display:block;margin:8px auto 0" onclick="window.__toggleHd2d&&__toggleHd2d()">HD-2D lighting: Off</button>\n'
if s.count('<button id="lightSetup"') == 1:
    rep('<button id="lightSetup"', CHIP + '<button id="lightSetup"')
elif s.count('<button id="mapSetup"') == 1:
    rep('<button id="mapSetup"', CHIP + '<button id="mapSetup"')
else:
    raise SystemExit("hd2d: no setup-screen chip anchor (lightSetup or mapSetup)")
open(out, "w", encoding="utf-8").write(s)
print("patched")
