// HD weapons (Graphics phase 6). Off unless localStorage rotk-hdweapons === "1".
// Loads skin/weapons/{map.json,atlas.png,normals.png,material.png} only after the toggle is on.
const HDW = { map: null, img: null, nrm: null, mat: null, tried: 0 };

function hdwOn(){ try { return localStorage.getItem("rotk-hdweapons") === "1"; } catch (e) { return false; } }
function hdwHd2d(){ try { return localStorage.getItem("rotk-hd2d") === "1"; } catch (e) { return false; } }
function hdwLabel(){ const b = document.getElementById("hdwSetup"); if (b) b.textContent = "HD weapons: " + (hdwOn() ? "On" : "Off"); }
function hdwSet(on){ try { localStorage.setItem("rotk-hdweapons", on ? "1" : "0"); } catch (e) {} if (on) hdwLoad(); hdwLabel(); if (on && typeof WideHost !== "undefined") WideHost.fitDue = true; }
window.__toggleHdWeapons = () => hdwSet(!hdwOn());
window.addEventListener("keydown", (e) => {
  const t = e.target;
  if ((e.key === "w" || e.key === "W") && !e.repeat && document.body.classList.contains("playing")
      && !(t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA"))) window.__toggleHdWeapons();
});
window.addEventListener("DOMContentLoaded", hdwLabel);
hdwLabel();

function hdwLoad(){
  if (HDW.tried) return;
  HDW.tried = 1;
  (async () => {
    try {
      const r = await fetch("skin/weapons/map.json");
      if (!r.ok) return;
      const m = await r.json();
      if (!m || !m.tiles) return;
      const load = async (name) => { const im = new Image(); im.src = URL.createObjectURL(await (await fetch("skin/weapons/" + name)).blob()); await im.decode(); return im; };
      HDW.img = await load("atlas.png");
      HDW.nrm = await load("normals.png");
      HDW.mat = await load("material.png");
      HDW.map = m;
    } catch (e) { HDW.map = null; }
  })();
}
if (hdwOn()) hdwLoad();

function hdwDevice(){
  if (typeof WideHost === "undefined" || !WideHost.canvas) return;
  const el = WideHost.canvas, r = (el.parentElement || el).getBoundingClientRect(), d = window.devicePixelRatio || 1;
  const W = Math.max(1, Math.round(r.width * d)), H = Math.max(1, Math.round(r.height * d));
  if (r.width > 0 && r.height > 0 && (el.width !== W || el.height !== H)) { el.width = W; el.height = H; }
}

function hdWeaponsMake(gl, prog, tex, MVP, MVP_FLIP){
  const api = { p: null, near: null, tags: null, lutT: null, atl: null, nrm: null, mat: null, tw: 0, th: 0, lw: 0, lh: 0, ep: 0, em: null, emF: null, emW: 0, emH: 0, noShader: 0 };
  const stamp = new Uint32Array(65536);
  const wlut = new Uint8Array(256 * 256 * 4);
  const log = (e) => { (window.__wideLog || (window.__wideLog = [])).push("hdw: " + (e && e.message || e)); };
  const fnv = (u8, a, n) => { let h = 0x811c9dc5; for (let i = 0; i < n; i++) h = Math.imul(h ^ u8[a + i], 0x01000193); return (h >>> 0).toString(16).padStart(8, "0"); };
  api.nearest = () => {
    if (api.near) return api.near;
    api.near = gl.createSampler();
    gl.samplerParameteri(api.near, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.samplerParameteri(api.near, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.samplerParameteri(api.near, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.samplerParameteri(api.near, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return api.near;
  };
  const shader = () => {
    if (api.p || api.noShader) return api.p;
    try { api.p = prog(HDW_GLSL); return api.p; }
    catch (e) { api.noShader = 1; log(e); return null; }
  };
  const uploadImg = (im, linear) => {
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, linear ? 1 : 0);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, im);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, 0);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    if (linear) {
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.generateMipmap(gl.TEXTURE_2D);
    } else {
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    }
    return t;
  };
  const scan = (heap, off, stride, sx, sy, w, h) => {
    const out = [];
    if (!hdwHd2d() || !heap) return out;
    const at = (x, y) => {
      x = x < 0 ? 0 : x >= w ? w - 1 : x; y = y < 0 ? 0 : y >= h ? h - 1 : y;
      const i = off + ((sy + y) * stride + (sx + x)) * 3;
      return [heap[i], heap[i + 1], heap[i + 2]];
    };
    const yMax = h - (h > 100 ? 34 : 0) - 2;
    for (let y = 2; y < yMax && out.length < 4; y += 8) {
      for (let x = 2; x < w - 2 && out.length < 4; x += 8) {
        const p = at(x, y), mx = Math.max(p[0], p[1], p[2]), mn = Math.min(p[0], p[1], p[2]);
        if (mx < 180 || (mx - mn) / mx < 0.34) continue;
        const s = at(x + 8, y);
        if (Math.abs(p[0] - s[0]) + Math.abs(p[1] - s[1]) + Math.abs(p[2] - s[2]) < 70) continue;
        out.push({ x: x + 0.5, y: y + 0.5, r: 34, k: 0.75, col: [p[0] / mx, p[1] / mx, p[2] / mx] });
      }
    }
    return out;
  };
  api.overlay = (env) => {
    window.__hdWeaponEm = null;
    if (!hdwOn()) return;
    hdwLoad();
    hdwDevice();
    if (!HDW.map || !HDW.img || !shader()) return;
    const M = window.__wideM;
    if (!M || !M._rotk_skin_slot || !M._rotk_vram || !M._rotk_pal) return;
    if (!M.__skinOn) { try { M._rotk_skin(1); M.__skinOn = 1; } catch (e) { return; } }
    const ptr = M._rotk_skin_slot(WideHost.front);
    if (!ptr) return;
    const heap = env.heap, stride = env.stride, sx = env.sx, sy = env.sy, w = env.w, h = env.h;
    if (!api.tags || api.lw !== w || api.lh !== h) {
      if (api.tags) gl.deleteTexture(api.tags);
      api.lw = w; api.lh = h;
      api.tags = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, api.tags);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.R32UI, w, h, 0, gl.RED_INTEGER, gl.UNSIGNED_INT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    }
    if (!api.lutT) {
      api.lutT = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, api.lutT);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, 256, 256, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    }
    if (!api.atl) { api.atl = uploadImg(HDW.img, true); api.nrm = uploadImg(HDW.nrm, true); api.mat = uploadImg(HDW.mat, true); }
    const u8 = heap, u32 = new Uint32Array(u8.buffer), vr = M._rotk_vram(), pl = M._rotk_pal(), base = ptr >> 2;
    const tiles = HDW.map.tiles;
    api.ep = (api.ep + 1) >>> 0; if (!api.ep) { stamp.fill(0); api.ep = 1; }
    const ep = api.ep;
    wlut.fill(0);
    let any = 0;
    for (let y = 0; y < h; y++) for (let i = base + (y + sy) * stride + sx, e = i + w; i < e; i++) {
      const t = u32[i]; if (!(t >>> 31)) continue;
      const li = ((t >>> 12) & 15) * 4096 + (t & 4095); if (stamp[li] === ep) continue; stamp[li] = ep;
      const c256 = (t >>> 16) & 1, obj = (t >>> 25) & 1, slot = t & 4095;
      const k = fnv(u8, vr + slot * 32, c256 ? 64 : 32) + fnv(u8, pl + (obj ? 0x200 : 0) + (c256 ? 0 : ((t >>> 12) & 15) * 32), c256 ? 512 : 32) + c256;
      const cell = tiles[k];
      if (!cell) continue;
      const o = li * 4;
      wlut[o] = (cell[0] + 1) & 255; wlut[o + 1] = (cell[1] + 1) & 255;
      any = 1;
    }
    if (!any) return;
    gl.bindTexture(gl.TEXTURE_2D, api.lutT);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 256, gl.RGBA, gl.UNSIGNED_BYTE, wlut);
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
    const prev = gl.getParameter(gl.FRAMEBUFFER_BINDING);
    const dw = Math.max(1, env.dest[2] | 0), dh = Math.max(1, env.dest[3] | 0);
    if (env.useHd && (!api.em || api.emW !== dw || api.emH !== dh)) {
      if (api.em) { gl.deleteTexture(api.em); gl.deleteFramebuffer(api.emF); }
      api.emW = dw; api.emH = dh;
      api.em = tex(dw, dh, "rgba", gl.LINEAR);
      api.emF = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, api.emF);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, api.em, 0);
    }
    const Ls = scan(heap, env.off || 0, stride, sx, sy, w, h);
    const place = () => {
      if (env.useHd) gl.viewport(0, 0, dw, dh);
      else gl.viewport(env.dest[0], env.ch - env.dest[1] - dh, dw, dh);
    };
    const draw = (mode, target) => {
      gl.bindFramebuffer(gl.FRAMEBUFFER, target);
      if (mode) gl.viewport(0, 0, dw, dh); else place();
      if (mode) { gl.disable(gl.BLEND); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); }
      else { gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); }
      const u = api.p.u;
      gl.useProgram(api.p.p);
      gl.uniformMatrix4fv(u.MVPMatrix, false, env.matrix);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, api.tags); gl.uniform1i(u.Tags, 0);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, api.lutT); gl.uniform1i(u.WLut, 1);
      gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, api.atl); gl.uniform1i(u.Atlas, 2);
      gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, api.nrm); gl.uniform1i(u.Nrm, 3);
      gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, api.mat); gl.uniform1i(u.Mat, 4);
      gl.uniform2f(u.GameSize, w, h);
      gl.uniform2f(u.AtlasSize, HDW.img.width, HDW.img.height);
      gl.uniform1f(u.Cell, HDW.map.cell || 130);
      gl.uniform1f(u.Pad, HDW.map.pad == null ? 1 : HDW.map.pad);
      gl.uniform1f(u.Scale, HDW.map.scale || 16);
      gl.uniform1f(u.Mode, mode);
      gl.uniform3f(u.KeyDir, -0.45, -0.62, 0.72);
      gl.uniform3f(u.KeyCol, 1.0, 0.9, 0.75);
      const lp = u["LPos[0]"] || u.LPos, lc = u["LCol[0]"] || u.LCol;
      const pv = new Float32Array(16), cv = new Float32Array(12);
      for (let i = 0; i < Ls.length && i < 4; i++) {
        const L = Ls[i];
        pv[i * 4] = (L.x || 0) / w; pv[i * 4 + 1] = (L.y || 0) / h; pv[i * 4 + 2] = L.r || 36; pv[i * 4 + 3] = L.k || 0.8;
        const c = L.col || [1, 0.7, 0.4]; cv[i * 3] = c[0]; cv[i * 3 + 1] = c[1]; cv[i * 3 + 2] = c[2];
      }
      if (lp) gl.uniform4fv(lp, pv);
      if (lc) gl.uniform3fv(lc, cv);
      if (u.LN) gl.uniform1f(u.LN, hdwHd2d() ? Math.min(4, Ls.length) : 0);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    };
    if (env.useHd) draw(1, api.emF);
    draw(0, prev);
    gl.disable(gl.BLEND);
    gl.bindSampler(0, null);
    window.__hdWeaponEm = env.useHd ? api.em : null;
  };
  return api;
}
