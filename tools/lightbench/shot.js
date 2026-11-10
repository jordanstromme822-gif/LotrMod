// node shot.js <harnessdir> <out-prefix> <map png> <look> <night> x y w h scale t1,t2,...
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path');
const [dir, outp, img, look, night, x, y, w, h, sc, ts] = process.argv.slice(2);
const srv = http.createServer((q, r) => { const f = path.join(dir, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, b) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'content-type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : 'image/png' }); r.end(b); } }); }).listen(0, async () => {
  const port = srv.address().port; const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage(); p.on('pageerror', e => console.log('pageerror', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('console', m.text()); });
  fs.copyFileSync(img, path.join(dir, 'frame.png'));
  await p.goto(`http://localhost:${port}/index.html`);
  await p.evaluate(d => { window.__dbgSet = d; }, +(process.env.DBG || 0)); const r = await p.evaluate(a => window.run(...a), ['frame.png', look, +night, +x, +y, +w, +h, +sc, ts.split(',').map(Number)]);
  if (typeof r === 'string') console.log(r); else { r.shots.forEach((s, i) => fs.writeFileSync(`${outp}-${i}.png`, Buffer.from(s.split(',')[1], 'base64'))); if (r.log.length) console.log(r.log); }
  await b.close(); srv.close();
});
