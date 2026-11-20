const { boot } = require('./lib');
(async () => {
  const { b, p } = await boot({ page: process.env.PAGE, lv: 82 });
  if (process.env.THR) { const c = await p.context().newCDPSession(p); await c.send('Emulation.setCPUThrottlingRate', { rate: +process.env.THR }); }
  const res = [];
  for (let i = 0; i < +(process.env.N || 12); i++) {
    await p.waitForTimeout(900);
    const r = await p.evaluate(async (hold) => {
      const g = __g, P = 0x03003C00, hero = g.r32(P);
      const a0 = g.r8(hero + 0x95), t0 = performance.now();
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'x' }));
      await new Promise(r => setTimeout(r, hold));
      window.dispatchEvent(new KeyboardEvent('keyup', { key: 'x' }));
      // wait up to 400ms for an attack picture
      let hit = -1; const anims = [];
      for (let k = 0; k < 80; k++) { const a = g.r8(hero + 0x95); anims.push(a); if (a !== 4 && a !== 6 && a !== a0) { hit = performance.now() - t0; break; } await new Promise(r => setTimeout(r, 5)); }
      return [hit, a0, [...new Set(anims)].join('/')];
    }, +(process.env.HOLD || 10));
    res.push(r);
  }
  console.log(JSON.stringify(res));
  const ok = res.filter(r => r[0] >= 0); console.log('landed', ok.length, 'of', res.length, 'avg ms', (ok.reduce((a, r) => a + r[0], 0) / Math.max(1, ok.length)).toFixed(0));
  await b.close();
})();
