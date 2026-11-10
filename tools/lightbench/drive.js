const _pn = performance.now.bind(performance);
performance.now = () => (typeof window.__t === "number" ? window.__t * 1000 : _pn());
window.run = async (url, look, night, x, y, w, h, scale, times) => {
  const img = new Image(); img.src = url; await img.decode();
  const cv0 = document.createElement("canvas"); cv0.width = w; cv0.height = h; const c0 = cv0.getContext("2d");
  c0.drawImage(img, -x, -y); const d = c0.getImageData(0, 0, w, h).data;
  const rgb = new Uint8Array(w * h * 3); for (let i = 0; i < w * h; i++) { rgb[i * 3] = d[i * 4]; rgb[i * 3 + 1] = d[i * 4 + 1]; rgb[i * 3 + 2] = d[i * 4 + 2]; }
  const cv = document.getElementById("c"); cv.width = w * scale; cv.height = h * scale;
  const gl = window.__gl || (window.__gl = cv.getContext("webgl2", { preserveDrawingBuffer: true }));
  if (!window.__draw) window.__draw = makeSharpHD(gl);
  if (!window.__draw) return "no draw: " + (window.__wideLog || []).join(" | ");
  window.__rotkNightForce = night; window.__aliveDbg = window.__dbgSet;
  window.__rotkLook = look === "off" ? null : (look in LIGHT_LOOKS.looks ? LIGHT_LOOKS.looks[look] : LIGHT_LOOKS.cycled(+look));
  try { localStorage.setItem("rotk-light", look === "off" ? "0" : "1"); } catch (e) {}
  const out = [];
  gl.finish(); const t0 = Date.now(); for (let i = 0; i < 150; i++) { window.__t = 1 + i * 0.01; window.__draw(rgb, 0, w, 0, 0, w, h, [0, 0, w * scale, h * scale], false); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); } window.__ms = (Date.now() - t0) / 150;
  for (const t of times) { window.__t = t; window.__draw(rgb, 0, w, 0, 0, w, h, [0, 0, w * scale, h * scale], false); out.push(cv.toDataURL("image/png")); }
  return { shots: out, log: (window.__wideLog || []).concat(["ms " + window.__ms]) };
};
