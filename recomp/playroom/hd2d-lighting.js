// HD-2D lighting runtime (Graphics phase 1). hd2d-lighting.py pastes this into the Play Room
// page ahead of makeSharpHD. Default is off (localStorage rotk-hd2d missing or not "1").
// While it is off the draw path does not compile this shader, allocate a target, or scan for lights.
const HD2D = { normImg: null, map: null, per: 112, cell: 36 };

function hd2dOn(){ try { return localStorage.getItem("rotk-hd2d") === "1"; } catch (e) { return false; } }
function hd2dLabel(){ const b = document.getElementById("hd2dSetup"); if (b) b.textContent = "HD-2D lighting: " + (hd2dOn() ? "On" : "Off"); }
function hd2dSet(on){ try { localStorage.setItem("rotk-hd2d", on ? "1" : "0"); } catch (e) {} hd2dLabel(); }
window.__toggleHd2d = () => hd2dSet(!hd2dOn());
window.addEventListener("keydown", (e) => {
  const t = e.target;
  if ((e.key === "h" || e.key === "H") && !e.repeat && document.body.classList.contains("playing")
      && !(t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA"))) window.__toggleHd2d();
});
window.addEventListener("DOMContentLoaded", hd2dLabel);
hd2dLabel();

function hd2dMenu(){
  try {
    const M = window.__wideM;
    if (!M || !M._rotk_iwram) return 1;
    return M.HEAPU8[M._rotk_iwram() + 0x41B0] === 1 ? 0 : 1;
  } catch (e) { return 1; }
}
function hd2dNum(o, k, d){ const v = o && o[k]; return typeof v === "number" ? v : d; }
function hd2dCol(o, k, d){ const v = o && o[k]; return v && v.length >= 3 ? v : d; }
function hd2dHash(n){ const x = Math.sin(n * 127.1) * 43758.5453; return x - Math.floor(x); }

// Bright, saturated pixels that stand out from their neighbours become lamps. Flat sunlit
// ground fails the neighbour test. A very hot warm core (a brazier, lava) still counts.
function hd2dScan(heap, off, stride, sx, sy, w, h, hudRows){
  const lights = [];
  const yMax = h - (hudRows > 0 ? hudRows : 0) - 2;
  const at = (x, y) => {
    if (x < 0) x = 0; else if (x >= w) x = w - 1;
    if (y < 0) y = 0; else if (y >= h) y = h - 1;
    const i = off + ((sy + y) * stride + (sx + x)) * 3;
    return [heap[i], heap[i + 1], heap[i + 2]];
  };
  for (let y = 2; y < yMax; y += 4) {
    for (let x = 2; x < w - 2; x += 4) {
      const p = at(x, y), r = p[0], g = p[1], b = p[2];
      const mx = r > g ? (r > b ? r : b) : (g > b ? g : b);
      const mn = r < g ? (r < b ? r : b) : (g < b ? g : b);
      if (mx < 168) continue;
      const sat = (mx - mn) / mx;
      if (sat < 0.34) continue;
      const s0 = at(x + 7, y), s1 = at(x - 7, y), s2 = at(x, y + 7), s3 = at(x, y - 7);
      const sr = (s0[0] + s1[0] + s2[0] + s3[0]) * 0.25;
      const sg = (s0[1] + s1[1] + s2[1] + s3[1]) * 0.25;
      const sb = (s0[2] + s1[2] + s2[2] + s3[2]) * 0.25;
      const dr = r - sr, dg = g - sg, db = b - sb;
      const diff = Math.sqrt(dr * dr + dg * dg + db * db) / 255;
      const veryHot = mx > 230 && (r - b) > 30 && sat > 0.25;
      if (diff < 0.16 && !veryHot) continue;
      const score = Math.min(1.4, (mx / 255) * (0.55 + sat) * (veryHot ? 1.15 : 0.75 + diff));
      const colS = Math.max(mx, 1);
      const hit = { x: x + 0.5, y: y + 0.5, r: 22 + Math.min(20, score * 16), k: Math.min(1.15, 0.42 + score * 0.65), col: [r / colS, g / colS, b / colS], ck: score, n: 1 };
      let best = null, bestD = 16 * 16;
      for (let i = 0; i < lights.length; i++) {
        const L = lights[i], dx = L.x - hit.x, dy = L.y - hit.y, d2 = dx * dx + dy * dy;
        if (d2 < bestD) { best = L; bestD = d2; }
      }
      if (best) {
        best.n += 1;
        best.x += (hit.x - best.x) / best.n;
        best.y += (hit.y - best.y) / best.n;
        best.k = Math.min(1.35, best.k + hit.k * 0.25);
        if (hit.r > best.r) best.r = hit.r;
        if (hit.ck > best.ck) { best.col = hit.col; best.ck = hit.ck; }
      } else if (lights.length < 24) lights.push(hit);
    }
  }
  lights.sort((a, b) => b.k - a.k);
  return lights.slice(0, 12);
}

// Motes that stay inside a lamp, plus a few dust specks in the upper air. Not a rising spark
// stream: that already lives in the living-light pass when it is on.
function hd2dParts(lights, w, h){
  if (Array.isArray(window.__hd2dParts)) return window.__hd2dParts.slice(0, 8);
  const t = performance.now() / 1000, parts = [];
  const n = lights.length < 4 ? lights.length : 4;
  for (let i = 0; i < n && parts.length < 4; i++) {
    const L = lights[i];
    const ang = t * 0.85 + i * 2.4;
    const rad = L.r * 0.32;
    const x = L.x + Math.cos(ang) * rad;
    const y = L.y + Math.sin(ang * 0.65) * rad * 0.45 - (3 + (t * 5 + i * 4) % (L.r * 0.45));
    parts.push({ x: x, y: y, r: 2.1, k: 0.62, col: L.col });
  }
  for (let i = 0; i < 4; i++) {
    const s = (i + 1) * 17.13;
    const x = (hd2dHash(s) + t * (0.012 + hd2dHash(s + 1) * 0.015)) % 1;
    const y = hd2dHash(s + 2) * 0.5 + Math.sin(t * 0.2 + i) * 0.015;
    parts.push({ x: x * w, y: y * h, r: 1.6, k: 0.26, col: [0.78, 0.8, 0.86] });
  }
  return parts.slice(0, 8);
}

// Gandalf, same read as the aura pass: hero id 3, object x/y at +0xAE/+0xB2.
function hd2dHero(stride, h, sx, sy, w){
  try {
    if (typeof auraPos !== "function") return null;
    const p = auraPos(stride, h);
    if (!p) return null;
    const x = (p[0] - sx) / w, y = (p[1] - sy) / h;
    if (x < -0.05 || x > 1.05 || y < -0.05 || y > 1.05) return null;
    return [x, y];
  } catch (e) { return null; }
}

(async () => {
  try {
    const r = await fetch("skin/normals.png");
    if (!r.ok) return;
    const img = new Image();
    img.src = URL.createObjectURL(await r.blob());
    await img.decode();
    const m = await (await fetch("skin/map.json")).json();
    if (!m || !m.keys) return;
    HD2D.normImg = img;
    HD2D.map = new Map(m.keys.map((k, i) => [k, i + 1]));
    HD2D.per = m.per || 112;
    HD2D.cell = m.cell || 36;
  } catch (e) {}
})();

function hd2dMake(gl, prog, tex, MVP, MVP_FLIP, blit){
  const api = { bad: 0, said: 0, p: null, fbo: null, col: null, dw: 0, dh: 0, dummy: null, lin: null, near: null, frameTex: null, atlTex: null, tagTex: null, lutTex: null, tagW: 0, tagH: 0, stamp: null, lut: null, ep: 0 };
  const log = (e) => { (window.__wideLog || (window.__wideLog = [])).push("hd2d: " + (e && e.message || e)); };
  const samp = (filter) => {
    const s = gl.createSampler();
    gl.samplerParameteri(s, gl.TEXTURE_MIN_FILTER, filter);
    gl.samplerParameteri(s, gl.TEXTURE_MAG_FILTER, filter);
    gl.samplerParameteri(s, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.samplerParameteri(s, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return s;
  };
  // Nothing is compiled or allocated until the toggle is on.
  api.prepare = () => {
    if (!hd2dOn() || api.bad) return false;
    if (api.p) return true;
    try {
      api.lin = samp(gl.LINEAR);
      api.near = samp(gl.NEAREST);
      api.dummy = tex(1, 1, "rgba", gl.NEAREST);
      api.p = prog(HD2D_GLSL);
      return true;
    } catch (e) { api.bad = 1; log(e); return false; }
  };
  api.begin = (dw, dh) => {
    if (!api.col || api.dw !== dw || api.dh !== dh) {
      if (api.col) { gl.deleteTexture(api.col); gl.deleteFramebuffer(api.fbo); }
      api.dw = dw; api.dh = dh;
      api.col = tex(dw, dh, "rgba", gl.NEAREST);
      api.fbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, api.fbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, api.col, 0);
      if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error("framebuffer");
    }
    return api.fbo;
  };
  const rgba = (img) => {
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return t;
  };
  // Same FNV-1a key as tools/skin/cut.py. Read-only: this does not change the skin tools.
  const fnv = (u8, a, n) => { let h = 0x811c9dc5; for (let i = 0; i < n; i++) h = Math.imul(h ^ u8[a + i], 0x01000193); return (h >>> 0).toString(16).padStart(8, "0"); };
  const uploadAtlas = (heap, stride, sx, sy, w, h) => {
    const M = window.__wideM;
    if (!HD2D.normImg || !HD2D.map || !M || !M._rotk_skin_slot || !M.__skinOn) return false;
    try { if (localStorage.getItem("rotk-skin") !== "1" && !window.__crispHook) return false; } catch (e) { return false; }
    if (!api.atlTex) api.atlTex = rgba(HD2D.normImg);
    const ptr = M._rotk_skin_slot(WideHost.front);
    if (!ptr) return false;
    if (!api.tagTex || api.tagW !== w || api.tagH !== h) {
      if (api.tagTex) gl.deleteTexture(api.tagTex);
      api.tagW = w; api.tagH = h;
      api.tagTex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, api.tagTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    }
    gl.bindTexture(gl.TEXTURE_2D, api.tagTex);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 4);
    gl.pixelStorei(gl.UNPACK_ROW_LENGTH, stride);
    gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, sx);
    gl.pixelStorei(gl.UNPACK_SKIP_ROWS, sy);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, heap, ptr);
    gl.pixelStorei(gl.UNPACK_ROW_LENGTH, 0);
    gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, 0);
    gl.pixelStorei(gl.UNPACK_SKIP_ROWS, 0);
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    if (!api.stamp) { api.stamp = new Uint32Array(65536); api.lut = new Uint8Array(256 * 256 * 4); }
    if (!api.lutTex) {
      api.lutTex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, api.lutTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 256, 256, 0, gl.RGBA, gl.UNSIGNED_BYTE, api.lut);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    }
    const u8 = heap, u32 = new Uint32Array(u8.buffer), vr = M._rotk_vram(), pl = M._rotk_pal(), base = ptr >> 2;
    api.ep = (api.ep + 1) >>> 0; if (!api.ep) { api.stamp.fill(0); api.ep = 1; }
    const lut = api.lut, stamp = api.stamp, ep = api.ep, map = HD2D.map;
    lut.fill(0);
    for (let y = 0; y < h; y++) for (let i = base + (y + sy) * stride + sx, e = i + w; i < e; i++) {
      const t = u32[i]; if (!(t >>> 31)) continue;
      const li = ((t >>> 12) & 15) * 4096 + (t & 4095); if (stamp[li] === ep) continue; stamp[li] = ep;
      const c256 = (t >>> 16) & 1, obj = (t >>> 25) & 1, slot = t & 4095;
      const k = fnv(u8, vr + slot * 32, c256 ? 64 : 32) + fnv(u8, pl + (obj ? 0x200 : 0) + (c256 ? 0 : ((t >>> 12) & 15) * 32), c256 ? 512 : 32) + c256;
      const cell = map.get(k) || 0;
      const o = li * 4; lut[o] = cell & 255; lut[o + 1] = (cell >> 8) & 255;
    }
    gl.bindTexture(gl.TEXTURE_2D, api.lutTex);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 256, gl.RGBA, gl.UNSIGNED_BYTE, lut);
    return true;
  };
  api.blit = (cw, ch, dest) => {
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);
    gl.useProgram(blit.p);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, api.col);
    gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };
  api.present = (env) => {
    const u = api.p.u, menu = hd2dMenu();
    const hudRows = env.h > 100 ? 34 : 0;
    const heroUv = menu ? null : hd2dHero(env.stride, env.h, env.sx, env.sy, env.w);
    let lights = [];
    if (!menu) {
      try { lights = hd2dScan(env.heap, env.off, env.stride, env.sx, env.sy, env.w, env.h, hudRows); }
      catch (e) { lights = []; }
      if (Array.isArray(window.__hd2dLights)) {
        for (let i = 0; i < window.__hd2dLights.length; i++) {
          const L = window.__hd2dLights[i];
          if (!L) continue;
          lights.push({ x: L.x, y: L.y, r: L.r || 28, k: L.k || 0.8, col: L.col || [1, 0.7, 0.4] });
        }
      }
      lights.sort((a, b) => b.k - a.k);
      // Keep one slot for Gandalf's lamp so a screen full of braziers does not crowd him out.
      lights = lights.slice(0, heroUv ? 11 : 12);
      if (heroUv) lights.push({ x: heroUv[0] * env.w, y: heroUv[1] * env.h, r: 46, k: 0.62, col: [0.62, 0.78, 1] });
    }
    const parts = menu ? [] : hd2dParts(lights, env.w, env.h);
    let mode = 0, atlasOn = false;
    const frameImg = window.__hd2dNormalImage;
    if (frameImg) {
      mode = 1;
      if (!api.frameTex || api.frameSrc !== frameImg) { if (api.frameTex) gl.deleteTexture(api.frameTex); api.frameTex = rgba(frameImg); api.frameSrc = frameImg; }
      else if (frameImg.tagName === "CANVAS") {
        gl.bindTexture(gl.TEXTURE_2D, api.frameTex);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, frameImg);
      }
    } else {
      try { atlasOn = uploadAtlas(env.heap, env.stride, env.sx, env.sy, env.w, env.h); } catch (e) { atlasOn = false; }
      if (atlasOn) mode = 2;
    }
    const cur = env.cur || {};
    const Lpos = new Float32Array(12 * 4), Lcol = new Float32Array(12 * 4);
    for (let i = 0; i < lights.length && i < 12; i++) {
      const L = lights[i];
      Lpos[i * 4] = L.x / env.w; Lpos[i * 4 + 1] = L.y / env.h; Lpos[i * 4 + 2] = L.r; Lpos[i * 4 + 3] = L.k;
      Lcol[i * 4] = L.col[0]; Lcol[i * 4 + 1] = L.col[1]; Lcol[i * 4 + 2] = L.col[2];
    }
    const Ppos = new Float32Array(8 * 4), Pcol = new Float32Array(8 * 4);
    for (let i = 0; i < parts.length && i < 8; i++) {
      const P = parts[i];
      Ppos[i * 4] = P.x / env.w; Ppos[i * 4 + 1] = P.y / env.h; Ppos[i * 4 + 2] = P.r || 2; Ppos[i * 4 + 3] = P.k || 0.3;
      const c = P.col || [1, 1, 1]; Pcol[i * 4] = c[0]; Pcol[i * 4 + 1] = c[1]; Pcol[i * 4 + 2] = c[2];
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, env.cw, env.ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.viewport(env.dest[0], env.ch - env.dest[1] - env.dest[3], env.dest[2], env.dest[3]);
    gl.useProgram(api.p.p);
    gl.uniformMatrix4fv(u.MVPMatrix, false, MVP_FLIP);
    const bind = (unit, texId, sampler) => {
      gl.activeTexture(gl.TEXTURE0 + unit);
      gl.bindTexture(gl.TEXTURE_2D, texId || api.dummy);
      gl.bindSampler(unit, sampler || null);
    };
    bind(0, api.col, api.near); gl.uniform1i(u.Texture, 0);
    bind(1, env.raw || env.outs[0], api.lin); if (u.Raw) gl.uniform1i(u.Raw, 1);
    const wem = window.__hdWeaponEm || null;
    bind(6, wem || api.dummy, api.lin); if (u.WeaponEm) gl.uniform1i(u.WeaponEm, 6); if (u.WeaponEmOn) gl.uniform1f(u.WeaponEmOn, wem ? 1 : 0);
    const glow = env.lit && env.gT && env.gT[1];
    bind(2, glow || api.dummy, api.lin); if (u.Glow) gl.uniform1i(u.Glow, 2);
    bind(3, mode === 1 ? api.frameTex : mode === 2 ? api.atlTex : api.dummy, api.near); if (u.Normals) gl.uniform1i(u.Normals, 3);
    bind(4, mode === 2 ? api.tagTex : api.dummy, api.near); if (u.Tags) gl.uniform1i(u.Tags, 4);
    bind(5, mode === 2 ? api.lutTex : api.dummy, api.near); if (u.Lut) gl.uniform1i(u.Lut, 5);
    if (u.FogCol) gl.uniform3fv(u.FogCol, hd2dCol(cur, "FogCol", [0.08, 0.09, 0.12]));
    if (u.NightTint) gl.uniform3fv(u.NightTint, hd2dCol(cur, "NightTint", [0.4, 0.48, 0.62]));
    const f1 = (name, v) => { if (u[name]) gl.uniform1f(u[name], v); };
    f1("Night", hd2dNum(cur, "Night", 0));
    f1("Sun", hd2dNum(cur, "Sun", 0.1));
    f1("Fog", hd2dNum(cur, "Fog", 0));
    f1("Vig", hd2dNum(cur, "Vig", 0.22));
    f1("Time", (performance.now() / 1000) % 600);
    f1("HudY", env.hudY);
    f1("Menu", menu);
    f1("Already", env.lit ? 1 : 0);
    f1("GlowOn", glow ? 1 : 0);
    f1("NMode", mode);
    f1("ShadowCut", (env.lit && typeof cur.ShadeK === "number" && cur.ShadeK > 0.15 && !window.__aliveOff) ? 1 : 0);
    f1("HeroK", heroUv ? 1 : 0);
    f1("LN", lights.length);
    f1("PN", parts.length);
    f1("Dbg", window.__hd2dDbg ? 1 : 0);
    f1("Cell", HD2D.cell || 36);
    f1("Pad", 2);
    f1("Per", HD2D.per || 112);
    if (u.GPx) gl.uniform2f(u.GPx, 1 / env.w, 1 / env.h);
    if (u.GameSize) gl.uniform2f(u.GameSize, env.w, env.h);
    if (u.AtlasSize) gl.uniform2f(u.AtlasSize, HD2D.normImg ? HD2D.normImg.width : 1, HD2D.normImg ? HD2D.normImg.height : 1);
    if (u.HeroP) gl.uniform2f(u.HeroP, heroUv ? heroUv[0] : 0, heroUv ? heroUv[1] : 0);
    const lp = u["LPos[0]"] || u.LPos; if (lp) gl.uniform4fv(lp, Lpos);
    const lc = u["LCol[0]"] || u.LCol; if (lc) gl.uniform4fv(lc, Lcol);
    const pp = u["PPos[0]"] || u.PPos; if (pp) gl.uniform4fv(pp, Ppos);
    const pc = u["PCol[0]"] || u.PCol; if (pc) gl.uniform4fv(pc, Pcol);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    for (let i = 0; i < 6; i++) { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, null); gl.bindSampler(i, null); }
    gl.activeTexture(gl.TEXTURE0);
  };
  return api;
}
