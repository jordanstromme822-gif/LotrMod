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
//   Blinding Aura (v206): casting it refills the shield to full; the game's white burst picture is moved out of sight and
//     Gandalf's own aura (shader) swells to twice its size and brightens instead; foes from the game's 60 px out to
//     120 px take the same hit (10 + 2 / level) from the page and are held 3 s (the game blinds the near ones 3 s).
//     v214 (Jordan, 2026-11-20: "it should be showing a countdown ... and its new animation"): the burst is also drawn on
//     this page's own effects layer (a white-gold flash, a ring out to the full reach and light rays), so it shows at
//     every graphics setting, not only in the HD shader. Ready again BA_CD ticks (15 s) after a cast: tables E-H are
//     A-D with Blinding Aura at 0xFFFF, so the game refuses it and takes no Spirit, and its button counts down.
//     The cast is seen from the cast flags (player + 0x1A3 = 3, + 0x1A5 bit 0), because the hero's + 0x99 bit 3
//     stays set ~9 s after a cast.
//   Dash (was Summon Gwaihir, v206): the ROM entry casts like Lightstrike, so the handler waits for the cast animation;
//     the page sees the cast (player + 0x1A3 = 4, + 0x1A5 bit 0), clears it before Gwaihir comes and dashes instead:
//     hit-reaction state 6 with a set velocity moves the hero through the game's own wall checks, DASH_T ticks at
//     DASH_V px a tick, through foes. While Lightning Blade is up each foe dashed through gives 10 Shield. 4 s cooldown
//     through tables C / D (Dash costs 0xFFFF there).
//     v218 (Jordan, 2026-11-20: "it should be redrawn as if he's being pulled forward by the light using his aura and
//     not make the damage sound effect"): state 6 is the game's hit reaction, and its handler (0x080244A0) starts a hit
//     (hurt pose = anim 3, hurt sound 0x08046EEC from the hero's sound table 0x080585D4 + 2, 15 invulnerable ticks)
//     whenever + 0xE8 bit 0x20 is clear. The page now sets that bit and keeps its timer (+ 0x56) up, so the handler
//     only "continues" a hit: no sound, no hurt pose. + 0x54 (hit ticks left) is kept above 0 so the game keeps moving
//     the hero; at the end it is 0, so the game itself goes back to standing (state 1, stand anim). Gandalf holds the
//     staff-raised frame (DASH_F) of his cast animation, and the effects layer draws a light ahead of him with a
//     beam from his staff and motes of light streaming into it, his aura swells, and the light is taken in at the end.
//   Wisps (was Lightstrike, v222; Jordan, 2026-11-20): no cooldown, but at most one cast every half second (WISP_GAP
//     ticks: tables I-P at 0x09601000 + 0x100 * i are A-H with Wisps at 0xFFFF, so the game refuses it and takes no
//     Spirit). Costs WISP_COST Spirit. The game never casts this slot (v226: cost 0xFFFF in every table, so no Gwaihir
//     even with a staff): the page reads the Quick Skill press itself (L held + A / B / R new, as 0x08043350 does),
//     makes the game's checks and takes the Spirit (v227: held, not just new, so holding it recasts each WISP_GAP). A game cast that still shows up (player + 0x1A3 = 1, + 0x1A5 bit 0)
//     is cleared before its handler runs. The wisp circles the spot where it was cast, spiralling outward: WISP_TURNS turns of
//     WISP_TURN ticks each, from WISP_R0 out to WISP_R1 px (about half the screen across), then it fades. It passes
//     through foes: each foe it touches loses 5 Hit Points / Wisps level straight off (no armor), flashes with a yellow
//     aura and gives Gandalf 1 Shield / level; the same wisp can touch the same foe again after WISP_REHIT ticks.
// Works in 1-player, P2 (one or two games: every write goes into every running game) and online (each page runs only
// its own player; the engine sends page writes with the buttons, so both pages see the same shield).
(() => {
  const FAKE = 0x0203FC50, TAB_A = 0x0806EE38, TAB_B = 0x09600000, TAB_C = 0x09600800, TAB_D = 0x09600900;   // copies, set by buildGame
  // index = Lightning Blade cooling | Dash cooling << 1 | Blinding Aura cooling << 2 (E-H: v214)
  const TABS = [TAB_A, TAB_B, TAB_C, TAB_D, 0x09600A00, 0x09600B00, 0x09600C00, 0x09600D00];
  // v222: + Wisps cooling << 3 (I-P at 0x09601000 + 0x100 * i)
  for (let i = 0; i < 8; i++) TABS.push(0x09601000 + 0x100 * i);
  const CD_TICKS = 600, BASE_DRAIN = 4, STUN_R = 80, STUN_T = 120;
  const WISP_COST = 10, WISP_NO_STATE = [6, 0x0A, 0x22, 0x23, 0x30, 0x31, 0x32, 0x60];   // hero states the game won't cast from (0x08043484)
  const WISP_GAP = 15, WISP_TURNS = 7, WISP_TURN = 20, WISP_R0 = 6, WISP_R1 = 84, WISP_SQ = 0.62, WISP_HIT = 15, WISP_REHIT = 15;
  const BA_CD = 450, DASH_CD = 120, DASH_T = 8, DASH_V = 9, DASH_F = 3, BA_R0 = 60, BA_R1 = 120, BA_UPD = 0x08020C05;
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
  const wantTab = (s, now) => {
    const cool = s.cdEnd !== undefined && ((s.cdEnd - now) | 0) > 0;
    const dcool = s.dashCd !== undefined && ((s.dashCd - now) | 0) > 0;
    const bcool = s.baCd !== undefined && ((s.baCd - now) | 0) > 0;
    const wcool = s.wispCd !== undefined && ((s.wispCd - now) | 0) > 0;
    if (!window.__gsDash) return cool ? TAB_B : TAB_A;
    return TABS[(cool ? 1 : 0) | (dcool ? 2 : 0) | (bcool && window.__gsBaCd ? 4 : 0) | (wcool && window.__gsWisp ? 8 : 0)];
  };
  // a foe a wisp can touch: alive and on the field (the first half of tools/turn16/turn16.c stunnable(), any state)
  const foe = (c, t) => { const e8 = c.r32(t + 0xE8); return (e8 & 0x801040) === 0x1000 && (e8 & 0x10040400) !== 0 && c.s16(t + 0x5A) > 0; };
  // where a wisp is, age u game ticks after its cast (world px, ground level)
  const wispAt = (w, u) => {
    const f = Math.max(0, Math.min(1, u / (WISP_TURNS * WISP_TURN))), r = WISP_R0 + (WISP_R1 - WISP_R0) * f;
    const a = w.a0 + w.dir * 2 * Math.PI * u / WISP_TURN;
    return [w.x + Math.cos(a) * r, w.y + Math.sin(a) * r * WISP_SQ];
  };
  const segD2 = (ax, ay, bx, by, px, py) => {   // squared distance from p to the segment a-b
    const dx = bx - ax, dy = by - ay, l = dx * dx + dy * dy, t = l ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / l)) : 0;
    const qx = ax + dx * t - px, qy = ay + dy * t - py; return qx * qx + qy * qy;
  };
  const wispFx = [[], []], wispHits = [];
  let tickSeen = -1, tickPn = 0;
  const tick = () => {
    const c = ctx(); if (!c) return;
    if (c.online && !window.__mp.sync) return;   // an online engine that can't send page writes: leave the game alone
    if (c.r8(0x030041B0) !== 1) {   // not in a level: the real table back (the Skills page shows its costs)
      for (const p of [0, 1]) { const P = 0x03003C00 + 0x1AC * p; if (TABS.includes(c.r32(P + 0x1C)) && c.r32(P + 0x1C) !== TAB_A) c.wN(P + 0x1C, TAB_A, 4); }
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
      const dcool = s.dashCd !== undefined && ((s.dashCd - now) | 0) > 0;
      const bcool = s.baCd !== undefined && ((s.baCd - now) | 0) > 0;
      const want = wantTab(s, now);
      if (TABS.includes(tab) && tab !== want && window.__gsTabB) c.wN(P + 0x1C, want, 4);
      s.cdLeft = cool ? ((s.cdEnd - now) | 0) / 30 : 0;
      s.dashLeft = dcool ? ((s.dashCd - now) | 0) / 30 : 0;
      s.baLeft = bcool && window.__gsBaCd ? ((s.baCd - now) | 0) / 30 : 0;
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
      if (s.fill) { S = max; s.fill = false; }   // Blinding Aura
      if (s.addS) { S = Math.min(max, S + s.addS); s.addS = 0; }   // Dash through foes with Lightning Blade up
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
  // ---- every animation frame: Dash and Blinding Aura (the cast windows are a few game ticks long) ----
  const fast = () => {
    const c = ctx(); if (!c || (c.online && !window.__mp.sync) || c.r8(0x030041B0) !== 1) { window.__auraS = 1; window.__auraX = 0; wispFx[0] = wispFx[1] = []; return; }
    const now = c.r32(0x030041A4), count = Math.min(2, c.r8(0x03003F58) || 1);
    if (now !== tickSeen) { tickSeen = now; tickPn = performance.now(); }
    const players = c.online ? [c.me] : [0, 1].filter((p) => p < Math.max(count, 1) || ewPtr(c.r32(0x03003C00 + 0x1AC * p)));
    for (const p of [0, 1]) if (!players.includes(p)) wispFx[p] = [];
    for (const p of players) {
      const P = 0x03003C00 + 0x1AC * p, hero = c.r32(P), s = st[p];
      if (!ewPtr(hero) || c.r8(P + 0x19F) !== 3) { s.wisps = null; wispFx[p] = []; continue; }
      const hx = c.s16(hero + 0xAE), hy = c.s16(hero + 0xB2), mine = p === (c.online ? c.me : 0);
      // Dash: take over the cast before its handler (Gwaihir) runs
      if (window.__gsDash && !s.dash && c.r8(P + 0x1A3) === 4 && (c.r8(P + 0x1A5) & 1) && c.r8(hero + 0x62) !== 6) {
        c.wN(P + 0x1A5, c.r8(P + 0x1A5) & ~1, 1);
        let ang;
        const fa = 0x0203FFC0 + 4 * p;
        if (c.r8(fa) & 2) ang = c.r8(fa + 1) / 256 * Math.PI * 2;
        else ang = (c.r8(hero + 0xF8) & 7) / 8 * Math.PI * 2;    // 8-way facing: 0 up, 2 right, 4 down, 6 left
        s.dash = { end: (now + DASH_T) | 0, vx: Math.round(Math.sin(ang) * DASH_V * 65536), vy: Math.round(-Math.cos(ang) * DASH_V * 65536), hit: new Set(), soft: new Set(), lb: (c.r8(hero + 0x99) & 1) !== 0 };
        s.dashCd = (now + DASH_CD) | 0;
        s.dash.anim = c.r8(hero + 0x95);   // the cast animation the game started; its staff-raised frame is held
        if (mine) window.__dashFx = { t: performance.now(), x: hx, y: hy, a: ang, on: true, end: 0 };
      }
      if (s.dash) {
        const d = s.dash;
        if (((d.end - now) | 0) <= 0 || c.s16(P + 0x17C) <= 0) {
          // let the game end the hit itself next tick (state 1, stand anim): hit ticks 0, the "already hit" bit kept 2 ticks
          c.wN(hero + 0xB4, 0, 4); c.wN(hero + 0xB8, 0, 4); c.wN(hero + 0x54, 0, 2); c.wN(hero + 0x56, 2, 2); c.wN(hero + 0x20, 1, 1);
          for (const o of d.soft) if (ewPtr(o)) c.wN(o + 0xE8, c.r32(o + 0xE8) | 4, 4);   // foes solid again
          s.dash = null;
          if (mine && window.__dashFx) { window.__dashFx.on = false; window.__dashFx.end = performance.now(); window.__dashFx.ex = hx; window.__dashFx.ey = hy; }
        } else {
          // a hit already under way (no hurt pose, no hurt sound), DASH_T + 2 ticks long
          c.wN(hero + 0xE8, c.r32(hero + 0xE8) | 0x20, 4); c.wN(hero + 0x56, 8, 2); c.wN(hero + 0x76, 0, 2);
          c.wN(hero + 0x54, Math.max(2, ((d.end - now) | 0) + 2), 2);
          if (c.r8(hero + 0x95) === d.anim && d.anim !== 3) { c.wN(hero + 0x23, DASH_F, 1); c.wN(hero + 0x20, 20, 1); }
          if (c.r8(hero + 0x62) !== 6) c.wN(hero + 0x62, 6, 1);
          c.wN(hero + 0xB4, d.vx, 4); c.wN(hero + 0xB8, d.vy, 4);
          for (const o of objs(c, hero)) {
            if (o === hero || d.hit.has(o) || !stunnable(c, o)) continue;
            const dx = c.s16(o + 0xAE) - hx, dy = c.s16(o + 0xB2) - hy, r2 = dx * dx + dy * dy;
            // foes near the path stop blocking (+0xE8 bit 2: the solid body the hero bumps into) until the dash ends
            if (r2 < 48 * 48 && (c.r32(o + 0xE8) & 4)) { c.wN(o + 0xE8, c.r32(o + 0xE8) & ~4, 4); d.soft.add(o); }
            if (r2 > 18 * 18) continue;
            d.hit.add(o);
            if (d.lb || (c.r8(hero + 0x99) & 1)) s.addS = (s.addS || 0) + 10;
          }
          if (mine) window.__dashTrail = { t: performance.now(), x: hx, y: hy };
        }
      }
      // Wisps (v222): take over the cast before its handler (Gwaihir's) runs, and let a wisp loose
      const spawnWisp = () => {
        const fa = 0x0203FFC0 + 4 * p;
        const ang = (c.r8(fa) & 2) ? c.r8(fa + 1) / 256 * Math.PI * 2 : (c.r8(hero + 0xF8) & 7) / 8 * Math.PI * 2;   // 0 up, clockwise
        const L = Math.max(1, c.r8(P + 0x171) << 24 >> 24);
        (s.wisps || (s.wisps = [])).push({ x: hx, y: hy, t0: now, a0: ang - Math.PI / 2, dir: (s.wispN = (s.wispN || 0) + 1) & 1 ? 1 : -1, L, last: now, hit: new Map() });
        s.wispCd = (now + WISP_GAP) | 0;
        const want = wantTab(s, now); if (TABS.includes(c.r32(P + 0x1C)) && window.__gsTabB) c.wN(P + 0x1C, want, 4);
      };
      if (window.__gsWisp && c.r8(P + 0x1A3) === 1 && (c.r8(P + 0x1A5) & 1)) {   // the game took it (a staff in his off hand)
        c.wN(P + 0x1A5, c.r8(P + 0x1A5) & ~1, 1);
        spawnWisp();
      }
      // v226 (Jordan: "Gandalf shouldn't summon an eagle anymore"): the game never casts this slot now (Wisps costs 0xFFFF
      // in every table; with a staff it used to, and Gwaihir's handler sometimes ran before the page saw the cast), so
      // the page reads the Quick Skill press itself as 0x08043350 does: L held (0x0300407C + 2 * player, bit 0x200) and A / B / R
      // newly down picks slot 0 / 1 / 2 (player + 0x191). It makes the game's own checks and takes the Spirit.
      const held = c.r16(0x0300407C + 2 * p), fresh = held & ~(s.held | 0); s.held = held;
      // v227 (Jordan: "Holding down the whisp button should keep casting wisps given the delay"): any held A / B / R whose
      // slot holds Wisps casts again each time the half-second gate opens, as long as L stays down and Spirit lasts.
      const wSlot = (held & 1) && c.r8(P + 0x191) === 1 ? 0 : (held & 2) && c.r8(P + 0x192) === 1 ? 1 : (held & 0x100) && c.r8(P + 0x193) === 1 ? 2 : -1;
      if (window.__gsWisp && (held & 0x200) && wSlot >= 0 && !(c.r8(P + 0x1A5) & 1)) {
        const st62 = c.r8(hero + 0x62), sp = c.s16(P + 0x17E);
        if ((c.r8(P + 0x171) << 24 >> 24) > 0 && !(((s.wispCd || 0) - now | 0) > 0) && sp >= WISP_COST &&
            c.s16(P + 0x17C) > 0 && !WISP_NO_STATE.includes(st62) && !(s.dash)) {
          c.wN(P + 0x17E, (sp - WISP_COST) & 0xffff, 2);
          spawnWisp();
        }
      }
      if (s.wisps && s.wisps.length) {
        const life = WISP_TURNS * WISP_TURN, hpm = s.hp || (s.hp = new Map());
        let list = null;
        for (let i = s.wisps.length - 1; i >= 0; i--) {
          const w = s.wisps[i], u1 = (now - w.t0) | 0;
          if (u1 < 0 || u1 > life + 12) { s.wisps.splice(i, 1); continue; }
          if (u1 > w.last - w.t0 && u1 <= life) {
            // every game tick since the last look: the path piece it flew, and any foe on it
            for (let u = Math.max(1, (w.last - w.t0) + 1); u <= u1; u++) {
              const [ax, ay] = wispAt(w, u - 1), [bx, by] = wispAt(w, u);
              list = list || objs(c, hero).filter((o) => o !== hero && o !== c.r32(0x03003C00) && o !== c.r32(0x03003DAC) && foe(c, o));
              for (const o of list) {
                const ox = c.s16(o + 0xAE), oy = c.s16(o + 0xB2);
                if (segD2(ax, ay, bx, by, ox, oy) > WISP_HIT * WISP_HIT) continue;
                const lastHit = w.hit.get(o);
                if (lastHit !== undefined && ((w.t0 + u - lastHit) | 0) < WISP_REHIT) continue;
                const hp0 = c.s16(o + 0x5A); if (hp0 <= 0) continue;
                w.hit.set(o, (w.t0 + u) | 0);
                const hp1 = hp0 - 5 * w.L;
                c.wN(o + 0x5A, (hp1 <= 0 ? 0 : hp1) & 0xffff, 2);
                if (hpm.has(o)) hpm.set(o, hp1 <= 0 ? 0 : hp1);   // not a sword strike (the Shield refill below)
                s.addS = (s.addS || 0) + w.L;
                wispHits.push({ o, x: ox, y: oy, t: performance.now() });
              }
            }
          }
          w.last = (w.t0 + Math.min(u1, life)) | 0;
          w.now = now;
        }
      }
      wispFx[p] = s.wisps ? s.wisps : [];
      // Blinding Aura: seen from the cast flags (skill 3 going off); the hero's + 0x99 bit 3 stays set ~9 s after it
      const ba = (c.r8(hero + 0x99) & 8) !== 0;
      const baCast = c.r8(P + 0x1A3) === 3 && (c.r8(P + 0x1A5) & 1) !== 0;
      if ((baCast && !s.baCast) || (ba && !s.ba && !s.baCast)) {
        s.fill = true;
        s.baCd = (now + BA_CD) | 0;
        if (mine) window.__baCast = { x: hx, y: hy, t: performance.now(), L: Math.max(1, c.r8(P + 0x173) << 24 >> 24) };
        const L = Math.max(1, c.r8(P + 0x173) << 24 >> 24), dmg = 10 + 2 * L;
        for (const o of objs(c, hero)) {
          if (o === hero) continue;
          if (c.r32(o + 0x14) === BA_UPD) { c.wN(o + 0xB2, (c.s16(o + 0xB2) + 4000) & 0xffff, 2); c.wN(o + 0xD2, (c.s16(o + 0xD2) + 4000) & 0xffff, 2); continue; }
          if (!stunnable(c, o)) continue;
          const dx = c.s16(o + 0xAE) - hx, dy = c.s16(o + 0xB2) - hy, r2 = dx * dx + dy * dy;
          if (r2 <= BA_R0 * BA_R0 || r2 > BA_R1 * BA_R1) continue;
          c.wN(o + 0x5A, (c.s16(o + 0x5A) - dmg) & 0xffff, 2);
          if (c.s16(o + 0x5A) > 0) { (s.stun || (s.stun = new Map())).set(o, (now + 90) | 0); stunHold(c, o, 90); }   // "blinded" 3 s
        }
        if (mine) window.__baT = performance.now();
      }
      if (ba) for (const o of objs(c, hero)) if (o !== hero && c.r32(o + 0x14) === BA_UPD && Math.abs(c.s16(o + 0xB2) - hy) < 1000) { c.wN(o + 0xB2, (c.s16(o + 0xB2) + 4000) & 0xffff, 2); c.wN(o + 0xD2, (c.s16(o + 0xD2) + 4000) & 0xffff, 2); }
      s.ba = ba; s.baCast = baCast;
    }
    // the aura swells to twice its size for a moment after Blinding Aura
    const bt = window.__baT ? (performance.now() - window.__baT) / 1000 : 9;
    const env = bt < 0.15 ? bt / 0.15 : bt < 0.9 ? 1 : bt < 1.6 ? 1 - (bt - 0.9) / 0.7 : 0;
    // and grows and brightens while the light pulls him (Dash, v218)
    const df = window.__dashFx, dt = df ? (performance.now() - df.t) / 1000 : 9;
    const denv = df && df.on && dt < 1 ? Math.min(1, dt / 0.08) : df ? Math.max(0, 1 - (performance.now() - df.end) / 350) : 0;
    window.__auraS = 1 + Math.max(env, 0.6 * denv); window.__auraX = Math.max(2.0 * env, 1.2 * denv);
  };
  const fastLoop = () => { requestAnimationFrame(fastLoop); try { fast(); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("gs fast: " + (e && e.message || e)); } };
  requestAnimationFrame(fastLoop);
  window.__baLeft = () => { const c = ctx(); const p = c && c.online ? c.me : 0; return (st[p] && st[p].baLeft) || 0; };
  window.__dashLeft = () => { const c = ctx(); const p = c && c.online ? c.me : 0; return (st[p] && st[p].dashLeft) || 0; };
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
  let glowT = 0, dashMoteT = 0;
  const dashMotes = [];
  const draw = (t) => {
    requestAnimationFrame(draw);
    const v = lastView, g = window.__gsShown;
    if (!v || !v.host) return;
    if (!ensure(v.host)) return;
    if (cv.width !== v.CW || cv.height !== v.CH) { cv.width = v.CW; cv.height = v.CH; }
    cx.setTransform(1, 0, 0, 1, 0, 0); cx.clearRect(0, 0, cv.width, cv.height);
    if (window.__fxOff) return;   // v218: casts are drawn even before Gandalf has a Shield level
    const VI = window.__gsVial || VIAL;
    const gx = (v.w - 240) / 2 + VI.x, gy = v.h - 160 + VI.y;
    const X = (x) => v.ox + (x - v.sx) * v.k, Y = (y) => v.oy + (y - v.sy) * v.ky;
    const x0 = X(gx), x1 = X(gx + VI.w), yb = Y(gy + VI.h), yt = Y(gy);
    if (g && g.frac > 0.001) {
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
    if (cam && g && g.lb) {
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
    // Blinding Aura (v214): a white-gold flash on Gandalf, a ring of light out to the full reach (BA_R1) and turning rays
    const bc = window.__baCast;
    if (cam && bc && performance.now() - bc.t < 1100) {
      const e = (performance.now() - bc.t) / 1100, k = v.k, ex = X(bc.x - cam[0]), ey = Y(bc.y - cam[1] - 10);
      const grow = Math.min(1, e / 0.45), ease = 1 - (1 - grow) * (1 - grow), fade = e < 0.45 ? 1 : 1 - (e - 0.45) / 0.55;
      cx.globalCompositeOperation = "lighter";
      // core flash
      const fr = (26 + 30 * ease) * k, fa = e < 0.12 ? e / 0.12 : Math.max(0, 1 - (e - 0.12) / 0.6);
      const rg = cx.createRadialGradient(ex, ey, 0, ex, ey, fr);
      rg.addColorStop(0, `rgba(255,255,245,${0.95 * fa})`); rg.addColorStop(0.35, `rgba(255,236,170,${0.55 * fa})`); rg.addColorStop(1, "rgba(255,220,140,0)");
      cx.fillStyle = rg; cx.fillRect(ex - fr, ey - fr, fr * 2, fr * 2);
      // rays
      const n = 14, rot = e * 0.9, rl = BA_R1 * ease * k;
      for (let i = 0; i < n; i++) {
        const a = rot + i * Math.PI * 2 / n, w = (i & 1 ? 0.05 : 0.09);
        const lg = cx.createLinearGradient(ex, ey, ex + Math.cos(a) * rl, ey + Math.sin(a) * rl * 0.6);
        lg.addColorStop(0, `rgba(255,248,220,${0.5 * fade})`); lg.addColorStop(1, "rgba(255,230,160,0)");
        cx.fillStyle = lg; cx.beginPath(); cx.moveTo(ex, ey);
        cx.lineTo(ex + Math.cos(a - w) * rl, ey + Math.sin(a - w) * rl * 0.6); cx.lineTo(ex + Math.cos(a + w) * rl, ey + Math.sin(a + w) * rl * 0.6);
        cx.closePath(); cx.fill();
      }
      // ring at the reach, plus a faint inner ring at the game's own range
      for (const [R, al, lw] of [[BA_R1, 0.85, 3], [BA_R0, 0.4, 1.5]]) {
        const r = R * ease * k;
        cx.strokeStyle = `rgba(255,244,205,${al * fade})`; cx.lineWidth = Math.max(1.5, lw * k * (0.4 + 0.6 * fade));
        cx.beginPath(); cx.ellipse(ex, ey, r, r * 0.6, 0, 0, Math.PI * 2); cx.stroke();
      }
      cx.globalCompositeOperation = "source-over";
    }
    // Dash (v218): Gandalf is pulled by light. A light shines ahead of him, a beam runs from his staff into it and motes
    // of light stream past him into it; his aura glows; at the end he takes the light in (a soft flash and ring).
    const df = window.__dashFx, dtr = window.__dashTrail, pn = performance.now();
    if (cam && df && pn - df.t < 1400) {
      const k = v.k, ux = Math.sin(df.a), uy = -Math.cos(df.a), on = df.on && pn - df.t < 1000;
      const hp = on && dtr ? [dtr.x, dtr.y] : [df.ex === undefined ? df.x : df.ex, df.ey === undefined ? df.y : df.ey];
      const prog = Math.min(1, (pn - df.t) / (DASH_T / 30 * 1000));
      const ab = on ? 0 : df.end ? Math.min(1, (pn - df.end) / 130) : 1;         // 0..1: the light flying into him
      const lead = (24 + 34 * (1 - prog)) * (1 - ab);
      const lx = hp[0] + ux * lead, ly = hp[1] + uy * lead - 16;               // the light, at staff height
      const sx = hp[0] + ux * 5, sy = hp[1] + uy * 5 - 18;                     // the staff
      const dtm = dashMoteT ? Math.min(50, pn - dashMoteT) : 16; dashMoteT = pn;
      cx.globalCompositeOperation = "lighter";
      // the path behind him: a soft warm glow from where he started, and his aura as a pale gold-white halo
      const fade = on ? 1 : Math.max(0, 1 - (pn - df.end) / 380);
      if (fade > 0) {
        const x0 = X(df.x - cam[0]), y0 = Y(df.y - cam[1] - 12), x1 = X(hp[0] - cam[0]), y1 = Y(hp[1] - cam[1] - 12);
        const lg = cx.createLinearGradient(x0, y0, x1, y1);
        lg.addColorStop(0, "rgba(255,236,190,0)"); lg.addColorStop(1, `rgba(255,244,220,${0.32 * fade})`);
        cx.strokeStyle = lg; cx.lineCap = "round"; cx.lineWidth = 13 * k;
        cx.beginPath(); cx.moveTo(x0, y0); cx.lineTo(x1, y1); cx.stroke();
        const hx = X(hp[0] - cam[0]), hy = Y(hp[1] - cam[1] - 14), hr = 22 * k * (0.95 + 0.08 * Math.sin(pn / 45));
        const hg = cx.createRadialGradient(hx, hy, 0, hx, hy, hr);
        hg.addColorStop(0, `rgba(255,250,235,${0.42 * fade})`); hg.addColorStop(0.5, `rgba(255,232,170,${0.2 * fade})`); hg.addColorStop(1, "rgba(150,200,255,0)");
        cx.fillStyle = hg; cx.fillRect(hx - hr, hy - hr, hr * 2, hr * 2);
      }
      if (ab < 1) {
        const LX = X(lx - cam[0]), LY = Y(ly - cam[1]), SX = X(sx - cam[0]), SY = Y(sy - cam[1]);
        const grow = Math.min(1, (pn - df.t) / 70), a = grow * (1 - ab);
        // the beam from his staff into the light, bending a little as it pulls
        const px = -uy, py = ux, wob = Math.sin(pn / 38) * 2.5 * k, mx = (SX + LX) / 2 + px * wob, my = (SY + LY) / 2 + py * wob;
        for (const [w, col] of [[8 * k, `rgba(255,214,140,${0.28 * a})`], [3.5 * k, `rgba(255,240,200,${0.55 * a})`], [1.4 * k, `rgba(255,255,255,${0.95 * a})`]]) {
          cx.strokeStyle = col; cx.lineWidth = Math.max(1, w); cx.lineCap = "round";
          cx.beginPath(); cx.moveTo(SX, SY); cx.quadraticCurveTo(mx, my, LX, LY); cx.stroke();
        }
        // the light itself, with four turning rays
        const r = (11 + 3 * Math.sin(pn / 60)) * k * (0.5 + 0.5 * grow) * (1 - 0.5 * ab);
        const rg = cx.createRadialGradient(LX, LY, 0, LX, LY, r * 2.2);
        rg.addColorStop(0, `rgba(255,255,255,${a})`); rg.addColorStop(0.22, `rgba(255,248,215,${0.85 * a})`);
        rg.addColorStop(0.5, `rgba(255,214,130,${0.35 * a})`); rg.addColorStop(1, "rgba(160,205,255,0)");
        cx.fillStyle = rg; cx.fillRect(LX - r * 2.2, LY - r * 2.2, r * 4.4, r * 4.4);
        const rot = pn / 260;
        cx.strokeStyle = `rgba(255,250,230,${0.7 * a})`; cx.lineWidth = Math.max(1, 1.1 * k);
        cx.beginPath();
        for (let q = 0; q < 4; q++) {
          const an = rot + q * Math.PI / 2, rl = r * (q & 1 ? 1.6 : 2.4);
          cx.moveTo(LX + Math.cos(an) * r * 0.3, LY + Math.sin(an) * r * 0.3); cx.lineTo(LX + Math.cos(an) * rl, LY + Math.sin(an) * rl);
        }
        cx.stroke();
      }
      // motes: born around and behind him, drawn into the light
      if (on) for (let q = 0; q < Math.max(1, Math.round(dtm / 6)); q++) {
        const side = (Math.random() - 0.5) * 26, back = 4 + Math.random() * 18;
        dashMotes.push({ x: hp[0] - ux * back - uy * side, y: hp[1] - uy * back + ux * side - 4 - Math.random() * 22, t: pn, life: 220 + Math.random() * 140 });
      }
      if (dashMotes.length > 90) dashMotes.splice(0, dashMotes.length - 90);
      cx.lineCap = "round";
      for (let q = dashMotes.length - 1; q >= 0; q--) {
        const m = dashMotes[q], age = (pn - m.t) / m.life;
        if (age >= 1) { dashMotes.splice(q, 1); continue; }
        const tx = lx - m.x, ty = ly - m.y, dd = Math.hypot(tx, ty) || 1, sp = Math.min(dd, (0.12 + 0.5 * age) * dtm);
        m.x += tx / dd * sp; m.y += ty / dd * sp;
        const al = Math.sin(age * Math.PI) * (dd < 6 ? 0.3 : 1);
        cx.strokeStyle = `rgba(255,${238 + (q & 1) * 17},${190 + (q & 3) * 20},${0.7 * al})`; cx.lineWidth = Math.max(1, (q & 1 ? 1.2 : 1.8) * k);
        cx.beginPath(); cx.moveTo(X(m.x - tx / dd * 5 - cam[0]), Y(m.y - ty / dd * 5 - cam[1])); cx.lineTo(X(m.x - cam[0]), Y(m.y - cam[1])); cx.stroke();
      }
      // taken in: a soft flash on him and a thin ring at his feet
      if (!on && df.end) {
        const e = (pn - df.end - 90) / 300;
        if (e > 0 && e < 1) {
          const hx = X(hp[0] - cam[0]), hy = Y(hp[1] - cam[1] - 14), fr = (14 + 12 * e) * k;
          const fg = cx.createRadialGradient(hx, hy, 0, hx, hy, fr);
          fg.addColorStop(0, `rgba(255,255,245,${0.75 * (1 - e)})`); fg.addColorStop(1, "rgba(255,225,160,0)");
          cx.fillStyle = fg; cx.fillRect(hx - fr, hy - fr, fr * 2, fr * 2);
          cx.strokeStyle = `rgba(255,240,200,${0.6 * (1 - e)})`; cx.lineWidth = Math.max(1, 1.5 * k);
          cx.beginPath(); cx.ellipse(hx, hy + 10 * k, (8 + 22 * e) * k, (5 + 12 * e) * k, 0, 0, Math.PI * 2); cx.stroke();
        }
      }
      cx.globalCompositeOperation = "source-over";
    } else if (dashMotes.length) dashMotes.length = 0;
    // Wisps (v222): a pale gold light with a fading tail, circling out from where it was cast; a yellow aura on each
    // foe it touches. Drawn between game ticks too (the tick's share of 1/30 s since it came).
    if (cam && (wispFx[0].length || wispFx[1].length || wispHits.length)) {
      const k = v.k, pn = performance.now(), fr = Math.min(1, (pn - tickPn) / 33.3), life = WISP_TURNS * WISP_TURN;
      cx.globalCompositeOperation = "lighter"; cx.lineCap = "round";
      for (const list of wispFx) for (const w of list) {
        const u = ((w.now - w.t0) | 0) + fr;
        if (u > life + 12) continue;
        const fade = (u < 3 ? u / 3 : 1) * (u > life ? Math.max(0, 1 - (u - life) / 12) : 1);
        if (fade <= 0) continue;
        const uu = Math.min(u, life);
        // tail: the last stretch of its path, thinning out
        const TAIL = 7, N = 10;
        for (let q = N; q >= 1; q--) {
          const ua = Math.max(0, uu - TAIL * q / N), ub = Math.max(0, uu - TAIL * (q - 1) / N);
          if (ub <= 0) continue;
          const [ax, ay] = wispAt(w, ua), [bx, by] = wispAt(w, ub), al = fade * (1 - (q - 1) / N);
          cx.strokeStyle = `rgba(255,${226 + 20 * (1 - q / N) | 0},${140 + 90 * (1 - q / N) | 0},${0.55 * al})`;
          cx.lineWidth = Math.max(1, (1 + 4 * (1 - q / N)) * k);
          cx.beginPath(); cx.moveTo(X(ax - cam[0]), Y(ay - cam[1] - 14)); cx.lineTo(X(bx - cam[0]), Y(by - cam[1] - 14)); cx.stroke();
        }
        // the wisp: a bright core in a soft gold glow that flickers
        const [wx, wy] = wispAt(w, uu), ex = X(wx - cam[0]), ey = Y(wy - cam[1] - 14 + 1.5 * Math.sin(pn / 90 + w.t0));
        const r = (7 + 1.5 * Math.sin(pn / 55 + w.t0 * 3)) * k;
        const rg = cx.createRadialGradient(ex, ey, 0, ex, ey, r * 2.4);
        rg.addColorStop(0, `rgba(255,255,250,${fade})`); rg.addColorStop(0.18, `rgba(255,248,205,${0.9 * fade})`);
        rg.addColorStop(0.45, `rgba(255,214,110,${0.38 * fade})`); rg.addColorStop(1, "rgba(255,190,80,0)");
        cx.fillStyle = rg; cx.fillRect(ex - r * 2.4, ey - r * 2.4, r * 4.8, r * 4.8);
        // its light on the ground
        const sg = cx.createRadialGradient(ex, ey + 14 * k, 0, ex, ey + 14 * k, 10 * k);
        sg.addColorStop(0, `rgba(255,220,140,${0.22 * fade})`); sg.addColorStop(1, "rgba(255,220,140,0)");
        cx.fillStyle = sg; cx.beginPath(); cx.ellipse(ex, ey + 14 * k, 10 * k, 5 * k, 0, 0, Math.PI * 2); cx.fill();
      }
      for (let i = wispHits.length - 1; i >= 0; i--) {
        const h = wispHits[i], e = (pn - h.t) / 380;
        if (e >= 1 || e < 0) { wispHits.splice(i, 1); continue; }
        const ex = X(h.x - cam[0]), ey = Y(h.y - cam[1] - 14), a = e < 0.15 ? e / 0.15 : 1 - (e - 0.15) / 0.85;
        const r = (14 + 8 * e) * k;
        const rg = cx.createRadialGradient(ex, ey, 0, ex, ey, r);
        rg.addColorStop(0, `rgba(255,250,170,${0.55 * a})`); rg.addColorStop(0.5, `rgba(255,220,60,${0.4 * a})`); rg.addColorStop(1, "rgba(255,200,40,0)");
        cx.fillStyle = rg; cx.beginPath(); cx.ellipse(ex, ey, r * 0.8, r * 1.15, 0, 0, Math.PI * 2); cx.fill();
        cx.strokeStyle = `rgba(255,232,90,${0.75 * a})`; cx.lineWidth = Math.max(1, 1.6 * k * (1 - e));
        cx.beginPath(); cx.ellipse(ex, ey + 12 * k, (7 + 12 * e) * k, (4 + 6 * e) * k, 0, 0, Math.PI * 2); cx.stroke();
      }
      if (wispHits.length > 40) wispHits.splice(0, wispHits.length - 40);
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
