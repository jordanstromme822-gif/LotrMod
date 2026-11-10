import sys
p = sys.argv[1]; s = open(p).read()
light = open('rich-lighting-shaders.js').read(); looks = open('rich-lighting-looks.js').read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a)); s = s.replace(a, b)
rep("  function makeSharpHD(gl) {\n    try {\n", looks + light + "  function makeSharpHD(gl) {\n    try {\n")
rep("const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);",
    "const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);\n      let glowP = null, finP = null, linS = null;\n      try { glowP = prog(LIGHT_GLOW); finP = prog(LIGHT_FINAL); linS = gl.createSampler(); gl.samplerParameteri(linS, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.samplerParameteri(linS, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.samplerParameteri(linS, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.samplerParameteri(linS, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); }\n      catch (e) { glowP = null; (window.__wideLog || (window.__wideLog = [])).push(\"light: \" + (e && e.message || e)); }\n      const cur = JSON.parse(JSON.stringify(LIGHT_LOOKS.looks.menu));\n      const ease = () => { const t = window.__rotkLook || LIGHT_LOOKS.looks.menu; for (const k in cur) { if (Array.isArray(cur[k])) for (let j = 0; j < 3; j++) cur[k][j] += (t[k][j] - cur[k][j]) * 0.06; else cur[k] += (t[k] - cur[k]) * 0.06; } };")
rep("let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0;", "let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0, gT = [], gF = [];")
rep("""        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      };
      // heap:""", """        for (const t of gT) gl.deleteTexture(t); for (const f of gF) gl.deleteFramebuffer(f); gT = []; gF = [];
        if (glowP) for (let i = 0; i < 2; i++) {
          const t = tex(w, h, "rgba", gl.LINEAR), fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0); gT.push(t); gF.push(fb);
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      };
      // heap:""")
rep("""        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;""", """        let lit = false; try { lit = !plain && !!glowP && localStorage.getItem("rotk-light") !== "0"; } catch (e) { lit = !plain && !!glowP; }
        if (lit) {
          ease();
          // Glow + wide shadow map: bright pixels blurred across and down at game size, luma blur kept in alpha.
          gl.useProgram(glowP.p); const gu = glowP.u;
          for (let i = 0; i < 2; i++) {
            gl.bindFramebuffer(gl.FRAMEBUFFER, gF[i]); gl.viewport(0, 0, w, h);
            gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, i ? gT[0] : outs[0]); gl.bindSampler(0, linS);
            gl.uniform1i(gu.Texture, 0); gl.uniformMatrix4fv(gu.MVPMatrix, false, MVP); gl.uniform2f(gu.TextureSize, w, h);
            gl.uniform2f(gu.Dir, i ? 0 : 2.2, i ? 2.2 : 0); gl.uniform1i(gu.Extract, i ? 0 : 1); gl.uniform1f(gu.Thr, cur.Thr);
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
          }
          gl.bindSampler(0, null);
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;""")
rep("""        gl.useProgram(blit.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, plain ? input : outs[5]);
        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);""", """        if (lit) {
          const fu = finP.u; gl.useProgram(finP.p);
          gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, gT[1]); gl.uniform1i(fu.Glow, 1);
          gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, outs[5]); gl.uniform1i(fu.Texture, 0);
          gl.uniformMatrix4fv(fu.MVPMatrix, false, MVP_FLIP);
          for (const k of ["ShadowTint", "HiTint", "GlowTint", "FogCol", "Gain"]) if (fu[k]) gl.uniform3fv(fu[k], cur[k]);
          for (const k of ["Sat", "GlowK", "Clarity", "Vig", "Fog", "Lift", "Amount", "Sun", "Relief"]) if (fu[k]) gl.uniform1f(fu[k], cur[k]);
          if (fu.Px) gl.uniform2f(fu.Px, 1.2 / w, 1.2 / h);
        } else {
        gl.useProgram(blit.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, plain ? input : outs[5]);
        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);
        }""")
open(sys.argv[2], 'w').write(s)
print("patched")
