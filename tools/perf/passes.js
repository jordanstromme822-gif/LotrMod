(() => {
  const P = WebGL2RenderingContext.prototype; const st = window.__pass = { on: false, m: new Map(), lab: new Map() };
  const oCS = P.createShader, oUse = P.useProgram, oDraw = P.drawArrays, oVp = P.viewport, oSrc = P.shaderSource, oAtt = P.attachShader, oFin = P.finish, oTsub = P.texSubImage2D, oBF = P.bindFramebuffer;
  P.createShader = function (t) { const s = oCS.call(this, t); if (s) s.__frag = t === 0x8B30; return s; };
  P.shaderSource = function (s, t) { s.__t = t; return oSrc.call(this, s, t); };
  P.attachShader = function (pg, s) { if (s.__frag && s.__t) { let t = s.__t; const i = t.indexOf('void main'); const u = (t.match(/uniform\s+\w+\s+(\w+)/g) || []).map(x => x.split(/\s+/).pop()).join(','); st.lab.set(pg, 'L' + t.length + '[' + u.slice(0, 80) + ']'); } return oAtt.call(this, pg, s); };
  P.useProgram = function (pg) { this.__pg = pg; return oUse.call(this, pg); };
  P.viewport = function (x, y, w, h) { this.__vp = w + 'x' + h; return oVp.call(this, x, y, w, h); };
  const px = new Uint8Array(4), pf = new Float32Array(4); const sync = (gl) => { const e = gl.getError(); try { gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); if (gl.getError()) gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.FLOAT, pf); gl.getError(); } catch (x) {} };
  const rec = (k, t) => { const e = st.m.get(k) || [0, 0]; e[0] += t; e[1]++; st.m.set(k, e); };
  P.texSubImage2D = function () { if (!st.on) return oTsub.apply(this, arguments); oFin.call(this); const t = performance.now(); const r = oTsub.apply(this, arguments); oFin.call(this); rec('texSub ' + arguments[4] + 'x' + arguments[5], performance.now() - t); return r; };
  P.drawArrays = function (a, b, c) { if (!st.on) return oDraw.call(this, a, b, c); sync(this); const t = performance.now(); oDraw.call(this, a, b, c); sync(this); rec((st.lab.get(this.__pg) || '?') + ' @' + this.__vp, performance.now() - t); };
  window.__passDump = () => [...st.m].sort((x, y) => y[1][0] - x[1][0]).map(([k, [t, n]]) => (t / n).toFixed(2).padStart(7) + ' ms x' + n + '  ' + k).join('\n');
})();
