// node perf.js <harnessdir> <map png> x y w h outW outH  -> ms per draw for each graphics config (swiftshader: relative costs only)
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const [dir, img, x, y, w, h, OW, OH] = process.argv.slice(2);
const srv = http.createServer((q, r) => { const f = path.join(dir, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, b) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'content-type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'image/png' }); r.end(b); } }); }).listen(0, async () => {
  const port = srv.address().port; const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage(); p.on('pageerror', e => console.log('pageerror', e.message)); p.on('console', m => console.log('console', m.text()));
  fs.copyFileSync(img, path.join(dir, 'frame.png'));
  await p.goto(`http://localhost:${port}/index.html`);
  const r = await p.evaluate(async ([x, y, w, h, OW, OH, cfgs]) => {
    const im = new Image(); im.src = 'frame.png'; await im.decode();
    const c0 = document.createElement('canvas'); c0.width = w; c0.height = h; const x0 = c0.getContext('2d'); x0.drawImage(im, -x, -y);
    const d = x0.getImageData(0, 0, w, h).data, rgb = new Uint8Array(w * h * 3); for (let i = 0; i < w * h; i++) { rgb[i*3] = d[i*4]; rgb[i*3+1] = d[i*4+1]; rgb[i*3+2] = d[i*4+2]; }
    const cv = document.getElementById('c'); cv.width = OW; cv.height = OH;
    const gl = cv.getContext('webgl2'); const draw = makeSharpHD(gl); if (!draw) return (window.__wideLog || []).join('|');
    window.__itemsDbg = [[w*0.3, h*0.5, 30], [w*0.6, h*0.4, 13], [w*0.5, h*0.7, 5]];
    const out = [];
    for (const c of cfgs) {
      const look = Object.assign({}, LIGHT_LOOKS.looks.Woods, c.set || {}); window.__rotkLook = c.off ? null : look;
      window.__aliveOff = !!c.aliveOff; window.__rotkNightForce = c.night || 0; if (c.noItems) window.__itemsDbg = []; else window.__itemsDbg = [[w*0.3, h*0.5, 30], [w*0.6, h*0.4, 13], [w*0.5, h*0.7, 5]];
      try { localStorage.setItem('rotk-light', c.off ? '0' : '1'); } catch (e) {}
      const dw = c.ow || OW, dh = c.oh || OH; if (cv.width !== dw) { cv.width = dw; cv.height = dh; }
      const one = () => { draw(rgb, 0, w, 0, 0, w, h, [0, 0, dw, dh], !!c.plain); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); };
      for (let i = 0; i < 10; i++) one();
      const t0 = performance.now(); for (let i = 0; i < 40; i++) one(); out.push(c.name + ': ' + ((performance.now() - t0) / 40).toFixed(1) + ' ms');
    }
    return out.join('\n');
  }, [+x, +y, +w, +h, +OW, +OH, JSON.parse(process.env.CFGS)]);
  console.log(r); await b.close(); srv.close();
});
