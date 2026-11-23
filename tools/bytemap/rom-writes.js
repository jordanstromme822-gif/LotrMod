// Byte map, part 1: every byte the Play Room page changes in the game ROM, who changed it, and where two
// features change the same bytes (2026-11-23, Phase 1.5).
//
//   node tools/bytemap/rom-writes.js SITE_DIR ROM OUT.json
//
// SITE_DIR is a local copy of the Play Room (index.html + wide/ ...). The page is opened headless; while it builds the
// patched ROM (buildGame), every array of 16 MB or more is watched: index writes and .set() calls are recorded with the
// page line that made them. The owner of a write is the nearest comment above that line naming a version (vNNN) or
// tool, so the map stays readable without anyone writing it by hand. A byte changed by two different page lines is an
// overlap; overlaps that are meant (a later version replacing an earlier patch) are listed in allow.json with a reason.
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const [dir, ROM, OUT] = process.argv.slice(2);
if (!dir || !ROM || !OUT) { console.error('usage: node rom-writes.js SITE_DIR ROM OUT.json'); process.exit(2); }
const mime = f => f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.wasm') ? 'application/wasm' : f.endsWith('.png') ? 'image/png' : f.endsWith('.json') ? 'application/json' : f.endsWith('.webp') ? 'image/webp' : 'text/plain';
const WATCH = () => {
  const Real = Uint8Array, BIG = 0x1000000, log = [], lines = new Map();
  const site = () => { const s = new Error().stack.split('\n'); for (const l of s) { const m = /index\.html[^:]*:(\d+):\d+/.exec(l); if (m && !/WATCH/.test(l)) return +m[1]; } return 0; };
  const rec = (t, off, len, line, changed) => { if (changed) log.push([off, len, line]); };
  const wrap = (t) => new Proxy(t, {
    get(o, k) {
      if (k === 'set') return (src, at = 0) => { at |= 0; const n = src.length, line = site();
        // record only the bytes this call really changes, as runs
        let i = 0; while (i < n) { while (i < n && o[at + i] === src[i]) i++; const a = i; while (i < n && o[at + i] !== src[i]) i++; if (i > a) rec(o, at + a, i - a, line, true); }
        return o.set(src, at); };
      if (k === '__raw') return o;
      const v = o[k]; return typeof v === 'function' ? v.bind(o) : v; },
    set(o, k, v) { if (typeof k === 'string' && /^\d+$/.test(k)) { const i = +k, b = v & 255; if (o[i] !== b) rec(o, i, 1, site(), true); } o[k] = v; return true; },
  });
  const P = new Proxy(Real, { construct(T, args) { const a = Reflect.construct(T, args); return a.length >= BIG && !window.__bmDone ? wrap(a) : a; } });
  window.Uint8Array = P; window.__bmLog = log;
};
(async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const ctx = await b.newContext({ viewport: { width: 844, height: 390 } });
  await ctx.route('https://site.test/**', async r => { const u = new URL(r.request().url()); let f = path.join(dir, decodeURIComponent(u.pathname)); if (u.pathname === '/') f = path.join(dir, 'index.html');
    try { await r.fulfill({ status: 200, body: fs.readFileSync(f), headers: { 'content-type': mime(f) } }); } catch (e) { await r.fulfill({ status: 404, body: '' }); } });
  const p = await ctx.newPage(); await p.addInitScript(WATCH);
  p.on('pageerror', e => console.log('pageerror', e.message));
  await p.goto('https://site.test/');
  await p.setInputFiles('#rom', ROM);
  await p.waitForFunction(() => !document.getElementById('play').disabled, null, { timeout: 300000 });
  await p.click('#play');
  await p.waitForFunction(() => window.__wideM && window.GbrHost && GbrHost.frames > 5, null, { timeout: 600000 });
  const log = await p.evaluate(() => { window.__bmDone = 1; return window.__bmLog; });
  await b.close();
  // owners from the page source: nearest comment above the line naming a version or a tool
  const src = fs.readFileSync(path.join(dir, 'index.html'), 'utf8').split('\n');
  const owner = (line) => { for (let i = line - 1; i >= 0 && i > line - 400; i--) { const m = /\/\/.*?\b(v\d{2,3}[a-z]?\b[^.;]{0,80}|tools\/[\w\/.-]+)/.exec(src[i] || ''); if (m) return m[1].trim(); } return 'line ' + line; };
  const own = new Map(); const ranges = [];
  for (const [off, len, line] of log) { if (!own.has(line)) own.set(line, owner(line)); ranges.push({ start: off, end: off + len, line, owner: own.get(line) }); }
  // merge touching runs from the same line
  ranges.sort((a, c) => a.line - c.line || a.start - c.start);
  const merged = []; for (const r of ranges) { const l = merged[merged.length - 1]; if (l && l.line === r.line && r.start <= l.end + 16) { l.end = Math.max(l.end, r.end); l.bytes += r.end - r.start; } else merged.push({ ...r, bytes: r.end - r.start }); }
  merged.sort((a, c) => a.start - c.start);
  // overlaps: the same byte changed by two different lines (later write wins in the page)
  const overlaps = []; const seq = log.map(([off, len, line], i) => ({ off, end: off + len, line, i })).sort((a, c) => a.off - c.off);
  for (let i = 0; i < seq.length; i++) for (let j = i + 1; j < seq.length && seq[j].off < seq[i].end; j++) if (seq[j].line !== seq[i].line) {
    const [x, y] = seq[i].i < seq[j].i ? [seq[i], seq[j]] : [seq[j], seq[i]];
    overlaps.push({ start: Math.max(x.off, y.off), end: Math.min(x.end, y.end), first: { line: x.line, owner: own.get(x.line) }, then: { line: y.line, owner: own.get(y.line) } }); }
  const key = o => o.first.owner + ' | ' + o.then.owner; const groups = {};
  for (const o of overlaps) { const k = key(o); (groups[k] = groups[k] || { first: o.first, then: o.then, ranges: [] }).ranges.push([o.start, o.end]); }
  const out = { rom: path.basename(ROM), writes: log.length, ranges: merged.map(r => ({ start: '0x' + r.start.toString(16), end: '0x' + r.end.toString(16), bytes: r.bytes, line: r.line, owner: r.owner })), overlaps: Object.values(groups).map(g => ({ ...g, bytes: g.ranges.reduce((s, [a, c]) => s + c - a, 0), ranges: g.ranges.slice(0, 8).map(([a, c]) => '0x' + a.toString(16) + '-0x' + c.toString(16)) })) };
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  console.log('writes', log.length, 'ranges', merged.length, 'overlap groups', out.overlaps.length);
  for (const g of out.overlaps) console.log('OVERLAP', g.bytes, 'bytes:', g.first.owner, '(line ' + g.first.line + ')  then  ', g.then.owner, '(line ' + g.then.line + ')', g.ranges.slice(0, 2).join(' '));
})();
