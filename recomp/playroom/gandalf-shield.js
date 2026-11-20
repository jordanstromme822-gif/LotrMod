// Gandalf's always-on Shield and Lightning Blade (Jordan, 2026-11-20; idea from a knight-mage whose hits build a barrier).
//   Shield: no cast any more (its Spirit cost in the ROM table is 0xFFFF, so the game never casts it). While Gandalf has a
//     Shield level it is always up: it holds 20 / level (+1 level from Servant of the Secret Fire), at most 120. It is full
//     when a level starts and drains all the time: 4 a second, 10% less per point of Spirit Regen, never under 1 a second.
//     The game's own absorb code does the soaking (0x0801154C: Gandalf, player block + 4 = shield object, its hit points
//     at +0x8A): the page points player + 4 at a stand-in object in unused EWRAM (FAKE, 0x90 bytes per player) instead of
//     the game's bubble, so there is no bubble picture and nothing for the game to time out. When a hit is bigger than
//     the shield, the game lets the whole hit through; the page gives back the part the shield had left.
//   Every sword strike that lands refills the shield 5 / Lightning Blade level (30 at most), Lightning Blade up or not
//     (Jordan v205: "It should no longer need lightning blade to be activated for it to generate the shield").
//   Lightning Blade (was Sword of Power): +3 damage / level for 10 s (ROM table). Casting it stuns every foe within
//     STUN_R px of Gandalf for STUN_T ticks (the game's own stun: state 0x1A, timer + 0x50, + 0x64 |= 2, as 0x08011730 does;
//     the page holds it while it lasts). Ready again 20 s after it is cast: while it waits, player + 0x1C (the
//     hero's skill table) points at a copy whose Lightning Blade costs 0xFFFF, so the game refuses it and takes no Spirit.
//   Seen: the sword glows white (FX layer), Gandalf's aura turns a softer light blue as the shield fills
//     (window.__shieldFrac), and the green XP vial at the bottom left fills light blue with the shield.
// Works in 1-player, P2 (one or two games: every write goes into every running game) and online (each page runs only
// its own player; the engine sends page writes with the buttons, so both pages see the same shield).
(() => {
  const FAKE = 0x0203FC50, TAB_A = 0x0806EE38, TAB_B = 0x09600000;   // TAB_B: copy of Gandalf's table, set by buildGame
  const CD_TICKS = 600, BASE_DRAIN = 4, STUN_R = 80, STUN_T = 120;
  const st = [{}, {}];
  let lastView = null;
  const ctx = () => {
    const mp = window.__mp, M = mp && mp.M; if (!M || !M.HEAPU8) return null;
    const linkOn = !!(M._rotk_link_on && M._rotk_link_on() && M._rotk_link_iwram);
    const online = !!mp.online, me = online ? (mp.me | 0) : 0;
    const view = linkOn ? me : -1;
    const iwOf = (g) => g < 0 ? M._rotk_iwram() : M._rotk_link_iwram(g);
    const ewOf = (g) => g < 0 ? M._rotk_ewram() : M._rotk_link_ewram(g);
    const games = linkOn ? [0, 1] : [-1];
    const H = M.HEAPU8, ib = iwOf(view), eb = ewOf(view);
    const at = (a) => (a >>> 24) === 3 ? ib + (a & 0x7fff) : (a >>> 24) === 2 ? eb + (a & 0x3ffff) : -1;
    const r8 = (a) => H[at(a)], r16 = (a) => { const o = at(a); return H[o] | H[o + 1] << 8; }, s16 = (a) => r16(a) << 16 >> 16;
    const r32 = (a) => { const o = at(a); return (H[o] | H[o + 1] << 8 | H[o + 2] << 16 | H[o + 3] << 24) >>> 0; };
    const wN = (a, v, n) => {   // little-endian write into every running game
      for (const g of games) {
        const o = (a >>> 24) === 3 ? iwOf(g) + (a & 0x7fff) : ewOf(g) + (a & 0x3ffff);
        for (let i = 0; i < n; i++) H[o + i] = (v >>> (8 * i)) & 255;
      }
    };
    return { M, online, me, r8, r16, s16, r32, wN };
  };
  const ewPtr = (p) => (p >>> 24) === 2 && (p & 0xffffff) < 0x40000;
  const objs = (c, hero) => {   // object list through +0 / +4, as impact-fx reads it
    let p = hero, n = 0; while (n++ < 400) { const nx = c.r32(p); if (!ewPtr(nx)) break; p = nx; }
    const out = []; n = 0;
    while (ewPtr(p) && n++ < 400) { out.push(p); p = c.r32(p + 4); }
    return out;
  };
  const stunnable = (c, t) => {   // tools/turn16/turn16.c stunnable(): a live foe that can be stunned now
    const e8 = c.r32(t + 0xE8), sx = c.r8(t + 0x62);
    if ((e8 & 0x801040) !== 0x1000 || !(e8 & 0x10040400) || c.s16(t + 0x5A) <= 0) return false;
    return !(sx === 0x11 || sx === 0x15 || sx === 4 || sx === 0x1B || sx === 0x13 || c.r8(t + 0x63) === 0x2F);
  };
  const stunHold = (c, t, left) => {
    if (c.r8(t + 0x62) !== 0x1A) { c.wN(t + 0x62, 0x1A, 1); c.wN(t + 0x64, c.r8(t + 0x64) | 2, 1); }
    if (c.r32(t + 0x50) < left) c.wN(t + 0x50, left, 4);
  };
  let stunFx = [];
  const tick = () => {
    const c = ctx(); if (!c) return;
    if (c.online && !window.__mp.sync) return;   // an online engine that can't send page writes: leave the game alone
    if (c.r8(0x030041B0) !== 1) {   // not in a level: the real table back (the Skills page shows its costs)
      for (const p of [0, 1]) { const P = 0x03003C00 + 0x1AC * p; if (c.r32(P + 0x1C) === TAB_B) c.wN(P + 0x1C, TAB_A, 4); }
      return;
    }
    const now = c.r32(0x030041A4), count = Math.min(2, c.r8(0x03003F58) || 1);
    const players = c.online ? [c.me] : [0, 1].filter((p) => p < Math.max(count, 1) || ewPtr(c.r32(0x03003C00 + 0x1AC * p)));
    let shown = null;
    for (const p of players) {
      const P = 0x03003C00 + 0x1AC * p, hero = c.r32(P), s = st[p];
      if (!ewPtr(hero) || c.r8(P + 0x19F) !== 3) { s.hero = 0; continue; }
      const F = FAKE + 0x90 * p, bonus = c.s16(P + 0x14C) > 0 ? 1 : 0;
      const shL = c.r8(P + 0x172) << 24 >> 24, lbL = c.r8(P + 0x170) << 24 >> 24;
      const dt = s.t === undefined ? 0 : Math.max(0, Math.min(30, (now - s.t) | 0)); s.t = now;
      // ---- Lightning Blade: up while the hero object's +0x99 bit 0 is set (the cast handler 0x08044C91 sets it) ----
      const lbOn = (c.r8(hero + 0x99) & 1) !== 0 && lbL > 0;
      const hx = c.s16(hero + 0xAE), hy = c.s16(hero + 0xB2);
      const stun = s.stun || (s.stun = new Map());
      if (lbOn && !s.lbOn) {   // just cast: stun every foe near Gandalf
        s.cdEnd = (now + CD_TICKS) | 0;
        for (const o of objs(c, hero)) {
          if (o === hero || !stunnable(c, o)) continue;
          const dx = c.s16(o + 0xAE) - hx, dy = c.s16(o + 0xB2) - hy;
          if (dx * dx + dy * dy > STUN_R * STUN_R) continue;
          stun.set(o, (now + STUN_T) | 0); stunHold(c, o, STUN_T);
        }
        if (p === (c.online ? c.me : 0)) window.__lbCast = { x: hx, y: hy, t: performance.now() };
      }
      s.lbOn = lbOn;
      const fx = [];
      for (const [o, end] of stun) {
        const left = (end - now) | 0;
        if (left <= 0 || !ewPtr(o) || c.s16(o + 0x5A) <= 0 || !(c.r8(o + 0x62) === 0x1A || stunnable(c, o))) { stun.delete(o); continue; }
        stunHold(c, o, left);
        fx.push([c.s16(o + 0xAE), c.s16(o + 0xB2)]);
      }
      if (p === (c.online ? c.me : 0)) stunFx = fx;
      const tab = c.r32(P + 0x1C), cool = s.cdEnd !== undefined && ((s.cdEnd - now) | 0) > 0;
      const want = cool ? TAB_B : TAB_A;
      if ((tab === TAB_A || tab === TAB_B) && tab !== want && window.__gsTabB) c.wN(P + 0x1C, want, 4);
      s.cdLeft = cool ? ((s.cdEnd - now) | 0) / 30 : 0;
      // ---- Shield ----
      if (shL <= 0) { if (c.r32(P + 4) === F) c.wN(P + 4, 0, 4); s.hero = hero; s.max = 0; continue; }
      const max = Math.min(120, 20 * Math.min(6, shL + bonus));
      const p4 = c.r32(P + 4);
      if (p4 !== F) {
        if (p4 !== 0) { s.hero = hero; continue; }   // a real effect object (a potion glow etc.) holds the slot for now
        c.wN(F + 0x62, 0, 1); c.wN(P + 4, F, 4);
      }
      let S = c.s16(F + 0x8A), hp = c.s16(P + 0x17C);
      if (hero !== s.hero || !s.max) { S = max; s.acc = 0; s.prevS = max; s.prevHp = hp; s.swing = null; s.hp = new Map(); }
      s.hero = hero; s.max = max;
      // the game let a too-big hit through whole: give back what the shield still had
      if (s.prevS > 0 && S <= 0 && hp > 0 && hp < s.prevHp) {
        const back = Math.min(s.prevS, s.prevHp - hp), mx = c.s16(P + 0xD0) || 9999;
        hp = Math.min(mx, hp + back); c.wN(P + 0x17C, hp, 2);
      }
      // drain, slowed by Spirit Regen (stat 30, player + 0xE0)
      const sr = Math.max(0, c.s16(P + 0xE0)), rate = Math.max(1, BASE_DRAIN * (1 - 0.1 * sr));
      s.acc = (s.acc || 0) + dt * rate / 30;
      const d = Math.floor(s.acc); s.acc -= d; S = Math.max(0, S - d);
      // strikes: a foe next to Gandalf loses hit points and no other hero stands closer to it; one refill per 10 game
      // ticks (a swing), so a sweep through several foes counts once. The refill follows Lightning Blade's level.
      const gain = Math.min(30, 5 * Math.min(6, lbL + bonus));
      const others = [0, 1].filter((q) => q !== p).map((q) => c.r32(0x03003C00 + 0x1AC * q)).filter((h2) => ewPtr(h2) && h2 !== hero)
        .map((h2) => [c.s16(h2 + 0xAE), c.s16(h2 + 0xB2)]);
      const hpm = s.hp || (s.hp = new Map()), seen = new Map();
      for (const o of objs(c, hero)) {
        if (o === hero || c.r32(o + 0x14) === 0x0802f131) continue;
        const ohp = c.s16(o + 0x5A); seen.set(o, ohp);
        const was = hpm.get(o);
        if (was === undefined || ohp >= was || was <= 0 || lbL <= 0 || ((now - (s.lastStrike || -99)) | 0) < 10) continue;
        const ex = c.s16(o + 0xAE), ey = c.s16(o + 0xB2), dx = ex - hx, dy = ey - hy;
        if (Math.abs(dx) > 48 || Math.abs(dy) > 40) continue;
        const dm = dx * dx + dy * dy;
        if (others.some(([x2, y2]) => (ex - x2) ** 2 + (ey - y2) ** 2 < dm)) continue;
        s.lastStrike = now;
        S = Math.min(max, S + gain);
        if (p === (c.online ? c.me : 0)) window.__lbStrike = { x: ex, y: ey, t: performance.now() };
      }
      s.hp = seen;
      S = Math.min(max, S);
      if (S !== c.s16(F + 0x8A)) c.wN(F + 0x8A, S & 0xffff, 2);
      if (c.s16(F + 0x8C) !== max) c.wN(F + 0x8C, max, 2);
      s.prevS = S; s.prevHp = hp;
      if (p === (c.online ? c.me : 0)) shown = { frac: max ? S / max : 0, S, max, lb: lbOn, hx, hy };
    }
    window.__gsShown = shown;
    window.__shieldFrac = shown ? shown.frac : 0;
    window.__lbGlow = shown && shown.lb ? 1 : 0;
  };
  window.__lbLeft = () => { const c = ctx(); const p = c && c.online ? c.me : 0; return (st[p] && st[p].cdLeft) || 0; };
  window.__gsState = () => st;
  setInterval(() => { try { tick(); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("gs: " + (e && e.message || e)); } }, 50);

  // ---- picture: shield in the XP vial, white sword glow ----
  let cv = null, cx = null;
  const ensure = (host) => {
    if (cv && cv.previousElementSibling && cv.parentElement === host.parentElement) return true;
    if (!host || !host.parentElement) return false;
    if (cv) cv.remove();
    cv = document.createElement("canvas"); cv.id = "gsCanvas";
    cv.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:4";
    const fx = document.getElementById("fxCanvas");
    (fx && fx.parentElement === host.parentElement ? fx : host).after(cv); cx = cv.getContext("2d"); return true;
  };
  const prev = window.__fxView;
  window.__fxView = (w, h, sx, sy, sw, sh, dest, CW, CH, host) => {
    lastView = window.__gsView = { w, h, sx, sy, sw, sh, k: dest[2] / sw, ky: dest[3] / sh, ox: dest[0], oy: dest[1], CW, CH, host };
    if (prev) return prev(w, h, sx, sy, sw, sh, dest, CW, CH, host);
  };
  // XP vial on the game picture: the HUD sits at the bottom of the picture, its 240 px centred across the width
  // (measured headless, 320 x 240 picture): inside of the vial x 4.5..17.2, y 142.5..160 of that 240 x 160 strip.
  const VIAL = { x: 4.5, y: 142.5, w: 12.7, h: 17.5 };
  let glowT = 0;
  const draw = (t) => {
    requestAnimationFrame(draw);
    const v = lastView, g = window.__gsShown;
    if (!v || !v.host) return;
    if (!ensure(v.host)) return;
    if (cv.width !== v.CW || cv.height !== v.CH) { cv.width = v.CW; cv.height = v.CH; }
    cx.setTransform(1, 0, 0, 1, 0, 0); cx.clearRect(0, 0, cv.width, cv.height);
    if (!g || window.__fxOff) return;
    const VI = window.__gsVial || VIAL;
    const gx = (v.w - 240) / 2 + VI.x, gy = v.h - 160 + VI.y;
    const X = (x) => v.ox + (x - v.sx) * v.k, Y = (y) => v.oy + (y - v.sy) * v.ky;
    const x0 = X(gx), x1 = X(gx + VI.w), yb = Y(gy + VI.h), yt = Y(gy);
    if (g.frac > 0.001) {
      const top = yb - (yb - yt) * g.frac;
      const gr = cx.createLinearGradient(0, top, 0, yb);
      gr.addColorStop(0, "rgba(190,230,255,0.85)"); gr.addColorStop(1, "rgba(70,150,255,0.8)");
      cx.fillStyle = gr; cx.fillRect(x0, top, x1 - x0, yb - top);
      cx.globalCompositeOperation = "lighter";
      const pulse = 0.5 + 0.5 * Math.sin(t / 380);
      const r = (x1 - x0) * (1.3 + 0.25 * pulse), mx = (x0 + x1) / 2, my = (top + yb) / 2;
      const rg = cx.createRadialGradient(mx, my, 0, mx, my, r);
      rg.addColorStop(0, `rgba(120,190,255,${0.35 * g.frac})`); rg.addColorStop(1, "rgba(120,190,255,0)");
      cx.fillStyle = rg; cx.fillRect(mx - r, my - r * 1.6, r * 2, r * 3.2);
      cx.globalCompositeOperation = "source-over";
    }
    // Lightning Blade: a white glow on the sword arm and short crackles while it is up, a white flash on each strike
    const cam = window.__FX && window.__FX.cam;
    if (cam && g.lb) {
      glowT += 1;
      const hx = X(g.hx - cam[0]), hy = Y(g.hy - cam[1] - 14), k = v.k;
      cx.globalCompositeOperation = "lighter";
      const r = 9 * k * (0.9 + 0.15 * Math.sin(t / 70));
      const rg = cx.createRadialGradient(hx + 5 * k, hy, 0, hx + 5 * k, hy, r);
      rg.addColorStop(0, "rgba(255,255,255,0.75)"); rg.addColorStop(0.35, "rgba(235,245,255,0.35)"); rg.addColorStop(1, "rgba(220,235,255,0)");
      cx.fillStyle = rg; cx.fillRect(hx + 5 * k - r, hy - r, r * 2, r * 2);
      if ((glowT & 7) < 3) {
        cx.strokeStyle = "rgba(255,255,255,0.85)"; cx.lineWidth = Math.max(1, 0.6 * k); cx.beginPath();
        let px = hx + 5 * k, py = hy - 6 * k; cx.moveTo(px, py);
        for (let i = 0; i < 4; i++) { px += (Math.random() - 0.5) * 6 * k; py += 3 * k; cx.lineTo(px, py); }
        cx.stroke();
      }
      cx.globalCompositeOperation = "source-over";
    }
    // Lightning Blade cast: a white-blue ring out to the stun range; stunned foes crackle while they are held
    const lc = window.__lbCast;
    if (cam && lc && performance.now() - lc.t < 400) {
      const f = (performance.now() - lc.t) / 400, ex = X(lc.x - cam[0]), ey = Y(lc.y - cam[1] - 8), r = STUN_R * f * v.k;
      cx.globalCompositeOperation = "lighter";
      cx.strokeStyle = `rgba(220,240,255,${0.8 * (1 - f)})`; cx.lineWidth = Math.max(1.5, 2.5 * v.k * (1 - f));
      cx.beginPath(); cx.ellipse(ex, ey, r, r * 0.6, 0, 0, Math.PI * 2); cx.stroke();
      cx.globalCompositeOperation = "source-over";
    }
    if (cam && stunFx.length) {
      cx.globalCompositeOperation = "lighter";
      cx.strokeStyle = "rgba(200,230,255,0.9)"; cx.lineWidth = Math.max(1, 0.5 * v.k);
      for (const [sx, sy] of stunFx) {
        const ex = X(sx - cam[0]), ey = Y(sy - cam[1] - 22), k = v.k;
        const rg = cx.createRadialGradient(ex, ey, 0, ex, ey, 7 * k);
        rg.addColorStop(0, "rgba(170,215,255,0.45)"); rg.addColorStop(1, "rgba(170,215,255,0)");
        cx.fillStyle = rg; cx.fillRect(ex - 7 * k, ey - 7 * k, 14 * k, 14 * k);
        if (Math.random() < 0.6) {
          cx.beginPath(); let px = ex + (Math.random() - 0.5) * 8 * k, py = ey - 4 * k; cx.moveTo(px, py);
          for (let i = 0; i < 3; i++) { px += (Math.random() - 0.5) * 5 * k; py += 3 * k; cx.lineTo(px, py); }
          cx.stroke();
        }
      }
      cx.globalCompositeOperation = "source-over";
    }
    const sk = window.__lbStrike;
    if (cam && sk && performance.now() - sk.t < 220) {
      const f = (performance.now() - sk.t) / 220, ex = X(sk.x - cam[0]), ey = Y(sk.y - cam[1] - 12), r = (10 + 14 * f) * v.k;
      cx.globalCompositeOperation = "lighter";
      const rg = cx.createRadialGradient(ex, ey, 0, ex, ey, r);
      rg.addColorStop(0, `rgba(255,255,255,${0.9 * (1 - f)})`); rg.addColorStop(1, "rgba(200,225,255,0)");
      cx.fillStyle = rg; cx.fillRect(ex - r, ey - r, r * 2, r * 2);
      cx.globalCompositeOperation = "source-over";
    }
  };
  requestAnimationFrame(draw);
})();
