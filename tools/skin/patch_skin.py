# Adds the skin pass to the Play Room page's makeSharpHD. Usage: patch_skin.py in.html out.html
import sys, json
s = open(sys.argv[1]).read()
glsl = open('/tmp/rc/skintools/skin.glsl').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]; s = s.replace(a, b)
rep('  function makeSharpHD(gl) {', '  const SKIN_GLSL = ' + json.dumps(glsl) + ''';
  // Skin (test, 2026-11-10): known 8x8 tiles drawn from 4x art. The engine tags every pixel with its tile
  // (rotk_skin_slot); the page hashes tile + palette (FNV-1a, as tools cut.py) and looks the art up in the atlas.
  const SKIN = { on: (() => { try { return localStorage.getItem("rotk-skin") === "1"; } catch (e) { return false; } })(), map: null, img: null };
  window.__toggleSkin = () => { SKIN.on = !SKIN.on; try { localStorage.setItem("rotk-skin", SKIN.on ? "1" : "0"); } catch (e) {} const b = document.getElementById("skinSetup"); if (b) b.textContent = "Skin (test): " + (SKIN.on ? "On" : "Off"); };
  (async () => { try {
    const m = await (await fetch("skin/map.json")).json(), img = new Image(); img.src = "skin/atlas.png"; await img.decode();
    SKIN.map = new Map(m.keys.map((k, i) => [k, i + 1])); SKIN.per = m.per; SKIN.img = img;
  } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("skin: " + e); } })();
  function makeSharpHD(gl) {''')
# build program + resources
rep('      const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);', '''      const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);
      let skP = null; try { skP = prog(SKIN_GLSL); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("skin glsl: " + (e && e.message || e)); }
      let skT = null, skOut = null, skFB = null, lutT = null, atlT = null, skW = 0, skH = 0, ep = 0;
      const lut = new Uint16Array(65536), stamp = new Uint32Array(65536);
      const fnv = (u8, a, n) => { let h = 0x811c9dc5; for (let i = 0; i < n; i++) h = Math.imul(h ^ u8[a + i], 0x01000193); return (h >>> 0).toString(16).padStart(8, "0"); };
      const skinPass = (heap, stride, sx, sy, w, h, srcTex) => {
        const M = window.__wideM; if (!skP || !SKIN.on || !SKIN.img || !M || !M._rotk_skin_slot) return srcTex;
        if (!M.__skinOn) { M._rotk_skin(1); M.__skinOn = 1; }
        const ptr = M._rotk_skin_slot(WideHost.front); if (!ptr) return srcTex;
        if (!atlT) { atlT = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, atlT); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 4);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, SKIN.img);
          for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
          lutT = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, lutT); gl.texImage2D(gl.TEXTURE_2D, 0, gl.R16UI, 256, 256, 0, gl.RED_INTEGER, gl.UNSIGNED_SHORT, null);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST); }
        if (skW !== w || skH !== h) {
          if (skT) { gl.deleteTexture(skT); gl.deleteTexture(skOut); gl.deleteFramebuffer(skFB); }
          skW = w; skH = h; skT = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, skT); gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32UI, w, h, 0, gl.RED_INTEGER, gl.UNSIGNED_INT, null);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
          skOut = tex(w * 3, h * 3, "rgba", gl.LINEAR); skFB = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, skFB);
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, skOut, 0);
        }
        // Which atlas cell each (VRAM tile, palette bank) on screen uses, worked out again every picture.
        const u8 = heap, u32 = new Uint32Array(u8.buffer), vr = M._rotk_vram(), pl = M._rotk_pal(), base = ptr >> 2;
        ep = (ep + 1) >>> 0; if (!ep) { stamp.fill(0); ep = 1; }
        for (let y = 0; y < h; y++) for (let i = base + (y + sy) * stride + sx, e = i + w; i < e; i++) {
          const t = u32[i]; if (!(t >>> 31)) continue;
          const li = ((t >>> 12) & 15) * 4096 + (t & 4095); if (stamp[li] === ep) continue; stamp[li] = ep;
          const c256 = (t >>> 16) & 1, obj = (t >>> 25) & 1, slot = t & 4095;
          const k = fnv(u8, vr + slot * 32, c256 ? 64 : 32) + fnv(u8, pl + (obj ? 0x200 : 0) + (c256 ? 0 : ((t >>> 12) & 15) * 32), c256 ? 512 : 32) + c256;
          lut[li] = SKIN.map.get(k) || 0;
        }
        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, lutT); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 2); gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 256, gl.RED_INTEGER, gl.UNSIGNED_SHORT, lut);
        gl.bindTexture(gl.TEXTURE_2D, skT); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 4); gl.pixelStorei(gl.UNPACK_ROW_LENGTH, stride); gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, sx); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, sy);
        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RED_INTEGER, gl.UNSIGNED_INT, u32, base);
        gl.pixelStorei(gl.UNPACK_ROW_LENGTH, 0); gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, 0); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, 0); gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
        const u = skP.u; gl.useProgram(skP.p); gl.bindFramebuffer(gl.FRAMEBUFFER, skFB); gl.viewport(0, 0, w * 3, h * 3);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, srcTex); gl.uniform1i(u.Texture, 0);
        gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, skT); gl.uniform1i(u.Tags, 1);
        gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, lutT); gl.uniform1i(u.Lut, 2);
        gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, atlT); gl.uniform1i(u.Atlas, 3);
        gl.uniformMatrix4fv(u.MVPMatrix, false, MVP); gl.uniform2f(u.GameSize, w, h); gl.uniform2f(u.AtlasSize, SKIN.img.width, SKIN.img.height);
        gl.uniform1f(u.Per, SKIN.per); gl.uniform1f(u.Mix, 1);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        for (const i of [1, 2, 3]) { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, null); }
        gl.activeTexture(gl.TEXTURE0);
        return skOut;
      };''')
rep('''        gl.bindSampler(2, null);
        let lit = false;''', '''        let hiTex = outs[5]; if (!plain) { try { hiTex = skinPass(heap, stride, sx, sy, w, h, outs[5]); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("skin: " + (e && e.message || e)); SKIN.on = false; } }
        gl.bindSampler(2, null);
        let lit = false;''')
rep('gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, outs[5]); gl.uniform1i(fu.Texture, 0);', 'gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, hiTex); gl.uniform1i(fu.Texture, 0);')
rep('gl.bindTexture(gl.TEXTURE_2D, plain ? input : outs[5]);', 'gl.bindTexture(gl.TEXTURE_2D, plain ? input : hiTex);')
# chip on setup screen
rep('<button id="lightSetup"', '<button id="skinSetup" class="chip" type="button" style="display:block;margin:8px auto 0" onclick="window.__toggleSkin&&__toggleSkin()">Skin (test): Off</button>\n<button id="lightSetup"')
open(sys.argv[2], 'w').write(s)
print('ok')
