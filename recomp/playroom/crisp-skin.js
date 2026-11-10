// Crisp skin runtime (Graphics phase 2). crisp-skin.py pastes this ahead of makeSharpHD.
// Off unless localStorage rotk-crisp === "1". While it is off, ScaleFX and the old skin pass are untouched.
const CRISP = { img: null, map: null, per: 112 };

function crispOn(){ try { return localStorage.getItem("rotk-crisp") === "1"; } catch (e) { return false; } }
function crispLabel(){ const b = document.getElementById("crispSetup"); if (b) b.textContent = "Crisp skin: " + (crispOn() ? "On" : "Off"); }
function crispSet(on){ try { localStorage.setItem("rotk-crisp", on ? "1" : "0"); } catch (e) {} crispLabel(); }
window.__toggleCrisp = () => crispSet(!crispOn());
window.addEventListener("keydown", (e) => {
  const t = e.target;
  if ((e.key === "k" || e.key === "K") && !e.repeat && document.body.classList.contains("playing")
      && !(t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA"))) window.__toggleCrisp();
});
window.addEventListener("DOMContentLoaded", crispLabel);
crispLabel();

// 4x matches the atlas (one authored texel per output pixel). 3x is the smaller nearest scale.
function crispMul(){
  if (!crispOn()) return 0;
  try { if (localStorage.getItem("rotk-crisp-scale") === "3" || window.__crispScale === 3) return 3; } catch (e) {}
  return 4;
}

(async () => {
  try {
    const r = await fetch("skin/atlas.png");
    if (!r.ok) return;
    const img = new Image();
    img.src = URL.createObjectURL(await r.blob());
    await img.decode();
    const m = await (await fetch("skin/map.json")).json();
    if (!m || !m.keys) return;
    CRISP.img = img;
    CRISP.map = new Map(m.keys.map((k, i) => [k, i + 1]));
    CRISP.per = m.per || 112;
  } catch (e) {}
})();

function crispMake(gl, prog, tex, MVP, blit){
  const api = { p: null, col: null, fbo: null, tw: 0, th: 0, tags: null, lutT: null, atl: null, noInt: 0, noShader: 0, lw: 0, lh: 0, ep: 0 };
  const lut = new Uint16Array(65536), stamp = new Uint32Array(65536);
  const log = (e) => { (window.__wideLog || (window.__wideLog = [])).push("crisp: " + (e && e.message || e)); };
  const fnv = (u8, a, n) => { let h = 0x811c9dc5; for (let i = 0; i < n; i++) h = Math.imul(h ^ u8[a + i], 0x01000193); return (h >>> 0).toString(16).padStart(8, "0"); };
  api.scale = () => crispMul();
  const ensure = (tw, th) => {
    if (api.col && api.tw === tw && api.th === th) return;
    if (api.col) { gl.deleteTexture(api.col); gl.deleteFramebuffer(api.fbo); }
    api.tw = tw; api.th = th;
    api.col = tex(tw, th, "rgba", gl.NEAREST);
    api.fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, api.fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, api.col, 0);
    if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error("framebuffer");
  };
  const blitNearest = (src, tw, th) => {
    gl.bindFramebuffer(gl.FRAMEBUFFER, api.fbo);
    gl.viewport(0, 0, tw, th);
    gl.disable(gl.BLEND);
    gl.bindSampler(0, null);
    gl.useProgram(blit.p);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, src);
    gl.uniform1i(blit.u.Texture, 0);
    gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };
  const shader = () => {
    if (api.p || api.noShader) return api.p;
    try { api.p = prog(CRISP_GLSL); return api.p; }
    catch (e) { api.noShader = 1; log(e); return null; }
  };
  const ints = (w, h) => {
    if (api.noInt) return false;
    if (api.tags && api.lw === w && api.lh === h && api.lutT && api.atl) return true;
    while (gl.getError()) {}
    if (!api.atl && CRISP.img) {
      api.atl = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, api.atl);
      gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, CRISP.img);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    }
    if (!api.lutT) {
      api.lutT = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, api.lutT);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.R16UI, 256, 256, 0, gl.RED_INTEGER, gl.UNSIGNED_SHORT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    }
    if (!api.tags || api.lw !== w || api.lh !== h) {
      if (api.tags) gl.deleteTexture(api.tags);
      api.lw = w; api.lh = h;
      api.tags = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, api.tags);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32UI, w, h, 0, gl.RED_INTEGER, gl.UNSIGNED_INT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    }
    if (gl.getError() !== gl.NO_ERROR) { api.noInt = 1; return false; }
    return !!(api.atl && api.lutT && api.tags);
  };
  // Same key as tools/skin/cut.py. Read-only: the skin tools are not modified.
  const composite = (heap, stride, sx, sy, w, h, src, tw, th) => {
    const M = window.__wideM;
    if (!CRISP.img || !CRISP.map || !M || !M._rotk_skin_slot || !shader() || !ints(w, h)) return false;
    if (!M.__skinOn) { M._rotk_skin(1); M.__skinOn = 1; }
    const ptr = M._rotk_skin_slot(WideHost.front);
    if (!ptr) return false;
    const u8 = heap, u32 = new Uint32Array(u8.buffer), vr = M._rotk_vram(), pl = M._rotk_pal(), base = ptr >> 2;
    api.ep = (api.ep + 1) >>> 0; if (!api.ep) { stamp.fill(0); api.ep = 1; }
    const ep = api.ep;
    for (let y = 0; y < h; y++) for (let i = base + (y + sy) * stride + sx, e = i + w; i < e; i++) {
      const t = u32[i]; if (!(t >>> 31)) continue;
      const li = ((t >>> 12) & 15) * 4096 + (t & 4095); if (stamp[li] === ep) continue; stamp[li] = ep;
      const c256 = (t >>> 16) & 1, obj = (t >>> 25) & 1, slot = t & 4095;
      const k = fnv(u8, vr + slot * 32, c256 ? 64 : 32) + fnv(u8, pl + (obj ? 0x200 : 0) + (c256 ? 0 : ((t >>> 12) & 15) * 32), c256 ? 512 : 32) + c256;
      let cell = CRISP.map.get(k) || 0;
      if (cell && window.__rotkAnimCell) { const alt = window.__rotkAnimCell(k, cell); if (alt) cell = alt; }
      lut[li] = cell;
    }
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, api.lutT);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 2);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 256, gl.RED_INTEGER, gl.UNSIGNED_SHORT, lut);
    gl.bindTexture(gl.TEXTURE_2D, api.tags);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 4);
    gl.pixelStorei(gl.UNPACK_ROW_LENGTH, stride);
    gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, sx);
    gl.pixelStorei(gl.UNPACK_SKIP_ROWS, sy);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RED_INTEGER, gl.UNSIGNED_INT, u32, base);
    gl.pixelStorei(gl.UNPACK_ROW_LENGTH, 0);
    gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, 0);
    gl.pixelStorei(gl.UNPACK_SKIP_ROWS, 0);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    const u = api.p.u;
    gl.useProgram(api.p.p);
    gl.bindFramebuffer(gl.FRAMEBUFFER, api.fbo);
    gl.viewport(0, 0, tw, th);
    gl.disable(gl.BLEND);
    gl.bindSampler(0, null);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, src); gl.uniform1i(u.Texture, 0);
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, api.tags); gl.uniform1i(u.Tags, 1);
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, api.lutT); gl.uniform1i(u.Lut, 2);
    gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, api.atl); gl.uniform1i(u.Atlas, 3);
    gl.uniformMatrix4fv(u.MVPMatrix, false, MVP);
    gl.uniform2f(u.GameSize, w, h);
    gl.uniform2f(u.AtlasSize, CRISP.img.width, CRISP.img.height);
    gl.uniform1f(u.Per, CRISP.per);
    gl.uniform1f(u.Mix, 1);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    for (let i = 1; i <= 3; i++) { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, null); }
    gl.activeTexture(gl.TEXTURE0);
    return true;
  };
  api.draw = (heap, stride, sx, sy, w, h, src, scale) => {
    window.__crispHook = 0;
    const tw = w * scale, th = h * scale;
    ensure(tw, th);
    try {
      if (composite(heap, stride, sx, sy, w, h, src, tw, th)) { window.__crispHook = 1; return api.col; }
    } catch (e) { log(e); }
    blitNearest(src, tw, th);
    return api.col;
  };
  return api;
}
