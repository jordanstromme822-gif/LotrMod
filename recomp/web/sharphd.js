  // Sharp HD for the wide view (Jordan, 2026-11-07: "Upgrade graphics"): the same passes as Classic's picture
  // (our scene pass, then ScaleFX at 3x), run here with WebGL2 because this engine draws its own pictures.
  // Returns null when the phone can't run it; the caller then draws plain pixels.
  function makeSharpHD(gl) {
    try {
      const src = {}; for (const r of SCALEFX_PRESET.resources) src[r.name] = r.type === "base64" ? atob(r.value) : r.value;
      src["rotk-enhance.glsl"] = ROTK_ENHANCE_GLSL;
      const order = ["rotk-enhance.glsl", "scalefx-pass0.glsl", "scalefx-pass1.glsl", "scalefx-pass2.glsl", "scalefx-pass3.glsl", "scalefx-pass4.glsl"];
      const floatFB = !!gl.getExtension("EXT_color_buffer_float") || !!gl.getExtension("EXT_color_buffer_half_float");
      const sh = (type, text) => { const s = gl.createShader(type); gl.shaderSource(s, text); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
      const prog = (text) => {
        const body = text.replace(/^\s*#version[^\n]*\n/, "").replace(/uniform\s+COMPAT_PRECISION\s+/g, "uniform highp ");
        const p = gl.createProgram();
        gl.attachShader(p, sh(gl.VERTEX_SHADER, "#version 300 es\n#define VERTEX\n" + body));
        gl.attachShader(p, sh(gl.FRAGMENT_SHADER, "#version 300 es\n#define FRAGMENT\n" + body));
        gl.bindAttribLocation(p, 0, "VertexCoord"); gl.bindAttribLocation(p, 1, "TexCoord");
        gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
        const u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
        for (let i = 0; i < n; i++) { const a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); }
        return { p, u };
      };
      const BLIT = "#if defined(VERTEX)\nin vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;\nvoid main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }\n#else\nprecision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture;\nvoid main(){ o = vec4(texture(Texture, v).rgb, 1.0); }\n#endif\n";
      const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);
      const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), gl.STATIC_DRAW);
      const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
      for (const loc of [0, 1]) { gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0); }
      const MVP = new Float32Array([2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, -1, -1, 0, 1]);
      const MVP_FLIP = new Float32Array([2, 0, 0, 0, 0, -2, 0, 0, 0, 0, 1, 0, -1, 1, 0, 1]);
      const tex = (w, h, fmt, filter) => {
        const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
        const f = { rgb: [gl.RGB8, gl.RGB, gl.UNSIGNED_BYTE], rgba: [gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE], float: [gl.RGBA16F, gl.RGBA, gl.HALF_FLOAT] }[fmt];
        gl.texImage2D(gl.TEXTURE_2D, 0, f[0], w, h, 0, f[1], f[2], null);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        return t;
      };
      let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0;
      const setup = (w, h) => {
        for (const t of outs) gl.deleteTexture(t); for (const f of fbs) gl.deleteFramebuffer(f); if (input) gl.deleteTexture(input);
        W = w; Hh = h; input = tex(w, h, "rgb", gl.NEAREST); outs = []; fbs = [];
        for (let i = 0; i < 6; i++) {
          const k = i === 5 ? 3 : 1, fl = (i === 1 || i === 2) && floatFB;
          const t = tex(w * k, h * k, fl ? "float" : "rgba", i === 5 ? gl.LINEAR : gl.NEAREST);
          const fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
          if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error("framebuffer " + i);
          outs.push(t); fbs.push(fb);
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      };
      // heap: bytes holding RGB888 rows of width `stride`; (sx, sy, w, h) is the part to show; dest is the
      // rectangle on the 960x720 canvas (top-left origin).
      return function draw(heap, off, stride, sx, sy, w, h, dest) {
        if (gl.isContextLost()) return;
        if (w !== W || h !== Hh) setup(w, h);
        gl.bindVertexArray(vao); gl.disable(gl.BLEND); gl.disable(gl.DEPTH_TEST);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, input);
        gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1); gl.pixelStorei(gl.UNPACK_ROW_LENGTH, stride);
        gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, sx); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, sy);
        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RGB, gl.UNSIGNED_BYTE, heap, off);
        gl.pixelStorei(gl.UNPACK_ROW_LENGTH, 0); gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, 0); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, 0);
        frame++;
        let srcTex = input;
        for (let i = 0; i < 6; i++) {
          const P = passes[i], u = P.u, k = i === 5 ? 3 : 1;
          gl.useProgram(P.p); gl.bindFramebuffer(gl.FRAMEBUFFER, fbs[i]); gl.viewport(0, 0, w * k, h * k);
          gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, srcTex);
          if (u.Texture) gl.uniform1i(u.Texture, 0);
          if (u.MVPMatrix) gl.uniformMatrix4fv(u.MVPMatrix, false, MVP);
          if (u.TextureSize) gl.uniform2f(u.TextureSize, w, h);
          if (u.InputSize) gl.uniform2f(u.InputSize, w, h);
          if (u.OutputSize) gl.uniform2f(u.OutputSize, w * k, h * k);
          if (u.FrameCount) gl.uniform1i(u.FrameCount, frame);
          if (u.FrameDirection) gl.uniform1i(u.FrameDirection, 1);
          // In the preset, pass 3 reads pass 1's output (PassPrev2) and pass 5 reads pass 0's output (PassPrev5).
          const prev = i === 3 ? ["PassPrev2Texture", outs[1]] : i === 5 ? ["PassPrev5Texture", outs[0]] : null;
          if (prev && u[prev[0]]) {
            gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, prev[1]); gl.uniform1i(u[prev[0]], 1);
            const n = prev[0].replace("Texture", "");
            if (u[n + "TextureSize"]) gl.uniform2f(u[n + "TextureSize"], w, h);
            if (u[n + "InputSize"]) gl.uniform2f(u[n + "InputSize"], w, h);
          }
          gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
          srcTex = outs[i];
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;
        gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);
        gl.useProgram(blit.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, outs[5]);
        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      };
    } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("sharp: " + (e && e.message || e)); return null; }
  }
