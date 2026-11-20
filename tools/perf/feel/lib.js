// boot the real Play Room headless, warp to a level. usage: const {boot}=require('./lib'); const {p,b,ev}=await boot({lv:82})
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const S = process.env.WORK || '/tmp/rc/feel';   // holds site/ (artifact files) and orig.gba
const mime = f => f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.wasm') ? 'application/wasm' : f.endsWith('.png') ? 'image/png' : f.endsWith('.json') ? 'application/json' : f.endsWith('.webp') ? 'image/webp' : 'text/plain';
async function boot(o = {}) {
  const dir = o.dir || process.env.SITE || S + '/site';
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: 844, height: 390 }, deviceScaleFactor: 1, hasTouch: !!o.touch });
  await ctx.route('https://site.test/**', async r => { const u = new URL(r.request().url()); let f = path.join(dir, decodeURIComponent(u.pathname)); if (u.pathname === '/') f = path.join(dir, 'index.html');
    if (u.pathname === '/index.html' || u.pathname === '/') { if (o.page) f = o.page; }
    try { await r.fulfill({ status: 200, body: fs.readFileSync(f), headers: { 'content-type': mime(f) } }); } catch (e) { await r.fulfill({ status: 404, body: '' }); } });
  const p = await ctx.newPage();
  p.on('pageerror', e => console.log('pageerror', e.message));
  p.on('console', m => { const t = m.text(); if (/^T:|error|Error/.test(t) && !/Failed to load resource|GL Driver|GPU stall/.test(t)) console.log('console', t.slice(0, 300)); });
  if (o.init) await p.addInitScript(o.init);
  await p.goto('https://site.test/');
  await p.setInputFiles('#rom', S + '/orig.gba');
  await p.waitForFunction(() => !document.getElementById('play').disabled, null, { timeout: 120000 });
  await p.click('#play');
  await p.waitForFunction(() => window.__wideM && window.GbrHost && GbrHost.frames > 30, null, { timeout: 180000 });
  const press = async (k, ms = 120) => { await p.keyboard.down(k); await p.waitForTimeout(ms); await p.keyboard.up(k); await p.waitForTimeout(250); };
  await p.waitForTimeout(5000);
  for (let i = 0; i < 12; i++) { await press('Enter'); await p.waitForTimeout(800); }
  for (let i = 0; i < 8; i++) { await press('z'); await p.waitForTimeout(800); }
  if (o.hero !== undefined) await p.evaluate(h => { const M = window.__wideM; M.HEAPU8[M._rotk_iwram() + 0x3C00 + 0x19F] = h; }, o.hero);
  await p.evaluate(lv => { const M = window.__wideM, H8 = M.HEAPU8, iw = M._rotk_iwram(); const w32 = (o, v) => { for (let i = 0; i < 4; i++) H8[iw + o + i] = (v >>> (8 * i)) & 255; }; w32(0x41F8, lv); w32(0x41F4, 5); w32(0x41F0, 0x81); }, o.lv || 82);
  await p.waitForTimeout(12000);
  for (let i = 0; i < 4; i++) { await press('z'); await p.waitForTimeout(600); }
  await p.evaluate(() => { const M = window.__wideM, iw = M._rotk_iwram(), ew = M._rotk_ewram();
    window.__g = { M, iw, ew, H: () => M.HEAPU8, r8: a => { const H = M.HEAPU8; return a >= 0x03000000 ? H[iw + a - 0x03000000] : H[ew + a - 0x02000000]; },
      r32: a => { const g = window.__g; return (g.r8(a) | g.r8(a + 1) << 8 | g.r8(a + 2) << 16 | g.r8(a + 3) << 24) >>> 0; },
      w8: (a, v) => { const H = M.HEAPU8; if (a >= 0x03000000) H[iw + a - 0x03000000] = v; else H[ew + a - 0x02000000] = v; } };
    window.__g.r16 = a => window.__g.r8(a) | window.__g.r8(a + 1) << 8; window.__g.s32 = a => window.__g.r32(a) | 0; });
  return { b, p, press };
}
module.exports = { boot, S };
