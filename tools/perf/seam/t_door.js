// WORK = folder with site/ (artifact files, maps/t too) and orig.gba, as for tools/perf/feel

const { boot } = require('../feel/lib'); const fs = require('fs');
(async () => {
  const LV = +(process.env.LV || 93), OUT = process.env.OUT || 'door'; fs.mkdirSync(OUT, { recursive: true });
  const { b, p } = await boot({ lv: LV });
  const key = await p.evaluate((LV) => {
    const g = window.__g; const D = window.__smData, e = D.EE[LV].find(e => e[0] === 1 && (!window.__want || e[3] === window.__want)), [w, hh] = D.SZ[LV]; const ex = e[1] * w / 1000, ey = e[2] * hh / 1000;
    const h = g.r32(0x03003C00), w16 = (a, v) => { g.w8(a, v & 255); g.w8(a + 1, (v >> 8) & 255); };
    const d = [ex, w - ex, ey, hh - ey], side = d.indexOf(Math.min(...d)); const off = [[40, 0], [-40, 0], [0, 40], [0, -40]][side];
    const tx = Math.round(ex + off[0]), ty = Math.round(ey + off[1]); w16(h + 0xAE, tx); w16(h + 0xB2, ty); w16(h + 0xCE, tx); w16(h + 0xD2, ty);
    window.__rec = []; const H = GbrHost, d0 = H.draw; H.draw = function () { const f0 = H.frames; d0.apply(this, arguments); if (H.frames !== f0) window.__rec.push([Math.round(performance.now()), H.frames, g.r8(0x030041F8), g.r8(0x03004174), g.r8(0x0203FFF1), window.__seam.on ? 1 : 0]); };
    return [['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'][side], e[3]];
  }, LV);
  console.log('walk', key);
  await p.waitForTimeout(500);
  await p.keyboard.down(key[0]);
  const t0 = Date.now(); let n = 0, seen = false;
  while (Date.now() - t0 < 7000) { const on = await p.evaluate(() => window.__seam.on); if (on) seen = true; if (on || (seen && n < 40)) { await p.screenshot({ path: `${OUT}/f${String(n).padStart(2, '0')}.png` }); n++; } else await p.waitForTimeout(30); if (seen && !on && n > 3) { await p.waitForTimeout(300); await p.screenshot({ path: `${OUT}/after.png` }); break; } }
  await p.keyboard.up(key[0]);
  const r = await p.evaluate(() => ({ rec: window.__rec, log: (window.__wideLog || []).slice(-5) }));
  let pv = null; r.rec.forEach(x => { const k = x.slice(2).join(' '); if (k !== pv) console.log(x.join(' ')); pv = k; });
  console.log('log', r.log, 'shots', n);
  await b.close();
})();
