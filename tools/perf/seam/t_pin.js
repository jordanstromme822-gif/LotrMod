// WORK = folder with site/ (artifact files, maps/t too) and orig.gba, as for tools/perf/feel

const { boot } = require('../feel/lib'); const fs = require('fs');
(async () => {
  const LV = +(process.env.LV || 93), WANT = +(process.env.WANT || 0), OUT = process.env.OUT || 'pin'; fs.mkdirSync(OUT, { recursive: true });
  const { b, p } = await boot({ lv: LV });
  const key = await p.evaluate(([LV, WANT]) => {
    const g = window.__g; const D = window.__smData, e = D.EE[LV].find(e => e[0] === 1 && (!WANT || e[3] === WANT)), [w, hh] = D.SZ[LV]; const ex = e[1] * w / 1000, ey = e[2] * hh / 1000;
    const h = g.r32(0x03003C00), w16 = (a, v) => { g.w8(a, v & 255); g.w8(a + 1, (v >> 8) & 255); };
    const d = [ex, w - ex, ey, hh - ey], side = d.indexOf(Math.min(...d)); const off = [[40, 0], [-40, 0], [0, 40], [0, -40]][side];
    const tx = Math.round(ex + off[0]), ty = Math.round(ey + off[1]); w16(h + 0xAE, tx); w16(h + 0xB2, ty); w16(h + 0xCE, tx); w16(h + 0xD2, ty);
    window.__seam.pin(0); window.__seamDebug = 1;
    return [['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'][side], e[3]];
  }, [LV, WANT]);
  console.log('walk', key);
  await p.waitForTimeout(500);
  await p.keyboard.down(key[0]);
  await p.waitForFunction(() => window.__seam.on, null, { timeout: 15000 });
  await p.keyboard.up(key[0]);
  fs.writeFileSync(OUT + '/dbg.json', JSON.stringify(await p.evaluate(() => { const f = window.__gbaFrame(); return { v: window.__gbaView, cam: window.__seamDbg, w: f.w, h: f.h }; })));
  for (const u of [0, 0.1, 0.2, 0.3, 0.4, 0.5]) { await p.evaluate(u => window.__seam.pin(u), u); await p.waitForTimeout(400); await p.screenshot({ path: `${OUT}/u${u.toFixed(2)}.png` }); }
  await p.waitForFunction(() => window.__seam.ready, null, { timeout: 15000 });
  for (const u of [0.6, 0.7, 0.8, 0.9, 0.97]) { await p.evaluate(u => window.__seam.pin(u), u); await p.waitForTimeout(400); await p.screenshot({ path: `${OUT}/u${u.toFixed(2)}.png` }); }
  await p.evaluate(() => window.__seam.pin(null)); await p.waitForTimeout(1500); await p.screenshot({ path: `${OUT}/z_after.png` });
  console.log((await p.evaluate(() => (window.__wideLog || []).slice(-4))).join(' | '));
  await b.close();
})();
