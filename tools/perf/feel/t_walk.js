const { boot } = require('./lib');
(async () => {
  const { b, p } = await boot({ page: process.env.PAGE, lv: +(process.env.LV || 82), hero: process.env.HERO ? +process.env.HERO : undefined });
  console.log('state', await p.evaluate(() => { const g = __g; return [g.r8(0x030041B0), g.r8(0x030041F8), g.r8(0x03003C00 + 0x19F), g.r32(0x03003C00).toString(16)]; }));
  // sample each animation frame
  await p.evaluate(() => { window.__s = []; const g = __g; const f = () => { const hero = g.r32(0x03003C00); if (hero >>> 24 === 2) window.__s.push([Math.round(performance.now()), GbrHost.frames, g.r16(hero + 0xAE), g.r16(hero + 0xB2), g.s32(hero + 0xB4), g.s32(hero + 0xB8), g.r8(hero + 0x22), g.r8(hero + 0x23), g.r8(hero + 0x95), g.r8(hero + 0x62), g.s32(hero + 0xE4)]); requestAnimationFrame(f); }; requestAnimationFrame(f); });
  const mode = process.env.MODE || 'key';
  const dirs = (process.env.DIRS || 'ArrowRight').split(',');
  for (const d of dirs) {
    await p.evaluate(() => window.__s.push('--'));
    if (mode === 'key') { await p.keyboard.down(d); await p.waitForTimeout(+(process.env.HOLD || 1500)); await p.keyboard.up(d); }
    else { const ang = +d; await p.evaluate(a => { window.__freeStick(true, a); }, ang); const dir8 = await p.evaluate(a => window.__freeDir8(a), ang); const ks = [['ArrowUp'], ['ArrowUp', 'ArrowRight'], ['ArrowRight'], ['ArrowRight', 'ArrowDown'], ['ArrowDown'], ['ArrowDown', 'ArrowLeft'], ['ArrowLeft'], ['ArrowLeft', 'ArrowUp']][dir8]; for (const k of ks) await p.keyboard.down(k); await p.waitForTimeout(+(process.env.HOLD || 1500)); for (const k of ks) await p.keyboard.up(k); await p.evaluate(() => window.__freeStick(false, 0)); }
    await p.evaluate(() => window.__s.push('up'));
    await p.waitForTimeout(700);
  }
  const s = await p.evaluate(() => window.__s);
  console.log(s.map(r => Array.isArray(r) ? r.join(' ') : r).join('\n'));
  await b.close();
})();
