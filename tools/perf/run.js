// node run.js <siteDir> <level> [secs] [profile.json]  -- real Play Room page, headless, warp to a level, measure
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [dir, LV = '46', SECS = '10', PROF] = process.argv.slice(2);
const mime = f => f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.wasm') ? 'application/wasm' : f.endsWith('.png') ? 'image/png' : f.endsWith('.json') ? 'application/json' : f.endsWith('.webp') ? 'image/webp' : 'text/plain';
(async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: +(process.env.VW || 844), height: +(process.env.VH || 390) }, deviceScaleFactor: +(process.env.DPR || 1) });
  await ctx.route('https://site.test/**', async r => { const u = new URL(r.request().url()); let f = path.join(dir, decodeURIComponent(u.pathname)); if (u.pathname === '/') f = path.join(dir, 'index.html');
    try { await r.fulfill({ status: 200, body: fs.readFileSync(f), headers: { 'content-type': mime(f) } }); } catch (e) { await r.fulfill({ status: 404, body: '' }); } });
  const p = await ctx.newPage(); if (process.env.CMP) await p.addInitScript(() => { window.__keepPicture = true; });
  if (process.env.PASSES) await p.addInitScript({ path: process.env.INJ || '/tmp/rc/perf/h/passes.js' });
  p.on('response', r => { if (r.status() === 404) console.log('404', r.url().slice(0,120)); });
  p.on('pageerror', e => console.log('pageerror', e.message));
  p.on('console', m => { const t = m.text(); if (!/Download the React|GL Driver|GPU stall|Failed to load resource/.test(t)) console.log('console', t.slice(0, 200)); });
  if (process.env.SAVE) { const sv = JSON.parse(fs.readFileSync(process.env.SAVE)); sv.at = Date.now(); const p2 = process.env.P2; await p.addInitScript(([sv, p2]) => { if (location.hostname !== 'site.test') return; try { if (!sessionStorage.getItem('__init')) { localStorage.setItem('rotk-wide-sav', JSON.stringify(sv)); if (p2) { const [a, b] = p2.split(','); sessionStorage.setItem('rotk-p2', JSON.stringify({ p1: +a, p2: +b })); } sessionStorage.setItem('__init', '1'); } } catch (e) {} }, [sv, p2]); }
  await p.goto('https://site.test/');
  await p.setInputFiles('#rom', '/tmp/rc/perf/orig.gba');
  await p.waitForFunction(() => !document.getElementById('play').disabled, null, { timeout: 120000 });
  await p.click('#play');
  await p.waitForFunction(() => window.__wideM && window.GbrHost && GbrHost.frames > 30, null, { timeout: 180000 });
  const press = async (k, ms = 120) => { await p.keyboard.down(k); await p.waitForTimeout(ms); await p.keyboard.up(k); await p.waitForTimeout(250); };
  await p.waitForTimeout(6000);
  if (!process.env.NOWARP) for (let i = 0; i < 12; i++) { await press('Enter'); await p.waitForTimeout(900); }
  if (!process.env.NOWARP) for (let i = 0; i < 8; i++) { await press('z'); await p.waitForTimeout(900); }
  if (!process.env.NOWARP) await p.evaluate(lv => { const M = window.__wideM, H8 = M.HEAPU8, iw = M._rotk_iwram(); const w32 = (o, v) => { for (let i = 0; i < 4; i++) H8[iw + o + i] = (v >>> (8 * i)) & 255; }; w32(0x41F8, lv); w32(0x41F4, 5); w32(0x41F0, 0x81); }, +LV);
  await p.waitForTimeout(12000);
  for (let i = 0; i < 4; i++) { await press('z'); await p.waitForTimeout(700); }
  const st = await p.evaluate(() => { const M = window.__wideM; return { link: !!(M._rotk_link_on && M._rotk_link_on()), p2: sessionStorage.getItem('rotk-p2'), st: M.HEAPU8[M._rotk_iwram() + 0x41B0], lv: M.HEAPU8[M._rotk_iwram() + 0x41F8], cw: GbrHost.canvas.width, ch: GbrHost.canvas.height, log: (window.__wideLog || []).slice(-5) }; });
  console.log('state', JSON.stringify(st));
  let cdp; if (PROF) { cdp = await ctx.newCDPSession(p); await cdp.send('Profiler.enable'); await cdp.send('Profiler.setSamplingInterval', { interval: 200 }); await cdp.send('Profiler.start'); }
  // walk around in a box while measuring
  await p.evaluate(() => { window.__m = { f: GbrHost.frames, t: performance.now(), raf: 0, long: 0, last: performance.now(), dts: [] }; const tick = () => { const n = performance.now(), m = window.__m; m.raf++; const dt = n - m.last; m.dts.push(dt); if (dt > 25) m.long++; m.last = n; requestAnimationFrame(tick); }; requestAnimationFrame(tick); });
  const t0 = Date.now(); const dirs = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp']; let k = 0;
  while (Date.now() - t0 < +SECS * 1000) { const d = dirs[k++ % 4]; await p.keyboard.down(d); await p.keyboard.down('x'); await p.waitForTimeout(400); await p.keyboard.up('x'); await p.waitForTimeout(800); await p.keyboard.up(d); }
  const r = await p.evaluate(() => { const m = window.__m, s = (performance.now() - m.t) / 1000; const d = m.dts.slice().sort((a, b) => a - b); return { pics: ((GbrHost.frames - m.f) / s).toFixed(1), raf: (m.raf / s).toFixed(1), long: m.long, p50: d[d.length >> 1].toFixed(1), p95: d[Math.floor(d.length * 0.95)].toFixed(1), log: (window.__wideLog || []).slice(-5) }; });
  console.log('result', JSON.stringify(r));
  if (process.env.PASSES) { await p.evaluate(() => { __pass.on = true; }); await p.waitForTimeout(+process.env.PASSES * 1000); console.log(await p.evaluate(() => { __pass.on = false; return __passDump(); })); }
  if (PROF) { const { profile } = await cdp.send('Profiler.stop'); fs.writeFileSync(PROF, JSON.stringify(profile)); }

  if (process.env.CMP) {
    const shots = await p.evaluate(async () => {
      const M = window.__wideM, H = GbrHost; M._rotk_pause(1); await new Promise(r => setTimeout(r, 300));
      const T = performance.now(); const pn = performance.now; performance.now = () => T;
      const out = {};
      const render = (name, f) => {
        window.__canOff = f.can; window.__preOff = f.pre; window.__fullRes = f.full; H.fitDue = true;
        const d = H.d, u = H.u32(), base = H.ptr + d.video + H.front * d.videoStride, w = u[base >> 2], h = u[(base >> 2) + 1];
        H._sw = w; H._sh = h; H._fr = !!window.__fullRes; H.fit();
        for (let i = 0; i < 80; i++) H.sharp(H._u8, base + d.pixels, w, 0, 0, w, h, [0, 0, H.canvas.width, H.canvas.height], false);
        const c = document.createElement('canvas'); c.width = H.fullW; c.height = H.fullH; const x = c.getContext('2d'); x.imageSmoothingEnabled = true; x.drawImage(H.canvas, 0, 0, c.width, c.height);
        out[name] = { url: c.toDataURL('image/png'), px: x.getImageData(0, 0, c.width, c.height).data, cw: H.canvas.width, ch: H.canvas.height };
      };
      render('old', { can: 1, pre: 1, full: 1 }); render('can', { can: 0, pre: 1, full: 1 }); render('pre', { can: 1, pre: 0, full: 1 }); render('cap', { can: 1, pre: 1, full: 0 }); render('new', { can: 0, pre: 0, full: 0 });
      performance.now = pn; M._rotk_pause(0);
      const res = {}; const a = out.old.px;
      for (const k of ['can', 'pre', 'cap', 'new']) { const b = out[k].px; let sum = 0, mx = 0, big = 0; for (let i = 0; i < a.length; i += 4) for (let j = 0; j < 3; j++) { const dd = Math.abs(a[i + j] - b[i + j]); sum += dd; if (dd > mx) mx = dd; if (dd > 24) big++; } res[k] = { mean: (sum / (a.length * 0.75)).toFixed(3), max: mx, over24: (100 * big / (a.length * 0.75)).toFixed(3) + '%', canvas: out[k].cw + 'x' + out[k].ch }; }
      return { res, urls: Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.url])) };
    });
    console.log('cmp', JSON.stringify(shots.res));
    for (const [k, u] of Object.entries(shots.urls)) fs.writeFileSync((process.env.CMPDIR || '/tmp/rc/perf/cmp') + '/' + k + '.png', Buffer.from(u.split(',')[1], 'base64'));
  }
  if (process.env.SHOT) await p.screenshot({ path: process.env.SHOT });
  await b.close();
})();
