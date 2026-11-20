const { boot } = require('./lib');
(async () => {
  const { b, p } = await boot({ page: process.env.PAGE, lv: +(process.env.LV || 82), hero: process.env.HERO ? +process.env.HERO : undefined });
  const foes = () => p.evaluate(() => { const g = __g, hero = g.r32(0x03003C00); let q = hero, n = 0; while (n++ < 400) { const nx = g.r32(q); if (!nx || nx >>> 24 !== 2) break; q = nx; } const out = [];
    for (n = 0; q >>> 24 === 2 && n < 400; n++, q = g.r32(q + 4)) if (g.r32(q + 0x14) === 0x0801b9d1 && ![0x11, 0x15, 4, 0x1b, 0x13].includes(g.r8(q + 0x62))) out.push([q, g.r16(q + 0xAE) - g.r16(hero + 0xAE), g.r16(q + 0xB2) - g.r16(hero + 0xB2), g.r8(q + 0x62), g.r16(q + 0x5A)]);
    return { hx: g.r16(hero + 0xAE), hy: g.r16(hero + 0xB2), out: out.sort((a, c) => Math.hypot(a[1], a[2]) - Math.hypot(c[1], c[2])).slice(0, 6) }; });
  console.log('foes', JSON.stringify(await foes()));
  // test only: put the hero OFF px to the right of the nearest foe, then let things settle
  await p.evaluate(([ox, oy]) => { const g = __g, hero = g.r32(0x03003C00); let q = hero, n = 0; while (n++ < 400) { const nx = g.r32(q); if (!nx || nx >>> 24 !== 2) break; q = nx; } let best = null, bd = 1e9;
    for (n = 0; q >>> 24 === 2 && n < 400; n++, q = g.r32(q + 4)) if (g.r32(q + 0x14) === 0x0801b9d1 && ![0x11, 0x15, 4, 0x1b, 0x13].includes(g.r8(q + 0x62))) { const d = Math.hypot(g.r16(q + 0xAE) - g.r16(hero + 0xAE), g.r16(q + 0xB2) - g.r16(hero + 0xB2)); if (d < bd) { bd = d; best = q; } }
    const w16 = (a, v) => { g.w8(a, v & 255); g.w8(a + 1, v >> 8 & 255); }; w16(hero + 0xAE, g.r16(best + 0xAE) + ox); w16(hero + 0xB2, g.r16(best + 0xB2) + oy); }, [+(process.env.OX || 50), +(process.env.OY || 0)]);
  await p.waitForTimeout(+(process.env.SETTLE || 300));
  console.log('placed', JSON.stringify((await foes()).out.slice(0, 2)));
  const r = await p.evaluate(async () => {
    const g = __g, hero = g.r32(0x03003C00), log = [], t0 = performance.now(), sp0 = g.r16(0x03003C00 + 0x17E);
    const iv = setInterval(() => log.push([Math.round(performance.now() - t0), g.r16(hero + 0xAE), g.r16(hero + 0xB2), g.r8(hero + 0x95), g.r8(hero + 0xF8), GbrHost.keys & 2 ? 0 : 1, GbrHost.keys & 512 ? 0 : 1, window.__hitStepLock ? 1 : 0].join(',')), 33);
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'x' })); await new Promise(r => setTimeout(r, 30)); window.dispatchEvent(new KeyboardEvent('keyup', { key: 'x' }));
    await new Promise(r => setTimeout(r, 1200)); clearInterval(iv); return { log: log.join(' | '), spirit: [sp0, g.r16(0x03003C00 + 0x17E)] };
  });
  console.log('t,x,y,anim,face,B,L,step:', r.log); console.log('spirit', r.spirit);
  console.log('after', JSON.stringify((await foes()).out.slice(0, 2)));
  await b.close();
})();
