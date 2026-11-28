// node tools/test/online-pair.js <siteDir>  -- two real Play Room pages headless, playing ONLINE with each other through a
// stand-in for the page's claude.ai capabilities (room presence relayed between the pages by this script, user ids,
// a db holding SAVE as each player's saved games). Host picks LEVEL (default 51). Once both games are in the level it
// runs PROBE (a JS file evaluated in the host page, may return a promise) and logs both pages' hash checks.
// Env: SAVE=<save json> (default the 2026-11-20 backup), LEVEL, SHOT=<png prefix>, LAG=<ms one way, default 40>,
// GPROBE=<js file evaluated in the guest page at the same time>, WAIT=<ms after the probe, default 30000>.
// ROM: /tmp/rc/perf/orig.gba.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [dir] = process.argv.slice(2);
const SAVE = JSON.parse(fs.readFileSync(process.env.SAVE || '/mnt/project-files/save-backups/save-backup-202611201056-before-gandalf-gear.json'));
const LEVEL = +(process.env.LEVEL || 51), LAG = +(process.env.LAG || 40), SHOT = process.env.SHOT || '/tmp/online';
const mime = f => f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.wasm') ? 'application/wasm' : f.endsWith('.png') ? 'image/png' : f.endsWith('.json') ? 'application/json' : f.endsWith('.webp') ? 'image/webp' : 'text/plain';
const STUB = ([who, save]) => {
  if (location.hostname !== 'site.test') return;
  const other = who === 'A' ? 'B' : 'A';
  // rooms: name -> { mine: presence, theirs: presence | undefined, subs: Set }
  const rooms = new Map();
  const roomOf = (name) => {
    if (rooms.has(name)) return rooms.get(name);
    const r = { mine: null, theirs: undefined, subs: new Set() };
    const api = {
      peers: () => r.theirs ? [{ sameTab: false, by: 'user-' + other, presence: r.theirs, guest: false }] : [],
      onPeers: (fn) => { r.subs.add(fn); setTimeout(() => { try { fn(api.peers()); } catch (e) {} }, 0); return () => r.subs.delete(fn); },
      presence: async (patch) => { r.mine = patch === null ? null : Object.assign({}, r.mine || {}, patch); window.__relayOut(JSON.stringify({ room: name, p: r.mine })); },
      join: async (n) => roomOf(n).api,
      leave: () => { r.mine = null; window.__relayOut(JSON.stringify({ room: name, p: null })); },
      emit: () => {}, on: () => () => {},
    };
    r.api = api; rooms.set(name, r); return r;
  };
  window.__relayIn = (s) => { const m = JSON.parse(s); const r = roomOf(m.room); r.theirs = m.p || undefined; for (const fn of r.subs) { try { fn(r.api.peers()); } catch (e) {} } };
  const docs = new Map([['data/users/user-' + who + '/save-rotk-modded', { data: save.data, size: +save.size, at: Date.now() }]]);
  const db = { doc: (p) => ({ get: async () => ({ exists: docs.has(p), data: () => docs.get(p) }), set: async (v) => { docs.set(p, v); }, update: async (v) => { docs.set(p, Object.assign({}, docs.get(p) || {}, v)); } }) };
  const user = { id: async () => 'user-' + who, me: async () => ({ id: 'user-' + who, name: 'Player ' + who }), profiles: async (ids) => Object.fromEntries(ids.map((i) => [i, { name: 'Player ' + i.slice(-1) }])), isOwner: () => true, canEdit: () => true, can: () => true };
  const NS = { room: roomOf('').api, db, user };
  window.claude = { use: async (n) => NS[n] || null };
  setTimeout(() => window.__relayHello(), 0);
};
(async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const pages = {}, lastP = { A: new Map(), B: new Map() };   // each page's latest presence per room, replayed to a page that (re)loads
  for (const who of ['A', 'B']) {
    const ctx = await b.newContext({ viewport: { width: +(process.env.VW || 844), height: +(process.env.VH || 390) } });
    await ctx.route('https://site.test/**', async r => { const u = new URL(r.request().url()); let f = path.join(dir, decodeURIComponent(u.pathname)); if (u.pathname === '/') f = path.join(dir, 'index.html');
      try { await r.fulfill({ status: 200, body: fs.readFileSync(f), headers: { 'content-type': mime(f) } }); } catch (e) { await r.fulfill({ status: 404, body: '' }); } });
    const p = await ctx.newPage(); pages[who] = p;
    await p.exposeFunction('__relayOut', (s) => { lastP[who].set(JSON.parse(s).room, s); const q = pages[who === 'A' ? 'B' : 'A']; setTimeout(() => q.evaluate((x) => window.__relayIn && window.__relayIn(x), s).catch(() => {}), LAG); });
    await p.exposeFunction('__relayHello', () => { const o = who === 'A' ? 'B' : 'A'; for (const s of lastP[o].values()) setTimeout(() => p.evaluate((x) => window.__relayIn && window.__relayIn(x), s).catch(() => {}), LAG); });
    await p.addInitScript(STUB, [who, SAVE]);
    await p.addInitScript(([sv]) => { if (location.hostname !== 'site.test') return; try { if (!sessionStorage.getItem('__init')) { localStorage.setItem('rotk-wide-sav', JSON.stringify(Object.assign({}, sv, { at: Date.now() }))); sessionStorage.setItem('__init', '1'); } } catch (e) {} }, [SAVE]);
    p.on('pageerror', e => console.log(who, 'pageerror', e.message));
    p.on('console', m => { const t = m.text(); if (/campfire|seam|online|link|Lost|error/i.test(t) && !/GL Driver|GPU stall|Failed to load/.test(t)) console.log(who, 'console', t.slice(0, 200)); });
  }
  const A = pages.A, B = pages.B;
  const boot = async (p, pick) => {
    await p.goto('https://site.test/');
    await p.evaluate((o) => sessionStorage.setItem('rotk-online', JSON.stringify(o)), pick);
    await p.reload();
    await p.setInputFiles('#rom', '/tmp/rc/perf/orig.gba');
    await p.waitForFunction(() => !document.getElementById('play').disabled, null, { timeout: 120000 });
    await p.click('#play');
  };
  await boot(A, { host: 1, level: LEVEL });
  await B.goto('https://site.test/');
  // the host's room name, from its lobby presence as the guest sees it
  let name = null;
  for (let t = 0; t < 120 && !name; t++) { await A.waitForTimeout(1000); name = await B.evaluate(async () => { const l = window.claude && await window.claude.use('room'); const h = l && l.peers().find((p) => p.presence && p.presence.host); return h ? h.presence.host.room : null; }).catch(() => null); }
  console.log('room', name, JSON.stringify(await A.evaluate(() => ({ st: (document.getElementById('mpStatus') || {}).textContent, play: (document.getElementById('play') || {}).textContent, cl: !!window.claude }))));
  if (!name) { await A.screenshot({ path: SHOT + '-nohost.png' }); await b.close(); return; }
  await boot(B, { join: name, name: 'Player A' });
  const st = (p) => p.evaluate(() => { const mp = window.__mp, M = mp && mp.M; if (!M || !mp.online) return null; const H = M.HEAPU8, iw = mp.iwram(); return { st: H[iw + 0x41B0], lv: H[iw + 0x4174], f: mp.frame(), net: mp.net && mp.net() }; }).catch(() => null);
  const t0 = Date.now(); let last = '';
  while (Date.now() - t0 < 480000) {
    const s = [await st(A), await st(B)]; const k = JSON.stringify(s);
    if (k !== last) { console.log(Math.round((Date.now() - t0) / 1000) + 's', k); last = k; }
    if (s[0] && s[1] && s[0].st === 1 && s[1].st === 1 && s[0].lv === LEVEL && s[1].lv === LEVEL) break;
    // the game's own menus, as the players would: Multiplayer on the title menu, the first saved game, then the host
    // presses A through the path screen (z = A on the keyboard)
    for (const [i, p] of [[0, A], [1, B]]) {
      const m = await p.evaluate(() => { const mp = window.__mp, M = mp && mp.M; if (!M || !mp.online) return null; const H = M.HEAPU8, iw = mp.iwram(); return { st: H[iw + 0x41B0], sub: H[iw + 0x41C0], cur: H[iw + 0x41B8] }; }).catch(() => null);
      if (!m) continue;
      const tap = async (k) => { await p.keyboard.down(k); await p.waitForTimeout(500); await p.keyboard.up(k); };
      if (m.st === 5 && m.sub === 2) await tap(m.cur < 2 ? 'ArrowDown' : m.cur > 2 ? 'ArrowUp' : 'z');
      else if (m.st === 9 && m.sub === 0) await tap('z');
      else if (m.st === 11 && i === 0) await tap('z');
      else if (m.st !== 1 && m.st !== 5 && m.st !== 9 && m.st !== 11) console.log('menu', i, JSON.stringify(m));
    }
    await A.waitForTimeout(2500);
  }
  await A.waitForTimeout(8000);
  await A.screenshot({ path: SHOT + '-A0.png' }); await B.screenshot({ path: SHOT + '-B0.png' });
  const sync = (p) => p.evaluate(() => { const mp = window.__mp; const el = document.getElementById('mpBanner'); return { banner: el && !el.hidden ? el.textContent : '', hs: mp && mp.hashes ? [...mp.hashes()].slice(-2) : null }; }).catch(() => null);
  console.log('sync before', JSON.stringify(await sync(A)), JSON.stringify(await sync(B)));
  if (process.env.HOOK) for (const p of [A, B]) console.log('hook', await p.evaluate(fs.readFileSync(process.env.HOOK, 'utf8')).catch(e => 'err ' + e.message));
  if (process.env.PROBE) console.log('probe A', JSON.stringify(await A.evaluate(fs.readFileSync(process.env.PROBE, 'utf8')).catch(e => 'err ' + e.message)));
  if (process.env.GPROBE) console.log('probe B', JSON.stringify(await B.evaluate(fs.readFileSync(process.env.GPROBE, 'utf8')).catch(e => 'err ' + e.message)));
  for (let k = 0; k < 6; k++) { await A.waitForTimeout(+(process.env.WAIT || 30000) / 6); await A.screenshot({ path: SHOT + '-A' + (k + 1) + '.jpg', type: 'jpeg', quality: 60 }); await B.screenshot({ path: SHOT + '-B' + (k + 1) + '.jpg', type: 'jpeg', quality: 60 }); console.log('t' + k, JSON.stringify([await st(A), await st(B)])); }
  console.log('sync after', JSON.stringify(await sync(A)), JSON.stringify(await sync(B)));
  if (process.env.HOOK) for (const [w, p] of [['A', A], ['B', B]]) console.log(w, 'starts', JSON.stringify(await p.evaluate(() => window.__startLog).catch(() => null)));
  for (const [w, p] of [['A', A], ['B', B]]) console.log(w, 'log', JSON.stringify(await p.evaluate(() => (window.__wideLog || []).slice(-8)).catch(() => null)));
  await b.close();
})();
