// Impact effects (Jordan, 2026-11-17: "I love Gandalf's aura, can you do a full overhaul on animations to make them feel modern").
// Our own effects, drawn at full screen resolution on a canvas over the game picture (no GBA limits):
//   swing trails when a hero attacks, hit flash + sparks + shock ring + damage numbers when an enemy loses hit points,
//   a death burst (embers, smoke, a rising wisp) when an enemy's hit points reach 0, a red pulse and shake when a hero is
//   hurt, light dust under walking heroes, and a short screen shake on big hits.
// Game memory it reads (checked headless, level 38):
//   object list from the player block's hero (word at IWRAM 0x3C00), next/prev at +0/+4; update function +0x14
//   (heroes 0x080236B9, or 0x0809F001 with the 16-facing hook; ground items 0x0802F131 skipped); hit points +0x5A (int16);
//   state +0x62 (heroes: 1 stand, 2 walk, 3 attack, 4 dead, 6 hurt; enemies: 6 hurt, 17 dying); x/y +0xAE/+0xB2;
//   camera 0x030020F8/FC; P1 hit points = player block +0x17C, hero id +0x19F (3 = Gandalf).
// Always on (Jordan: features he wants are on, no settings). window.__fxOff = true hides it for tests.
(() => {
  const FX = { parts: [], nums: [], rings: [], flashes: [], slashes: [], shake: 0, hurt: 0, objs: new Map(), cam: [0, 0],
    view: null, cv: null, ctx: null, php: null, hid: -1, live: false, lastT: 0, glow: new Map() };
  window.__FX = FX;
  const HERO = new Set([0x080236b9, 0x0809f001]);
  const rnd = (a, b) => a + Math.random() * (b - a);
  const read = (w, h) => {
    const M = window.__wideM; if (!M || !M._rotk_iwram) return null;
    const H8 = M.HEAPU8, ib = M._rotk_iwram(), eb = M._rotk_ewram(), dv = new DataView(H8.buffer);
    if (H8[ib + 0x41B0] !== 1) return null;
    const at = (q) => q >= 0x2000000 && q < 0x2040000 ? eb + (q - 0x2000000) : q >= 0x3000000 && q < 0x3008000 ? ib + (q - 0x3000000) : 0;
    const r32 = (q) => { const o = at(q); return o ? dv.getUint32(o, true) : 0; };
    let p = dv.getUint32(ib + 0x3C00, true), n = 0; if (!at(p)) return null;
    while (n++ < 400) { const nx = r32(p); if (!at(nx)) break; p = nx; }
    const list = [];
    n = 0; while (at(p) && n++ < 400) {
      const o = at(p), fn = dv.getUint32(o + 0x14, true);
      if (fn !== 0x0802f131) list.push({ p, hero: HERO.has(fn), hp: dv.getInt16(o + 0x5A, true), st: H8[o + 0x62], x: dv.getInt16(o + 0xAE, true), y: dv.getInt16(o + 0xB2, true) });
      p = r32(p + 4);
    }
    return { list, cam: [dv.getInt32(ib + 0x20F8, true) - (w - 240) / 2, dv.getInt32(ib + 0x20FC, true) - (h - 160) / 2],
      php: dv.getInt16(ib + 0x3C00 + 0x17C, true), hid: H8[ib + 0x3C00 + 0x19F], p1: dv.getUint32(ib + 0x3C00, true) };
  };
  // Colours: Gandalf's effects are pale blue like his aura; everyone else gets warm steel and gold.
  const PAL = (hid) => hid === 3 ? { core: [235, 245, 255], edge: [120, 170, 255], spark: [[255, 255, 255], [150, 200, 255]] }
    : { core: [255, 250, 235], edge: [255, 190, 90], spark: [[255, 245, 210], [255, 140, 40]] };
  const cap = (a, n) => { if (a.length > n) a.splice(0, a.length - n); };
  const add = (a, o) => { a.push(o); };
  const sparks = (x, y, dx, dy, n, spread, sp0, sp1, pal, life = 0.4) => {
    for (let i = 0; i < n; i++) {
      const a = Math.atan2(dy, dx) + rnd(-spread, spread), s = rnd(sp0, sp1);
      add(FX.parts, { k: 0, x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s - rnd(10, 40), g: 260, t: 0, life: rnd(life * 0.6, life * 1.3),
        c0: pal.spark[0], c1: pal.spark[1], w: rnd(0.9, 1.6) });
    }
  };
  const hit = (o, dmg, src, dead) => {
    const pal = PAL(FX.hid), x = o.x, y = o.y - 12;
    let dx = 0, dy = -1; if (src) { dx = x - src.x; dy = y - (src.y - 12); const l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l; }
    const big = dmg >= 15 || dead;
    add(FX.flashes, { x, y, t: 0, life: big ? 0.16 : 0.11, r: big ? 22 : 15, c: pal.core });
    add(FX.flashes, { x, y: y + 2, t: 0, life: 0.09, r: 9, c: [255, 255, 255], body: 1 });
    add(FX.rings, { x, y, t: 0, life: big ? 0.36 : 0.26, r0: 3, r1: big ? 30 : 18, c: pal.edge, w: big ? 2.2 : 1.5 });
    sparks(x, y, dx, dy, 8 + Math.min(14, dmg | 0), 1.1, 70, 210, pal);
    add(FX.nums, { x: x + rnd(-4, 4), y: y - 10, t: 0, life: 0.95, v: dmg, big, hurt: false });
    FX.shake = Math.max(FX.shake, big ? 4 : 2);
    if (dead) death(o, pal);
  };
  const death = (o, pal) => {
    const x = o.x, y = o.y - 10;
    add(FX.rings, { x, y: y + 6, t: 0, life: 0.5, r0: 6, r1: 40, c: [255, 160, 80], w: 3 });
    for (let i = 0; i < 26; i++) add(FX.parts, { k: 1, x: x + rnd(-8, 8), y: y + rnd(-10, 8), vx: rnd(-25, 25), vy: rnd(-70, -20), g: -15, t: 0,
      life: rnd(0.8, 1.7), c0: [255, 220, 120], c1: [200, 50, 20], w: rnd(0.8, 1.6), ph: rnd(0, 6) });
    for (let i = 0; i < 7; i++) add(FX.parts, { k: 2, x: x + rnd(-7, 7), y: y + rnd(-6, 6), vx: rnd(-12, 12), vy: rnd(-22, -6), g: 0, t: 0,
      life: rnd(0.7, 1.1), r0: rnd(3, 5), r1: rnd(10, 16), a: rnd(0.25, 0.4) });
    add(FX.parts, { k: 3, x, y, vx: 0, vy: -38, g: -20, t: 0, life: 1.2, c0: pal.core, c1: pal.edge });
    FX.shake = Math.max(FX.shake, 6);
  };
  const swing = (o, list) => {
    const pal = PAL(FX.hid), x = o.x, y = o.y - 13;
    let best = null, bd = 56;
    for (const e of list) if (!e.hero && e.hp > 0) { const d = Math.hypot(e.x - o.x, e.y - o.y); if (d < bd) { bd = d; best = e; } }
    let ang = best ? Math.atan2(best.y - o.y, best.x - o.x) : (o.fx || o.fy) ? Math.atan2(o.fy, o.fx) : Math.PI / 2;
    add(FX.slashes, { x, y, ang, t: 0, life: 0.2, r: 21, span: 2.5, dir: Math.random() < 0.5 ? 1 : -1, c0: pal.core, c1: pal.edge });
  };
  const hurtHero = (o) => {
    FX.hurt = 1; FX.shake = Math.max(FX.shake, 4.5);
    sparks(o.x, o.y - 14, 0, -1, 10, Math.PI, 40, 140, { spark: [[255, 200, 190], [220, 30, 30]] }, 0.35);
  };
  const dust = (o) => {
    for (let i = 0; i < 2; i++) add(FX.parts, { k: 2, x: o.x + rnd(-4, 4), y: o.y - 1, vx: rnd(-10, 10), vy: rnd(-8, -2), g: 0, t: 0,
      life: rnd(0.45, 0.6), r0: 1.5, r1: rnd(5, 7), a: 0.16, dust: 1 });
  };
  FX.tick = (w, h) => {
    const r = window.__fxOff ? null : read(w, h);
    if (!r) { FX.objs.clear(); FX.php = null; FX.live = false; return; }
    FX.live = true; FX.cam = r.cam; FX.hid = r.hid;
    const now = performance.now(), seen = new Set(), heroes = r.list.filter((o) => o.hero);
    for (const o of r.list) {
      seen.add(o.p);
      const q = FX.objs.get(o.p);
      if (o.hero) {
        if (q) {
          const mx = o.x - q.x, my = o.y - q.y;
          if (mx || my) { o.fx = mx; o.fy = my; } else { o.fx = q.fx; o.fy = q.fy; }
          o.dust = q.dust;
          if (o.st === 3 && q.st !== 3) swing(o, r.list);
          if (o.st === 6 && q.st !== 6) { hurtHero(o); FX.hurtT = now; }
          if (o.st === 2 && (mx || my) && now - (q.dust || 0) > 240) { dust(o); o.dust = now; }
        }
      } else if (q && o.hp < q.hp && q.hp > 0 && q.hp - o.hp < 5000 && Math.abs(o.x - q.x) < 40) {
        let src = null, bd = 1e9;
        for (const hh of heroes) { const d = Math.hypot(hh.x - o.x, hh.y - o.y); if (d < bd) { bd = d; src = hh; } }
        hit(o, q.hp - o.hp, src, o.hp <= 0);
      }
      FX.objs.set(o.p, o);
    }
    for (const k of FX.objs.keys()) if (!seen.has(k)) FX.objs.delete(k);
    if (FX.php !== null && r.php < FX.php && FX.php - r.php < 1000 && (heroes.some((o) => o.st === 6) || now - (FX.hurtT || 0) < 700)) {
      const me = r.list.find((o) => o.p === r.p1) || heroes[0];
      if (me) add(FX.nums, { x: me.x + rnd(-3, 3), y: me.y - 30, t: 0, life: 1.0, v: FX.php - r.php, big: false, hurt: true });
    }
    FX.php = r.php;
    cap(FX.parts, 600); cap(FX.nums, 40); cap(FX.rings, 40); cap(FX.flashes, 40); cap(FX.slashes, 12);
  };
  // Where the game picture sits on the screen canvas; called by the page for every new game picture.
  window.__fxView = (w, h, sx, sy, sw, sh, dest, CW, CH, host) => {
    FX.view = { sx, sy, sw, sh, k: dest[2] / sw, ky: dest[3] / sh, ox: dest[0], oy: dest[1], CW, CH, host };
    try { FX.tick(w, h); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("fx: " + (e && e.message || e)); }
  };
  const ensure = (host) => {
    if (FX.cv && FX.cv.previousElementSibling === host) return true;
    if (!host || !host.parentElement) return false;
    if (FX.cv) FX.cv.remove();
    const c = document.createElement("canvas"); c.id = "fxCanvas";
    c.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:3";
    host.after(c); FX.cv = c; FX.ctx = c.getContext("2d"); return true;
  };
  // Soft round glow pictures, one per colour, drawn with "lighter" so they only add light.
  const glow = (c) => {
    const key = c.join(","); let g = FX.glow.get(key); if (g) return g;
    g = document.createElement("canvas"); g.width = g.height = 64; const x = g.getContext("2d"), gr = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    gr.addColorStop(0, `rgba(${key},1)`); gr.addColorStop(0.25, `rgba(${key},0.6)`); gr.addColorStop(1, `rgba(${key},0)`);
    x.fillStyle = gr; x.fillRect(0, 0, 64, 64); FX.glow.set(key, g); return g;
  };
  const mix = (a, b, t) => [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * t));
  const render = (dt) => {
    const v = FX.view;
    if (!v || !v.host || !ensure(v.host)) return;
    const c = FX.cv, x = FX.ctx;
    if (c.width !== v.CW || c.height !== v.CH) { c.width = v.CW; c.height = v.CH; }
    x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, c.width, c.height);
    const empty = !FX.parts.length && !FX.nums.length && !FX.rings.length && !FX.flashes.length && !FX.slashes.length && FX.hurt <= 0 && FX.shake <= 0;
    if (!FX.live || window.__fxOff) { FX.parts.length = FX.nums.length = FX.rings.length = FX.flashes.length = FX.slashes.length = 0; FX.hurt = FX.shake = 0; }
    // Screen shake: the game picture and this layer move together, a few screen pixels, fading fast.
    let shx = 0, shy = 0;
    if (FX.shake > 0.05) { const a = FX.shake * (window.devicePixelRatio > 1 ? 1 : 0.8); shx = rnd(-a, a); shy = rnd(-a, a); FX.shake *= Math.exp(-dt * 16); } else FX.shake = 0;
    const tr = FX.shake ? `${shx.toFixed(1)}px ${shy.toFixed(1)}px` : "";
    if (v.host.style.translate !== tr) { v.host.style.translate = tr; c.style.translate = tr; }
    if (empty) return;
    const k = v.k, X = (gx) => v.ox + (gx - FX.cam[0] - v.sx) * k, Y = (gy) => v.oy + (gy - FX.cam[1] - v.sy) * v.ky;
    x.save(); x.beginPath(); x.rect(v.ox, v.oy, v.sw * k, v.sh * v.ky); x.clip();
    // Smoke and dust first (normal blend), then light (additive).
    x.globalCompositeOperation = "source-over";
    for (const p of FX.parts) if (p.k === 2) {
      const f = p.t / p.life, r = (p.r0 + (p.r1 - p.r0) * Math.sqrt(f)) * k, a = p.a * (1 - f) * (f < 0.15 ? f / 0.15 : 1);
      x.fillStyle = p.dust ? `rgba(196,182,156,${a})` : `rgba(40,34,32,${a})`; x.beginPath(); x.arc(X(p.x), Y(p.y), r, 0, 6.283); x.fill();
    }
    x.globalCompositeOperation = "lighter";
    for (const s of FX.slashes) {
      const f = s.t / s.life, head = Math.min(1, f * 2.2), tail = Math.max(0, f * 2.2 - 1.2), cx = X(s.x), cy = Y(s.y);
      const a0 = s.ang - s.span / 2 * s.dir, steps = 18, R = s.r * k * (0.95 + 0.15 * f);
      const pts = [];
      for (let i = 0; i <= steps; i++) {
        const u = tail + (head - tail) * i / steps, a = a0 + s.span * s.dir * u, th = Math.sin(Math.PI * (i / steps)) * 0.42 * (1 - f * 0.6);
        pts.push([Math.cos(a), Math.sin(a), th * 0.75]);
      }
      if (head - tail < 0.02) continue;
      for (let pass = 0; pass < 2; pass++) {
        x.beginPath();
        pts.forEach(([ca, sa], i) => { const px = cx + ca * R, py = cy + sa * R * 0.8; i ? x.lineTo(px, py) : x.moveTo(px, py); });
        for (let i = pts.length - 1; i >= 0; i--) { const [ca, sa, th] = pts[i], rr = R * (1 - th * (pass ? 0.45 : 1)); x.lineTo(cx + ca * rr, cy + sa * rr * 0.8); }
        x.closePath();
        const col = pass ? s.c0 : s.c1, al = (1 - f) * (pass ? 0.8 : 0.5);
        x.fillStyle = `rgba(${col.join(",")},${al})`; x.fill();
      }
    }
    for (const fl of FX.flashes) {
      const f = fl.t / fl.life, r = fl.r * k * (0.7 + 0.6 * f), a = (1 - f) * (1 - f);
      x.globalAlpha = a * (fl.body ? 0.55 : 0.9); x.drawImage(glow(fl.c), X(fl.x) - r, Y(fl.y) - r, r * 2, r * 2);
    }
    x.globalAlpha = 1;
    for (const rg of FX.rings) {
      const f = rg.t / rg.life, e = 1 - Math.pow(1 - f, 3), r = (rg.r0 + (rg.r1 - rg.r0) * e) * k;
      x.strokeStyle = `rgba(${rg.c.join(",")},${(1 - f) * 0.8})`; x.lineWidth = rg.w * k * (1 - f * 0.7);
      x.beginPath(); x.ellipse(X(rg.x), Y(rg.y), r, r * 0.62, 0, 0, 6.283); x.stroke();
    }
    x.lineCap = "round";
    for (const p of FX.parts) {
      if (p.k === 2) continue;
      const f = p.t / p.life, col = mix(p.c0, p.c1, Math.min(1, f * 1.4)), px = X(p.x), py = Y(p.y);
      if (p.k === 0) {   // spark: a short bright streak along its motion
        const L = 0.04, a = 1 - f;
        x.strokeStyle = `rgba(${col.join(",")},${a})`; x.lineWidth = p.w * k * (1 - f * 0.5);
        x.beginPath(); x.moveTo(px, py); x.lineTo(px - p.vx * L * k, py - p.vy * L * v.ky); x.stroke();
      } else if (p.k === 1) {   // ember: a glowing dot that flickers as it rises
        const fl = 0.65 + 0.35 * Math.sin(p.t * 22 + p.ph), r = (2.4 + 1.6 * fl) * p.w * k * (1 - f * 0.5);
        x.globalAlpha = (1 - f) * fl; x.drawImage(glow(col), px - r, py - r, r * 2, r * 2); x.globalAlpha = 1;
      } else if (p.k === 3) {   // wisp: a pale column of light lifting out of the fallen enemy
        const a = Math.sin(Math.PI * Math.min(1, f * 1.2)) * 0.8, rw = 6 * k, rh = 18 * k * (0.6 + f);
        x.globalAlpha = a; x.drawImage(glow(p.c1), px - rw, py - rh, rw * 2, rh * 2); x.drawImage(glow(p.c0), px - rw * 0.45, py - rh * 0.7, rw * 0.9, rh * 1.4); x.globalAlpha = 1;
      }
    }
    // Damage numbers: pop in big, settle, float up and fade. Hero damage is red.
    x.globalCompositeOperation = "source-over"; x.textAlign = "center"; x.textBaseline = "middle"; x.lineJoin = "round";
    for (const n of FX.nums) {
      const f = n.t / n.life, pop = 1 + 0.7 * Math.exp(-n.t * 16) * Math.cos(n.t * 30), up = (1 - Math.pow(1 - Math.min(1, f * 1.3), 3)) * 16;
      const size = (n.big ? 12 : 9) * k * pop, a = f > 0.65 ? 1 - (f - 0.65) / 0.35 : 1;
      x.globalAlpha = a; x.font = `700 ${size.toFixed(1)}px Cinzel, Georgia, serif`;
      const px = X(n.x), py = Y(n.y - up);
      x.lineWidth = Math.max(2, size * 0.18); x.strokeStyle = "rgba(10,6,4,0.9)"; x.strokeText(String(n.v), px, py);
      const g = x.createLinearGradient(0, py - size / 2, 0, py + size / 2);
      if (n.hurt) { g.addColorStop(0, "#ffb3a6"); g.addColorStop(1, "#e0281e"); }
      else if (n.big) { g.addColorStop(0, "#fff6c8"); g.addColorStop(1, "#ff9a2a"); }
      else { g.addColorStop(0, "#ffffff"); g.addColorStop(1, "#ffd98a"); }
      x.fillStyle = g; x.fillText(String(n.v), px, py);
    }
    x.globalAlpha = 1; x.restore();
    // Hurt: the screen edges pulse red for a moment.
    if (FX.hurt > 0.01) {
      const g = x.createRadialGradient(c.width / 2, c.height / 2, Math.min(c.width, c.height) * 0.35, c.width / 2, c.height / 2, Math.max(c.width, c.height) * 0.75);
      g.addColorStop(0, "rgba(160,0,0,0)"); g.addColorStop(1, `rgba(170,10,10,${0.45 * FX.hurt})`);
      x.fillStyle = g; x.fillRect(0, 0, c.width, c.height); FX.hurt *= Math.exp(-dt * 4.5);
    } else FX.hurt = 0;
  };
  const step = (dt) => {
    for (const a of [FX.parts, FX.nums, FX.rings, FX.flashes, FX.slashes]) {
      let j = 0;
      for (const p of a) {
        p.t += dt;
        if (p.vx !== undefined) { p.vy += (p.g || 0) * dt; p.x += p.vx * dt; p.y += p.vy * dt; if (p.k === 0) { p.vx *= Math.exp(-dt * 3); } }
        if (p.t < p.life) a[j++] = p;
      }
      a.length = j;
    }
  };
  const frame = (t) => {
    requestAnimationFrame(frame);
    if (window.__fxManual) return;   // tests step time by hand with __FX.advance(dt)
    const dt = FX.lastT ? Math.min(0.05, (t - FX.lastT) / 1000) : 0.016; FX.lastT = t;
    if (!FX.view) return;
    step(dt); render(dt);
  };
  FX.advance = (dt) => { step(dt); render(dt); };
  requestAnimationFrame(frame);
})();
