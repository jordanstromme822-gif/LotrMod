// node tools/test/region-walk.js <siteDir>  -- real Play Room page headless: boots into the Isengard region (P2=a,b for 2-player, ONEP=1 for 1-player via the title menu + level change), WARPS="x,y;..." then WALK=<key> or <key>;<key>;... one per warp (FRAMES=<ms> saves a picture every <ms> while walking) with TURBO=<frames> (virtual clock, ~75 game frames per real second) or WMS=<ms>. SAVE=<save json>, SHOT=<png prefix>, PROBE=<js file evaluated in the page at the end, result logged>. ROM: /tmp/rc/perf/orig.gba.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [dir, LV = '46', SECS = '10', PROF] = process.argv.slice(2);
const mime = f => f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.wasm') ? 'application/wasm' : f.endsWith('.png') ? 'image/png' : f.endsWith('.json') ? 'application/json' : f.endsWith('.webp') ? 'image/webp' : 'text/plain';
(async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: +(process.env.VW || 844), height: +(process.env.VH || 390) }, deviceScaleFactor: +(process.env.DPR || 1) });
  await ctx.route('https://site.test/**', async r => { const u = new URL(r.request().url()); let f = path.join(dir, decodeURIComponent(u.pathname)); if (u.pathname === '/') f = path.join(dir, 'index.html');
    try { await r.fulfill({ status: 200, body: fs.readFileSync(f), headers: { 'content-type': mime(f) } }); } catch (e) { await r.fulfill({ status: 404, body: '' }); } });
  const p = await ctx.newPage(); await p.addInitScript(() => { const pn = performance.now.bind(performance); window.__toff = 0; performance.now = () => pn() + window.__toff; }); if (process.env.PLAINT) await p.addInitScript(() => { window.__plainT = 1; });
  if (process.env.CMP) await p.addInitScript(() => { window.__keepPicture = true; });
  if (process.env.PASSES) await p.addInitScript({ path: process.env.INJ || '/tmp/rc/perf/h/passes.js' });
  p.on('response', r => { if (r.status() === 404) console.log('404', r.url().slice(0,120)); });
  p.on('pageerror', e => console.log('pageerror', e.message));
  p.on('console', m => { const t = m.text(); if (!/Download the React|GL Driver|GPU stall|Failed to load resource/.test(t)) console.log('console', t.slice(0, 200)); });
  if (process.env.SAVE) { const sv = JSON.parse(fs.readFileSync(process.env.SAVE)); sv.at = Date.now(); const p2 = process.env.P2; await p.addInitScript(([sv, p2]) => { if (location.hostname !== 'site.test') return; try { if (!sessionStorage.getItem('__init')) { localStorage.setItem('rotk-wide-sav', JSON.stringify(sv)); if (p2) { const [a, b] = p2.split(','); sessionStorage.setItem('rotk-p2', JSON.stringify({ p1: +a, p2: +b, level: 51 })); } sessionStorage.setItem('__init', '1'); } } catch (e) {} }, [sv, p2]); }
  await p.goto('https://site.test/');
  await p.setInputFiles('#rom', '/tmp/rc/perf/orig.gba');
  await p.waitForFunction(() => !document.getElementById('play').disabled, null, { timeout: 120000 });
  await p.click('#play');
  await p.waitForFunction(() => window.__wideM && window.GbrHost && GbrHost.frames > 30, null, { timeout: 180000 });
  const t0 = Date.now(); let last = '';
  while (Date.now() - t0 < 420000) {
    const s = await p.evaluate(() => { const M = window.__wideM, H = M.HEAPU8, iw = M._rotk_iwram(); const el = document.getElementById('p2Load'); return { st: H[iw + 0x41B0], lv: H[iw + 0x4174], load: !!(el && !el.hidden), link: !!(M._rotk_link_on && M._rotk_link_on()), one: !!(M._rotk_link_is_one && M._rotk_link_is_one()) }; });
    const k = JSON.stringify(s); if (k !== last) { console.log(Math.round((Date.now() - t0) / 1000) + 's', k); last = k; }
    if (s.st === 1 && s.lv === 51 && !s.load) break;
    if (process.env.ONEP) {   // 1 player: through the title menu with Enter (Load Game, first slot), then the game's own level change to 51
      if (s.st !== 1) { await p.keyboard.press('Enter'); }
      else if (s.lv !== 51) { await p.evaluate(() => { const M = window.__wideM, H8 = M.HEAPU8, iw = M._rotk_iwram(); const w32 = (o, v) => { for (let i = 0; i < 4; i++) H8[iw + o + i] = (v >>> (8 * i)) & 255; }; w32(0x41F8, 51); w32(0x41F4, 5); w32(0x41F0, 0x81); }); await p.waitForTimeout(6000); }
    }
    await p.waitForTimeout(3000);
  }
  await p.waitForTimeout(8000);
  console.log('heroes', JSON.stringify(await p.evaluate(() => { const M = window.__wideM, iw = M._rotk_iwram(), H = M.HEAPU8; const r32 = a => (H[iw+a]|H[iw+a+1]<<8|H[iw+a+2]<<16|H[iw+a+3]<<24)>>>0; return [0,1].map(i => r32(0x3c00 + i*0x1ac).toString(16)); })));
  await p.screenshot({ path: process.env.SHOT + '-a.png' });
  for (const [k, xy] of (process.env.WARPS || '5736,9950').split(';').entries()) { const [x, y] = xy.split(',').map(Number);
    if (x) await p.evaluate(([x, y, both]) => { const M = window.__wideM, iw = M._rotk_iwram(), ew = M._rotk_ewram(), H = M.HEAPU8; const r8 = a => a >= 0x03000000 ? H[iw + a - 0x03000000] : H[ew + a - 0x02000000]; const w8 = (a, v) => { if (a >= 0x03000000) H[iw + a - 0x03000000] = v; else H[ew + a - 0x02000000] = v; }; const r32 = a => (r8(a) | r8(a+1) << 8 | r8(a+2) << 16 | r8(a+3) << 24) >>> 0; const put = (o, x, y) => { for (const b of [0xac, 0xb4, 0xcc]) { w8(o+b+2, x & 255); w8(o+b+3, x >> 8); w8(o+b+6, y & 255); w8(o+b+7, y >> 8); } }; const me = r8(0x03003f59) & 1; put(r32(0x03003c00 + me * 0x1ac), x, y); if (both) { const o2 = r32(0x03003c00 + (me ^ 1) * 0x1ac); if (o2 >>> 24 === 2) put(o2, x + 24, y + 12); } }, [x, y, !!process.env.BOTH]);
    await p.waitForTimeout(+(process.env.WAIT || 12000));
    // A warp leaves an object (shown as a chest) 90 px in front of the hero that blocks walking; move it out of the way
    // (test only: real play never warps).
    if (x) console.log('moved', JSON.stringify(await p.evaluate(() => { const M = window.__wideM, iw = M._rotk_iwram(), ew = M._rotk_ewram(), H = M.HEAPU8; const r8 = a => a >= 0x03000000 ? H[iw + a - 0x03000000] : H[ew + a - 0x02000000]; const w8 = (a, v) => { H[ew + a - 0x02000000] = v; }; const r16 = a => r8(a) | r8(a+1) << 8; const r32 = a => (r8(a) | r8(a+1) << 8 | r8(a+2) << 16 | r8(a+3) << 24) >>> 0; const o = r32(0x03003c00 + r8(0x03003f59) * 0x1ac); const hx = r16(o+0xae), hy = r16(o+0xb2); const out = []; for (let a = 0x02000000; a < 0x02040000 - 0xb4; a += 4) { if (a === o) continue; const dx = r16(a+0xae) - hx, dy = r16(a+0xb2) - hy; if ((dx === 0 && Math.abs(dy) === 90) || (dy === 0 && Math.abs(dx) === 90)) { const y2 = hy - 2 * dy, x2 = hx - 2 * dx; w8(a+0xae, x2 & 255); w8(a+0xaf, x2 >> 8); w8(a+0xb2, y2 & 255); w8(a+0xb3, y2 >> 8); out.push(a.toString(16)); } } return out; })));
    await p.waitForTimeout(500); await p.screenshot({ path: process.env.SHOT + '-w' + k + '.png' });
    const POS = () => p.evaluate(() => { const M = window.__wideM, iw = M._rotk_iwram(), ew = M._rotk_ewram(), H = M.HEAPU8; const r8 = a => a >= 0x03000000 ? H[iw + a - 0x03000000] : H[ew + a - 0x02000000]; const r32 = a => (r8(a) | r8(a+1) << 8 | r8(a+2) << 16 | r8(a+3) << 24) >>> 0; const o = r32(0x03003c00 + r8(0x03003f59) * 0x1ac); return [r8(o+0xae)|r8(o+0xaf)<<8, r8(o+0xb2)|r8(o+0xb3)<<8]; });
    const WK = process.env.WALK ? (process.env.WALK.split(';')[k] || process.env.WALK.split(';').pop()) : ''; if (WK) { console.log('before', JSON.stringify(await POS())); await p.keyboard.down(WK); if (process.env.TURBO) { await p.waitForTimeout(300); const t1 = Date.now(); const n = await p.evaluate((N) => { const M = window.__wideM; let k = 0; for (; k < N; k++) { window.__toff += 16.743; M._rotk_bg_tick(); } return k; }, +process.env.TURBO); console.log('turbo frames', n, 'ms', Date.now() - t1); } else if (process.env.FRAMES) { const t1 = Date.now(); let f = 0; while (Date.now() - t1 < +(process.env.WMS || 4000)) { await p.screenshot({ path: process.env.SHOT + '-k' + k + '-f' + String(f++).padStart(2, '0') + '.jpg', type: 'jpeg', quality: 60 }); await p.waitForTimeout(+process.env.FRAMES); } } else await p.waitForTimeout(+(process.env.WMS || 4000)); await p.keyboard.up(WK); await p.waitForTimeout(500); console.log('after', JSON.stringify(await POS())); await p.screenshot({ path: process.env.SHOT + '-k' + k + '.png' }); }
    if (process.env.SCAN) console.log('near', k, JSON.stringify(await p.evaluate(() => { const M = window.__wideM, iw = M._rotk_iwram(), ew = M._rotk_ewram(), H = M.HEAPU8; const r8 = a => a >= 0x03000000 ? H[iw + a - 0x03000000] : H[ew + a - 0x02000000]; const r16 = a => r8(a) | r8(a+1) << 8; const r32 = a => (r8(a) | r8(a+1) << 8 | r8(a+2) << 16 | r8(a+3) << 24) >>> 0; const o = r32(0x03003c00 + r8(0x03003f59) * 0x1ac); const hx = r16(o+0xae), hy = r16(o+0xb2); const out = []; for (const [base, len] of [[0x02000000, 0x40000], [0x03000000, 0x8000]]) for (let a = base; a < base + len - 0xb4; a += 4) { const x = r16(a+0xae), y = r16(a+0xb2); if (Math.abs(x-hx) < 160 && Math.abs(y-hy) < 160 && a !== o) out.push([a.toString(16), x-hx, y-hy, r8(a), r8(a+1), r8(a+2), r8(a+3), r16(a+0x10), r16(a+0x12)]); } return { o: o.toString(16), hx, hy, out: out.slice(0, 40) }; })));
    console.log('pos', k, JSON.stringify(await p.evaluate(() => { const M = window.__wideM, iw = M._rotk_iwram(), ew = M._rotk_ewram(), H = M.HEAPU8; const r8 = a => a >= 0x03000000 ? H[iw + a - 0x03000000] : H[ew + a - 0x02000000]; const r32 = a => (r8(a) | r8(a+1) << 8 | r8(a+2) << 16 | r8(a+3) << 24) >>> 0; const o = r32(0x03003c00 + r8(0x03003f59) * 0x1ac); return [r8(o+0xae)|r8(o+0xaf)<<8, r8(o+0xb2)|r8(o+0xb3)<<8]; }))); } 
  if (process.env.PROBE) console.log('probe', JSON.stringify(await p.evaluate(fs.readFileSync(process.env.PROBE, 'utf8'))));
  if (process.env.PROBE) await p.screenshot({ path: process.env.SHOT + '-probe.png' });
  console.log('orth', JSON.stringify(await p.evaluate(() => window.__orthancDbg && window.__orthancDbg.info())));
  console.log('log', JSON.stringify(await p.evaluate(() => (window.__wideLog || []).slice(-8))));
  await b.close();
})();
