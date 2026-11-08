  // ---------------- P2 helper (Jordan, 2026-11-08) ----------------
  // A P2 button next to Auto. In the wide view it lists the saved heroes that aren't the one being played; picking one
  // restarts as a 2-player link game (the PC app's engine runs both games side by side): both games load their own
  // slot, and P2 is played by the page like Auto, but it stays on P1's screen: it fights enemies near P1, picks up herbs
  // and food near P1, and otherwise follows P1. Only P1's picture is shown. When P1 saves (pause, Save Game), P2 saves
  // its own slot too, and both slots go into the one saved-games file. Tap P2 again to stop it.
  // Loading screen over the game while P2 joins (Jordan, 2026-11-08: don't show the menus being driven).
  const p2Loading = (on, text) => {
    let el = document.getElementById("p2Load");
    if (!el) { if (!on) return; el = document.createElement("div"); el.id = "p2Load"; el.innerHTML = '<div class="spin"></div><div class="t"></div>'; ($("game") || document.body).appendChild(el); }
    if (on) el.querySelector(".t").textContent = text || "P2 is joining…";
    el.hidden = !on;
    // No sound while P2 joins (Jordan, 2026-11-08).
    try { const g = window.GbrHost && window.GbrHost.gain; if (g) g.gain.value = on ? 0 : 1.1; } catch (e) {}
  };
  const P2_HEROES = ["Frodo", "Legolas", "Aragorn", "Gandalf", "Eowyn", "Gimli", "Sam", "Smeagol"];
  // Saved-games file: slot k at 0x40 + 0x70 k, stored in 8-byte blocks with each block's bytes reversed.
  const p2SlotInfo = (b) => {
    const out = [];
    for (let k = 0; k < 4; k++) {
      const o = 0x40 + k * 0x70; let used = false;
      if (b && b.length >= 0x200) for (let j = 0; j < 0x60; j++) if (b[o + j]) { used = true; break; }
      out.push(used ? { slot: k, hero: b[o + 0x62] >> 4, level: b[o + 0x5B] + 1 } : null);
    }
    return out;
  };
  const p2Config = () => { try { const j = JSON.parse(sessionStorage.getItem("rotk-p2") || "null"); return j && j.p2 >= 0 && j.p2 < 4 && j.p1 >= 0 && j.p1 < 4 && j.p1 !== j.p2 ? j : null; } catch (e) { return null; } };
  function wideP2({ M, H, readSave, save, link, setBoot, keepSave, join, prefetch }) {
    // Each call (1 player, then again when P2 joins) gets its own timers; dispose() stops them.
    const timers = [], every = (fn, ms) => { const t = setInterval(fn, ms); timers.push(t); return t; };
    let disposed = false;
    const btn = $("p2Btn"), panel = $("p2Pick"), note = $("saveNote");
    const show = (msg, ms) => { note.textContent = msg; note.hidden = false; clearTimeout(show.t); show.t = setTimeout(() => { note.hidden = true; }, ms || 3000); };
    const slog = (m) => { try { window.__slog && window.__slog("p2: " + m); } catch (e) {} };
    const linkOn = !!(link && M._rotk_link_on && M._rotk_link_on());
    // Memory of game i (0 = P1, 1 = P2); solo: the one game.
    const mem = (i) => {
      const H8 = M.HEAPU8, iw = linkOn ? M._rotk_link_iwram(i) : M._rotk_iwram(), ew = linkOn ? M._rotk_link_ewram(i) : M._rotk_ewram();
      const at = (a) => ((a >>> 24) === 3 ? iw + (a & 0x7fff) : (a >>> 24) === 2 ? ew + (a & 0x3ffff) : -1);
      const r8 = (a) => { const o = at(a); return o >= 0 ? H8[o] : 0; };
      const r16 = (a) => { const o = at(a); return o >= 0 ? H8[o] | H8[o + 1] << 8 : 0; };
      const r32 = (a) => { const o = at(a); return o >= 0 ? (H8[o] | H8[o + 1] << 8 | H8[o + 2] << 16 | H8[o + 3] << 24) >>> 0 : 0; };
      return { ok: iw > 0 && ew > 0, r8, r16, r32 };
    };
    const close = () => { panel.hidden = true; panel.innerHTML = ""; };
    const ctl = { dispose: () => {
      disposed = true; timers.forEach(clearInterval); close();
      try { if (M._rotk_link_p2) M._rotk_link_p2(0); if (M._rotk_link_turbo) M._rotk_link_turbo(0); } catch (e) {}
      window.__mirrorIw = null; window.__p2Tick = null;
    } };
    // Joining without a reload (Jordan, 2026-11-08): tapping P2 pauses the game, picking a hero unpauses it
    // straight into the 2-player game (from the saved games), Cancel just unpauses.
    let held = false, playLvl = 0;   // playLvl: the level last seen in play
    const hold = (on) => { if (held === on) return; held = on; try { M._rotk_pause(on ? 1 : 0); } catch (e) {} };
    const doJoin = async (cfg) => {
      if (disposed) return;
      if (cfg.p1 === cfg.p2 || cfg.p1 > 3) { hold(false); show("P2 can't join: load a different hero first.", 4000); return; }
      try { keepSave(); } catch (e) {}

      if (!(await join(cfg))) { hold(false); show("P2 couldn't join. Keep playing, or try again.", 5000); }
    };
    const restart = (cfg) => {
      try { keepSave(); } catch (e) {}
      try { if (cfg) sessionStorage.setItem("rotk-p2", JSON.stringify(cfg)); else sessionStorage.removeItem("rotk-p2"); } catch (e) {}
      // Give the account backup a moment to take the newest saved games, then start again.
      show(cfg ? "Starting the 2-player game…" : "Going back to 1 player…", 4000);
      setTimeout(() => location.reload(), 2500);
    };
    const open = () => {
      panel.innerHTML = ""; panel.hidden = false;
      const h = document.createElement("div"); h.className = "p2-title"; panel.appendChild(h);
      const add = (label, fn, cls) => { const b = document.createElement("button"); b.type = "button"; b.textContent = label; if (cls) b.className = cls; b.addEventListener("click", (e) => { e.preventDefault(); e.stopPropagation(); fn(); }); panel.appendChild(b); };
      if (linkOn) {
        const s = p2SlotInfo(save)[link.p2];
        h.textContent = "P2 is playing " + (s ? P2_HEROES[s.hero] || "a hero" : "a hero") + ".";
        const n = document.createElement("div"); n.className = "p2-note"; n.textContent = "Stopping goes back to 1 player from your saved games, so save first."; panel.appendChild(n);
        add("Stop P2", () => { close(); restart(null); }, "p2-main");
        add("Cancel", close);
        return;
      }
      const m = mem(0), cur = m.ok ? m.r8(0x03005834) : -1, lvl = playLvl || (m.ok ? m.r8(0x030041F8) : 0);
      const list = p2SlotInfo(readSave() || save).filter((s) => s && s.slot !== cur);
      if (list.length) { hold(true); try { prefetch && prefetch().catch(() => {}); } catch (e) {} }   // paused while picking; fetch the 2-player engine now
      h.textContent = list.length ? "Pick P2's hero" : "No other saved heroes";
      const n = document.createElement("div"); n.className = "p2-note";
      n.textContent = list.length ? "Game paused. Pick a hero to unpause with P2; the level starts again from your last save" + (lvl === 82 ? " (back in Moria)" : "") + "." : "Start another hero in a free slot first, then P2 can play it.";
      panel.appendChild(n);
      for (const s of list) add((P2_HEROES[s.hero] || "Hero") + " · level " + s.level, () => {
        close(); doJoin({ p1: cur, p2: s.slot, moria: lvl === 82, level: lvl });
      }, "p2-hero");
      add("Cancel", () => { close(); hold(false); });
    };
    btn.__open = open; btn.__unhold = () => hold(false);
    if (!btn.__bound) {
      btn.__bound = true;
      btn.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); if (!panel.hidden) { panel.hidden = true; panel.innerHTML = ""; btn.__unhold && btn.__unhold(); } else btn.__open(); });
      btn.addEventListener("click", (e) => e.preventDefault());
    }
    btn.classList.toggle("on", linkOn); btn.setAttribute("aria-pressed", linkOn ? "true" : "false");
    // Page changes to game memory (skill slots, options) are copied into P2's game so both stay identical.
    if (linkOn) window.__mirrorIw = (off) => { const H8 = M.HEAPU8; H8[M._rotk_link_iwram(1) + off] = H8[M._rotk_link_iwram(0) + off]; };
    // The button shows while a hero is loaded in a level (state 1) or the game is paused, and always in a P2 game.
    every(() => {
      // Only in the game's pause menu (Jordan, 2026-11-08), in 1 player and in a P2 game.
      let vis = false;
      try { const m = mem(0); const st = m.r32(0x030041B0) & 255; vis = m.ok && st === 16 && (linkOn || m.r8(0x03005834) < 4); if (m.ok && st === 1 && m.r8(0x030041F8)) playLvl = m.r8(0x030041F8); } catch (e) {}
      btn.hidden = !vis; if (!vis && !panel.hidden) { close(); hold(false); }
    }, 500);
    if (!link) return ctl;
    if (!linkOn) { try { sessionStorage.removeItem("rotk-p2"); } catch (e) {} show("P2 couldn't start, playing 1 player.", 5000); return ctl; }

    // ---- 2-player game ----
    const K = { A: 1, B: 2, SEL: 4, START: 8, RT: 16, LT: 32, U: 64, D: 128, R: 256, L: 512 };
    const frames = () => M._rotk_link_frames() >>> 0;
    const state = (i) => mem(i).r32(0x030041B0) & 255, sub = (i) => mem(i).r8(0x030041C0), cursor = (i) => mem(i).r8(0x030041BC);
    let p2keys = 0; const p2 = (k) => { p2keys = k; try { M._rotk_link_p2(k); } catch (e) {} };
    // Presses: [frame to start, p1 keys, p2 keys, frames held]. The boot runs from the title to the level start.
    let boot = { phase: "title", t: 0, presses: [], tries: 0 }, macro = null;
    const press = (p1k, p2k, hold, after) => { const f0 = boot.presses.length ? boot.presses[boot.presses.length - 1].end : frames(); boot.presses.push({ at: f0, p1: p1k, p2: p2k, until: f0 + hold, end: f0 + hold + after }); };
    // P2 joins in the level you paused in (Jordan, 2026-11-08): Moria, a hero's own campaign, any level.
    { const lv = link.level > 0 && link.level < 256 ? link.level : link.moria ? 82 : 0; if (lv) try { M._rotk_link_level(lv); } catch (e) {} }
    setBoot(0);
    const say = (t) => { $("mpBanner").textContent = t; $("mpBanner").hidden = !t; };
    // Gems P2 picks up go into your gem total too (Jordan, 2026-11-08): P2's own game is where its pickups count, so each
    // rise in P2's gems there is added to your gems in both games.
    let p2Gems = -1;
    every(() => {
      try {
        if (boot || state(0) !== 1) { p2Gems = -1; return; }
        const m0 = mem(0), m1 = mem(1); if (!m0.ok || !m1.ok) return;
        const i1 = m1.r8(0x03003F59) & 1, i0 = m0.r8(0x03003F59) & 1, Q = 0x03003C00 + 0x1AC * i1, O = 0x03003C00 + 0x1AC * i0;
        const g = m1.r16(Q + 0x184);
        if (p2Gems >= 0 && g > p2Gems) {
          const v = Math.min(65535, m0.r16(O + 0x184) + (g - p2Gems));
          w8both(O + 0x184, v & 255); w8both(O + 0x185, v >> 8); slog("P2 gems +" + (g - p2Gems) + " -> yours " + v);
        }
        p2Gems = g;
      } catch (e) {}
    }, 200);
    p2Loading(true);
    try { M._rotk_link_turbo && M._rotk_link_turbo(4); } catch (e) {}   // menus run at 5x while the page drives them
    const bootTick = () => {
      const f = frames();
      if (boot.presses.length) {
        const p = boot.presses[0];
        if (f < p.at) { setBoot(0); p2(0); return; }
        // Every press is held for at least one picture (the menus run several frames per picture while starting).
        if (f < p.until || !p.held) { p.held = true; setBoot(p.p1); p2(p.p2); return; }
        setBoot(0); p2(0);
        if (f < p.end) return;
        boot.presses.shift(); return;
      }
      const s0 = state(0), s1 = state(1);
      if (boot.phase === "title") {
        // Title menu (state 5, part 2): move both cursors down to Multiplayer (item 2), then A opens Load Game.
        if (s0 !== 5 || s1 !== 5 || sub(0) !== 2 || sub(1) !== 2) { if (f > 1800) fail("the title menu didn't show"); return; }
        if (!boot.tt) boot.tt = f;
        if (f - boot.tt < 60) return;
        const c = [mem(0).r8(0x030041B8), mem(1).r8(0x030041B8)];   // title menu cursor
        if (c[0] === 2 && c[1] === 2) { press(K.A, K.A, 6, 60); boot.phase = "slots"; boot.t = f; boot.tries = 0; return; }
        if (++boot.tries > 12) { fail("couldn't reach Multiplayer on the title menu"); return; }
        const mv = (i) => (c[i] < 2 ? K.D : c[i] > 2 ? K.U : 0);
        press(mv(0), mv(1), 4, 24); return;
      }
      if (boot.phase === "slots") {
        if (s0 !== 9 || s1 !== 9) { if (f - boot.t > 900) fail("the games didn't reach Load Game (" + s0 + "/" + s1 + ")"); return; }
        // The Load Game screen ignores buttons for a while after it opens.
        if (!boot.t9) boot.t9 = f;
        if (f - boot.t9 < 120) return;
        const want = [link.p1, link.p2], c = [cursor(0), cursor(1)];
        if (c[0] === want[0] && c[1] === want[1]) { press(K.A, K.A, 4, 60); boot.phase = "path"; boot.t = f; return; }
        if (++boot.tries > 12) { fail("couldn't pick the slots"); return; }
        const mv = (i) => ((c[i] & 1) !== (want[i] & 1) ? (want[i] & 1 ? K.RT : K.LT) : (c[i] >> 1) !== (want[i] >> 1) ? (want[i] >> 1 ? K.D : K.U) : 0);
        press(mv(0), mv(1), 4, 20); return;
      }
      if (boot.phase === "path") {
        // Choose Your Path: P1 presses A three times and the level starts.
        if (s0 === 1 && s1 === 1 && f - boot.t > 200) { done(); return; }
        // Still on Load Game: press A again (only while both cursors are on the right slots).
        if (s0 === 9 && s1 === 9 && sub(0) === 0 && sub(1) === 0 && f - boot.t > 120) { boot.t = f; if (cursor(0) === link.p1 && cursor(1) === link.p2) press(K.A, K.A, 6, 60); else { boot.phase = "slots"; boot.t9 = f - 120; } return; }
        if (s0 === 11) { if (!boot.pathT) boot.pathT = f; if (f - boot.pathT >= 150) press(K.A, 0, 4, 90); }
        if (f - boot.t > 3600) fail("the level didn't start (" + s0 + "/" + s1 + ")");
      }
    };
    const fail = (why) => { try { M._rotk_link_turbo && M._rotk_link_turbo(0); } catch (e) {} slog("boot failed: " + why); boot = null; setBoot(null); p2(0); say(""); p2Loading(false); show("P2 couldn't start the game: " + why + ". You can play on as P1.", 6000); };
    const done = () => { try { M._rotk_link_turbo && M._rotk_link_turbo(0); } catch (e) {} slog("boot done, P1 slot " + link.p1 + ", P2 slot " + link.p2 + ", level " + mem(0).r8(0x030041F8)); boot = null; setBoot(null); p2(0); say(""); p2Loading(false); show("P2 joined", 2500);
      // The level's first seconds stay quiet and the sound fades in (Jordan heard extra music for ~4 s as P2 joined).
      try { const g = window.GbrHost && window.GbrHost.gain, c = g && g.context; if (g && c) { g.gain.cancelScheduledValues(c.currentTime); g.gain.setValueAtTime(0, c.currentTime); g.gain.setValueAtTime(0, c.currentTime + 4); g.gain.linearRampToValueAtTime(1.1, c.currentTime + 5); } } catch (e) {} };

    // ---- Saves: both games keep their own copy; slot p2 comes from P2's game, the rest from P1's. ----
    const buf = M._malloc(512), copies = [save.slice(0, 512), save.slice(0, 512)], so = 0x40 + link.p2 * 0x70;
    let wrote = 0;
    every(() => {
      let dirty = false;
      for (let i = 0; i < 2; i++) { try { if (M._rotk_link_save(i, buf)) { copies[i] = M.HEAPU8.slice(buf, buf + 512); dirty = true; } } catch (e) {} }
      if (!dirty) return;
      const merged = copies[0].slice(); merged.set(copies[1].subarray(so, so + 0x70), so);
      try { M.FS.writeFile("/data/saves/rotk-modded.sav", merged); wrote++; } catch (e) {}
    }, 1000);

    // ---- P2 player ----
    const ENEMY_UPD = 0x0801b9d1, ITEM_UPD = 0x0802f131, DEAD = new Set([0x11, 0x15, 4, 0x1b, 0x13]);
    let p2Hp = 0, p2HurtAt = 0, dbg = null, grid = null, gridT = 0, hist = [], savedPause = false, lastSave = 0, waitB = 0, mirror = 0, blocked = new Map(), seqRun = null;
    const pkeys = () => 1023 & ~H.keys;  // P1's buttons held now
    const tick = () => {
      if (boot) { try { bootTick(); } catch (e) { fail(String(e)); } return; }
      const f = frames();
      if (macro) { runMacro(f); return; }
      const s0 = state(0), s1 = state(1);
      if (wearRun) { try { runWear(f, s1); } catch (e) { wearRun = null; } return; }
      if (s1 === 16) {
        // Paused: P1 went to Save Game, so P2 saves its own slot; P1 pressed B to go on, so P2 does too.
        if (s0 === 9 && !savedPause && sub(1) === 0) { savedPause = true; macro = { phase: "enter", t: f }; slog("saving P2's slot"); return; }
        if (s0 === 16 && sub(0) === 2 && sub(1) === 0) { if (!waitB) waitB = f; if (f - waitB > 10) { seq([[K.B, 20], [0, 30]], f); waitB = 0; } return; }
        p2(0); return;
      }
      if (s1 === 1) {
        savedPause = false;
        if (s0 !== 1) { p2(0); return; }   // P1 is in a menu (backpack, shop): P2 waits
        try { play(f); } catch (e) { p2(0); }
        return;
      }
      if ([10, 14, 15, 20, 6].includes(s1)) { seq([[K.B, 6], [0, 30]], f); return; }   // a menu of P2's own: back out
      if (s1 === 9 || s1 === 11) { p2(0); return; }
      // Other shared screens (level results and the like): copy P1's A presses.
      const a = pkeys() & K.A;
      if (a && !mirror) { mirror = 1; seq([[K.A, 6], [0, 10]], f); return; }
      if (!a) mirror = 0;
      p2(0);
    };
    const runMacro = (f) => {
      const m = macro, s1 = state(1), sb = sub(1);
      if (f < (m.next || 0)) { p2(f < (m.until || 0) ? m.k : 0); return; }
      const tap = (k, n, gap) => { m.k = k; m.until = f + n; m.next = f + n + gap; p2(k); };
      if (f - m.t > 1500) { slog("save gave up in " + s1 + "/" + sb); macro = null; p2(0); return; }
      if (m.phase === "enter") { if (s1 === 9) { m.phase = "wait"; m.t9 = f; p2(0); return; } if (s1 === 16 && sb === 0) tap(K.A, 20, 40); else p2(0); return; }
      if (m.phase === "wait") { p2(0); if (f - m.t9 >= 150) m.phase = "ovw"; return; }
      if (m.phase === "ovw") {
        if (s1 === 9 && sb === 1) { m.phase = "yes"; p2(0); return; }
        // Only ever saves over P2's own slot.
        if (s1 === 9 && sb === 0 && cursor(1) === link.p2) tap(K.A, 20, 40); else { slog("save: cursor on " + cursor(1) + ", not saving"); m.phase = "ack"; }
        return;
      }
      if (m.phase === "yes") { if (sb === 3) { m.phase = "ack"; p2(0); return; } if (sb === 1) { if (!m.lt) { m.lt = 1; tap(K.LT, 20, 20); } else { m.lt = 0; tap(K.A, 20, 60); } } else p2(0); return; }
      if (m.phase === "ack") {
        if (s1 === 16) { macro = null; p2(0); lastSave = f; slog("P2 saved"); return; }
        if (s1 === 9 && sb === 3) tap(K.A, 20, 40); else if (s1 === 9 && sb === 0) tap(K.B, 20, 40); else if (s1 === 9 && sb === 1) tap(K.B, 20, 40); else p2(0);
      }
    };
    // P2 like a live player (Jordan, 2026-11-08): it walks smoothly (holds a direction toward the furthest point
    // of its route it can see, and only re-plans about 7 times a second), reacts to a new enemy after a short
    // random delay, stands beside P1 and attacks from the side opposite P1, uses its learned skills on elites and
    // groups, backs off behind P1 when its health is low (with a note on screen), and picks up gear only when it is
    // an upgrade for P2, then wears it. P2 never discards, sells or uses the Forge.
    const seen = new Map(), skillCost2 = new Map(), noSkill2 = new Map(), noGear = new Set(), p2Tries = new Map();
    // P2 picks up gear only when it beats what P2 wears (and anything of that kind in its pack) and the pack has room; it
    // never wears or throws gear away itself (Jordan, 2026-11-08), so it stays in the pack for you.
    const P2_WEARS = false;
    let kiteT = 0, rangerShots = 0;
    let plan = null, lastNote = 0, retreatT = 0, retreatCool = 0, castT2 = 0, castPend = null, eqPend = null, side = 1, lastGoalKey = "";
    const p2casts = {}, p2eq = [];
    const w8both = (a, v) => { const o = a & 0x7fff, H8 = M.HEAPU8; H8[M._rotk_link_iwram(0) + o] = v; H8[M._rotk_link_iwram(1) + o] = v; };
    // Items: 32-bit words (category bits 0-3, index 8-15, prefix 16-23, suffix 24-31); category table 0x08068F50.
    const ROM = () => window.__romFull;
    const rr8 = (a) => ROM()[a - 0x08000000];
    const rr32 = (a) => { const R = ROM(), o = a - 0x08000000; return (R[o] | R[o + 1] << 8 | R[o + 2] << 16 | R[o + 3] << 24) >>> 0; };
    const catw = (c, k) => rr32(0x08068F50 + c * 0x28 + 4 * k);
    const iflags = (it) => rr32(catw(it & 15, 8) + 8 * ((it >>> 8) & 255));
    const ipairs = (it) => {
      const c = it & 15, i = (it >>> 8) & 255, pre = (it >>> 16) & 255, suf = it >>> 24, out = [];
      const ents = [catw(c, 0) + 12 * i];
      if (pre !== 255 && c !== 7) ents.push(catw(c, 2) + 12 * pre);
      if (suf !== 255) ents.push(catw(c, 5) + 12 * suf);
      for (const e of ents) for (let k = 3; k < 11; k += 2) { const s = rr8(e + k); if (s !== 0x5a) out.push([s, rr8(e + k + 1) << 24 >> 24]); }
      return out;
    };
    const wstat = (s) => s <= 6 ? 3 : s <= 12 ? 0.5 : s <= 15 ? 2 : s === 16 ? 1 : s <= 21 ? 1.5 : s === 22 ? 0.3 : s === 23 ? 0.2 : s === 46 ? 1 : 0.4;
    const score = (it) => ipairs(it).reduce((t, [s, v]) => t + wstat(s) * v, 0);
    const slotOf = (fl) => { for (let s = 0; s < 8; s++) if (fl & (1 << (18 + s))) return s; return -1; };
    const empty = (it) => (it & 15) === 15;
    const reqLevel = (it) => {
      const c = it & 15, i = (it >>> 8) & 255, pre = (it >>> 16) & 255, suf = it >>> 24, fl = iflags(it);
      let r = rr8(catw(c, 0) + 12 * i + 2);
      if (fl & 0x80) r += 5; if (fl & 0x100) r += 5;
      if (pre !== 255 && c !== 7) { r += rr8(catw(c, 2) + 12 * pre + 2) >> 1; const pf = rr32(catw(c, 3) + 4 * pre); r += 5 * !!(pf & 1) + 5 * !!(pf & 2); }
      if (suf !== 255) { r += rr8(catw(c, 5) + 12 * suf + 2); const sf = rr32(catw(c, 6) + 4 * suf); r += 5 * !!(sf & 1) + 5 * !!(sf & 2); }
      if (fl & 0x10000) r = 1;
      return r & 255;
    };
    // Slot P2 would wear this item in (its hero, its level, no two-hander + shield clash), or -1.
    const gearSlot = (m, P, it) => {
      if (empty(it) || (it & 15) === 7) return -1;
      const fl = iflags(it); if (fl & 0x10000) return -1;
      let hero = m.r8(P + 0x19F); if (hero === 6) hero = 0;
      if (hero >= 6 || !(fl & (0x04000000 << hero))) return -1;
      if (reqLevel(it) > m.r8(P + 0x19C) + 1) return -1;
      const s = slotOf(fl); if (s < 0) return -1;
      const wpn = m.r32(P + 0x40), sh = m.r32(P + 0x44);
      if (s === 2 && !empty(wpn) && (iflags(wpn) & 0x20000)) return -1;
      if (s === 1 && (fl & 0x20000) && !empty(sh)) return -1;
      return s;
    };
    const packFull = (m, P) => { for (let k = 0; k < 8; k++) if (empty(m.r32(P + 0x5c + 4 * k))) return false; return true; };
    // An upgrade: wearable now and better than what P2 wears in that slot and than anything of that slot in its pack.
    const upgrade = (m, P, it) => {
      if (noGear.has(it)) return false;
      const s = gearSlot(m, P, it); if (s < 0) return false;
      const cur = m.r32(P + 0x3c + 4 * s); let best = empty(cur) ? -1e9 : score(cur);
      for (let k = 0; k < 8; k++) { const b = m.r32(P + 0x5c + 4 * k); if (!empty(b) && slotOf(iflags(b)) === s) best = Math.max(best, score(b)); }
      return score(it) > best + 0.01;
    };
    // Backpack item to wear now (picked up as an upgrade), or -1.
    const toWear = (m, P) => {
      for (let k = 0; k < 8; k++) {
        const it = m.r32(P + 0x5c + 4 * k); if (empty(it) || noGear.has(it)) continue;
        const s = gearSlot(m, P, it); if (s < 0) continue;
        const cur = m.r32(P + 0x3c + 4 * s);
        if (empty(cur) || score(it) > score(cur) + 0.01) return k;
      }
      return -1;
    };
    const pickSkill2 = (m, P, now) => {
      const hero = m.r8(P + 0x19F), sp = m.r16(P + 0x17E), msp = m.r16(P + 0xD2) || 1;
      let best = -1, bc = -1;
      for (let s = 0; s < 6; s++) {
        if ((m.r8(P + 0x16A + s) << 24 >> 24) <= 0) continue;
        const key = hero * 8 + s; if ((noSkill2.get(key) || 0) > now) continue;
        const t = m.r32(P + 0x1C), real = t >>> 24 === 8 && rr32(t + 40 * s) ? rr8(t + 40 * s + 4) | rr8(t + 40 * s + 5) << 8 : -1;
        const cost = real > 0 ? real : skillCost2.has(key) ? skillCost2.get(key) : Math.round(msp * 0.3);
        if (sp < cost) continue;
        if (cost > bc) { bc = cost; best = s; }
      }
      return best;
    };
    // Grid line of sight (8 px cells): every 4 px along the line is walkable.
    const clear = (x0, y0, x1, y1) => {
      const { W, free } = grid, n = Math.ceil(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) / 4);
      for (let i = 1; i <= n; i++) { const xx = x0 + (x1 - x0) * i / n, yy = y0 + (y1 - y0) * i / n; if (!free[(xx >> 3) + (yy >> 3) * W]) return false; }
      return true;
    };
    const freeAt = (tx, ty) => { if (!grid || tx < 8 || ty < 8) return false; const c = (tx >> 3) + (ty >> 3) * grid.W; return c < grid.free.length && !!grid.free[c]; };
    // Steering: diagonal only when the smaller offset is a real part of the move, so P2 doesn't zig-zag.
    const steerTo = (x, y, tx, ty) => {
      const dx = tx - x, dy = ty - y, ax = Math.abs(dx), ay = Math.abs(dy); let k = 0;
      if (ax > 2 && ax >= ay * 0.45) k |= dx > 0 ? K.RT : K.LT;
      if (ay > 2 && ay >= ax * 0.45) k |= dy > 0 ? K.D : K.U;
      return k;
    };
    const say2 = (msg) => { const now = performance.now(); if (now - lastNote < 12000) return; lastNote = now; show(msg, 2500); };
    const play = (f) => {
      const m = mem(1), now = performance.now();
      const idx = m.r8(0x03003F59) & 1, P = 0x03003C00 + 0x1AC * idx, O = 0x03003C00 + 0x1AC * (1 - idx);
      const hero = m.r32(P), hp = m.r16(P + 0x17C), oh = m.r32(O);
      if (!hero || !hp || hp > 5000 || !oh) { p2(0); plan = null; return; }
      const pos = (p) => [m.r16(p + 0xae), m.r16(p + 0xb2)];
      const [x, y] = pos(hero), [px, py] = pos(oh);
      // A cast in progress: put the old R skill back and learn what it cost.
      if (castPend) {
        if (f < castPend.at) { p2(0); return; }
        if (m.r8(P + 0x193) === castPend.s) w8both(P + 0x193, castPend.old);
        const d = castPend.sp0 - m.r16(P + 0x17E), key = m.r8(P + 0x19F) * 8 + castPend.s;
        if (d > 3) skillCost2.set(key, d); else noSkill2.set(key, now + 60000);
        p2casts[castPend.s] = (p2casts[castPend.s] || 0) + 1; castPend = null;
      }
      // After the Backpack menu: if the item is still in the pack, don't try that one again.
      if (eqPend && !wearRun) { const ok = m.r32(P + 0x5c + 4 * eqPend.k) !== eqPend.it; p2eq.push([(eqPend.it >>> 0).toString(16), ok]); if (!ok) noGear.add(eqPend.it); eqPend = null; }
      if (!grid || now - gridT > 2000) {
        gridT = now; grid = null; plan = null;
        const W = m.r16(0x03005F90), Hh = m.r16(0x03005F88), bm = m.r32(0x0300206C), ct = m.r32(0x03002068);
        if (W && Hh && W <= 512 && Hh <= 512) {
          const bw = W >> 2, cell = new Uint8Array(W * Hh), free = new Uint8Array(W * Hh);
          for (let cy = 0; cy < Hh; cy++) for (let cx = 0; cx < W; cx++) { const b = m.r16(bm + 2 * ((cx >> 2) + (cy >> 2) * bw)) & 0xfff, v = m.r8(ct + (b << 4) + ((cx & 3) | ((cy & 3) << 2))) & 7; cell[cx + cy * W] = v === 1 || v === 2 ? 0 : 1; }
          for (let cy = 1; cy < Hh - 1; cy++) for (let cx = 1; cx < W - 1; cx++) { const i = cx + cy * W; free[i] = cell[i] & cell[i - 1] & cell[i + 1]; }
          grid = { W, H: Hh, free };
        }
      }
      if (!grid) { p2(0); return; }
      const list = []; { let p = hero, n = 0; while (p && n++ < 400) { const nx = m.r32(p); if (!nx || nx >>> 24 !== 2) break; p = nx; } n = 0; while (p && p >>> 24 === 2 && n++ < 400) { list.push(p); p = m.r32(p + 4); } }
      const inView = (tx, ty) => Math.abs(tx - px) <= 100 && Math.abs(ty - py) <= 62;
      const en = [], items = [], ids = new Set();
      for (const p of list) {
        const u = m.r32(p + 0x14);
        if (u === ENEMY_UPD) {
          if (DEAD.has(m.r8(p + 0x62)) || m.r8(p + 0x63) === 0x2f || (m.r32(p + 0xe8) & 2)) continue;
          const [ex, ey] = pos(p); if (!inView(ex, ey)) continue;
          ids.add(p);
          // Reaction time: a newly seen enemy is noticed 0.15 to 0.3 s later.
          if (!seen.has(p)) seen.set(p, now + 150 + Math.random() * 150);
          if (seen.get(p) <= now) en.push(p);
        } else if (u === ITEM_UPD && m.r8(p + 0x63) === 3) {
          const t = m.r8(p + 0x60), [ix, iy] = pos(p); if (!inView(ix, iy)) continue;
          if (t >= 15 && t <= 24) items.push(p);
          else if (t >= 25 && !packFull(m, P) && upgrade(m, P, m.r32(p + 0x88))) items.push(p);
        }
      }
      if (seen.size > 64) for (const p of [...seen.keys()]) if (!ids.has(p)) seen.delete(p);
      const mhp = m.r16(P + 0xD0), low = hp * 10 < mhp * 4, veryLow = hp * 10 < mhp * 3;
      if (hp < p2Hp) p2HurtAt = now; p2Hp = hp;
      const elite = (p) => (m.r8(p + 0x60) & 1) === 0 || (m.r16(p + 0x5A) << 16 >> 16) >= 40;
      const dist = (p) => { const [ex, ey] = pos(p); return Math.abs(ex - x) + Math.abs(ey - y); };
      const close = en.some((p) => dist(p) < 70);
      // Ranger (Legolas, Jordan 2026-11-08): keeps bow distance behind P1, lines up on a row, column or diagonal
      // before shooting, steps back when an enemy gets close, and shoots the enemies on P1 first.
      const ranger = m.r8(P + 0x19F) === 1;
      const onP1 = (p) => { const [ex, ey] = pos(p); return Math.abs(ex - px) + Math.abs(ey - py) < 44; };
      const lined = (ex, ey) => {
        const dx = ex - x, dy = ey - y, ax = Math.abs(dx), ay = Math.abs(dy);
        if (ay <= 7 && ax >= 20 && ax <= 112) return true;
        if (ax <= 7 && ay >= 20 && ay <= 76) return true;
        return Math.abs(ax - ay) <= 8 && ax >= 18 && ax <= 76;
      };
      const rTargets = ranger ? en.slice().sort((a, b) => (onP1(b) - onP1(a)) * 2 + (elite(b) - elite(a)) || dist(a) - dist(b)) : [];
      // spots to shoot target p from, nearest P2 first: on its row (either side), its column, its diagonals
      const aimSpots = (p) => {
        const [ex, ey] = pos(p), out = [];
        for (const [ox, oy] of [[72, 0], [-72, 0], [56, 0], [-56, 0], [0, 52], [0, -52], [46, 46], [-46, 46], [46, -46], [-46, -46]]) {
          const sx = ex + ox, sy = ey + oy;
          if (freeAt(sx, sy) && clear(sx, sy, ex, ey)) out.push([sx, sy]);
        }
        // nearest P2, and on P1's side of the target (P1 stays the front line)
        const c = (q) => Math.abs(q[0] - x) + Math.abs(q[1] - y) + 0.6 * (Math.abs(q[0] - px) + Math.abs(q[1] - py));
        return out.sort((a, b) => c(a) - c(b));
      };
      const fighting = now - p2HurtAt < 3000 && close;
      const food = (t) => t === 15 || t === 16 || t === 19, gear = (t) => t >= 25;
      const want = items.filter((p) => { const t = m.r8(p + 0x60); return food(t) ? hp < mhp && (!fighting || low) : !fighting && !(gear(t) && close); });
      en.sort((a, b) => elite(b) - elite(a));
      dbg = { x, y, px, py, en: en.length, items: items.length, hp, mhp, retreat: !!retreatT, goal: lastGoalKey, ranger, shots: rangerShots, near: en.length ? Math.min(...en.map(dist)) : -1 };
      const at = (p, r) => { const [ix, iy] = pos(p); return Math.abs(ix - x) <= r && Math.abs(iy - y) <= r; };
      // Low HP: food right next to P2 comes before anything else.
      if (low) for (const p of want) if (food(m.r8(p + 0x60)) && at(p, 8)) { seq([[K.R, 4], [0, 6]], f); return; }
      // Wear an upgrade picked up earlier (the game's Backpack menu: Start, move to it, A, A), when no enemy is near.
      if (P2_WEARS && !close && !eqPend && now - (wearT || 0) > 3000) {
        const k = toWear(m, P);
        if (k >= 0) { wearT = now; const it = m.r32(P + 0x5c + 4 * k); eqPend = { k, it, t: now }; slog("P2 wears " + (it >>> 0).toString(16)); wearMacro(k, f); return; }
      }
      // Backing off: health very low with enemies near and no food at hand: go behind P1 for a few seconds.
      const nearFood = want.some((p) => food(m.r8(p + 0x60)) && dist(p) < 40);
      if (veryLow && close && !nearFood && now > retreatCool) { if (!retreatT) { retreatT = now; say2("P2 is low on health!"); } }
      if (retreatT && (!veryLow || now - retreatT > 4000)) { retreatT = 0; retreatCool = now + 8000; }
      // Picking up beats swinging (Jordan, 2026-11-08): an item at P2's feet is taken first if there's room for it.
      for (const p of items) {
        if (!at(p, 8) || (p2Tries.get(p) || 0) > 6) continue;
        const t = m.r8(p + 0x60);
        const ok = food(t) ? hp < mhp : gear(t) ? true : t === 17 ? (m.r8(P + 0x1AA) >> 4) < 10 : t === 18 ? (m.r8(P + 0x1AA) & 15) < 10 : true;
        if (ok) { p2Tries.set(p, (p2Tries.get(p) || 0) + 1); seq([[K.R, 4], [0, 6]], f); return; }
      }
      if (p2Tries.size > 64) p2Tries.clear();
      // An unopened chest at P2's feet: open it (B, which works as R there, like the player's B).
      for (const p of list) if (m.r32(p + 0x14) === 0x08014a3d && !m.r8(p + 0x85) && (p2Tries.get(p) || 0) <= 6) {
        const [bx, by] = pos(p); if (bx - x >= -18 && bx - x <= 22 && Math.abs(by - y) <= 24) { p2Tries.set(p, (p2Tries.get(p) || 0) + 1); seq([[0, 6], [K.R, 6], [0, 20]], f); return; }
      }
      if (!retreatT && ranger && en.length) {
        // Too close: step back away from the nearest enemy (toward P1's side), unless there is no room.
        let near = null, nd = 1e9;
        for (const p of en) { const d = dist(p); if (d < nd) { nd = d; near = p; } }
        if (near && nd < 34 && now - (kiteT || 0) > 250) {
          const [ex, ey] = pos(near); let ax = x - ex, ay = y - ey; const l = Math.hypot(ax, ay) || 1; ax /= l; ay /= l;
          const bx = px - x, by = py - y, bl = Math.hypot(bx, by) || 1;
          let tx = x + ax * 30 + bx / bl * 10, ty = y + ay * 24 + by / bl * 8;
          if (!freeAt(Math.round(tx), Math.round(ty)) || !clear(x, y, tx, ty)) { tx = x + ay * 30; ty = y - ax * 24; if (!freeAt(Math.round(tx), Math.round(ty)) || !clear(x, y, tx, ty)) { tx = x - ay * 30; ty = y + ax * 24; } }
          if (freeAt(Math.round(tx), Math.round(ty)) && clear(x, y, tx, ty)) { kiteT = now; plan = null; seq([[steerTo(x, y, tx, ty), 7]], f); return; }
        }
        // Lined up with a target and a clear shot: face it and shoot (skills on elites and groups).
        for (const p of rTargets) {
          const [ex, ey] = pos(p);
          if (!lined(ex, ey) || !clear(x, y, ex, ey)) continue;
          const face = steerTo(x, y, ex, ey) || 0;
          const group = en.filter((q) => { const [qx, qy] = pos(q); return Math.abs(qx - ex) + Math.abs(qy - ey) <= 48; }).length >= 3;
          if ((elite(p) || group) && now - castT2 > 1500 + Math.random() * 600) {
            const s = pickSkill2(m, P, now);
            if (s >= 0) {
              castT2 = now;
              w8both(0x03005820, m.r8(0x03005820) | 8); w8both(P + 0x19A, m.r8(P + 0x19A) | 2);
              castPend = { s, old: m.r8(P + 0x193), sp0: m.r16(P + 0x17E), at: f + 40 };
              w8both(P + 0x193, s);
              seq([[face, 1], [K.L, 5], [K.L | K.R, 8], [K.L, 4], [0, 21]], f); return;
            }
          }
          rangerShots++;
          seq([[face, 1], [K.B, 4], [0, 4 + ((Math.random() * 5) | 0)]], f); return;
        }
      }
      if (!retreatT) {
        // Hit an enemy next to P2 (elites first); skills on elites and groups.
        for (const p of en) {
          const [ex, ey] = pos(p);
          if (Math.abs(ex - x) <= 22 && Math.abs(ey - y) <= 16) {
            const face = steerTo(x, y, ex, ey) || 0;
            const group = en.filter((q) => dist(q) <= 56).length >= 2;
            if ((elite(p) || group) && now - castT2 > 1200 + Math.random() * 600) {
              const s = pickSkill2(m, P, now);
              if (s >= 0) {
                castT2 = now;
                w8both(0x03005820, m.r8(0x03005820) | 8); w8both(P + 0x19A, m.r8(P + 0x19A) | 2);
                castPend = { s, old: m.r8(P + 0x193), sp0: m.r16(P + 0x17E), at: f + 40 };
                w8both(P + 0x193, s);
                seq([[face, 2], [K.L, 5], [K.L | K.R, 8], [K.L, 4], [0, 21]], f); return;
              }
            }
            // Swing, with a small random pause like a person's rhythm.
            // P2's B works like the player's B, except gear that isn't an upgrade (or has no room) is left on the floor.
            const bList = list.filter((p) => !(m.r32(p + 0x14) === ITEM_UPD && m.r8(p + 0x60) >= 25 && !items.includes(p)));
            const bk = window.__bAct && window.__bAct(m, P, bList, false) ? K.R : K.B;
            seq([[face, 2], [bk, 4], [0, 3 + ((Math.random() * 5) | 0)]], f); return;
          }
        }
        for (const p of want) if (at(p, 8)) { seq([[K.R, 4], [0, 6]], f); return; }
      }
      // Where to go (planned about 7 times a second): back off behind P1; food when low; an enemy (elites count
      // 40 steps nearer), from the side away from P1; an item; else a spot beside P1.
      if (!plan || now - plan.t > 150) {
        const prev = bfs(x, y);
        let best = null, bestSc = 1e9, key = "";
        const consider = (tx, ty, r, bonus, k) => { const path = pathTo(prev, tx, ty, r); if (path && path.length - (bonus || 0) < bestSc) { best = path; bestSc = path.length - (bonus || 0); key = k; } };
        if (retreatT && en.length) {
          let cx = 0, cy = 0; for (const p of en) { const [ex, ey] = pos(p); cx += ex; cy += ey; } cx /= en.length; cy /= en.length;
          const dx = px - cx, dy = py - cy, l = Math.hypot(dx, dy) || 1;
          consider(Math.round(px + dx / l * 28), Math.round(py + dy / l * 20), 2, 0, "back");
        }
        if (!best && low) for (const p of want) { if (!food(m.r8(p + 0x60))) continue; const [ix, iy] = pos(p); consider(ix, iy, 1, 0, "food"); }
        if (!best && !retreatT && ranger) for (const p of rTargets.slice(0, 3)) {
          const sp = aimSpots(p);
          for (const [sx, sy] of sp.slice(0, 3)) consider(sx, sy, 1, onP1(p) ? 30 : elite(p) ? 15 : 0, "aim");
        }
        if (!best && !retreatT && !ranger) for (const p of en) {
          let [ex, ey] = pos(p);
          // P1 is on this enemy already: come at it from the other side.
          const fx = ex - px, fy = ey - py, fl = Math.hypot(fx, fy);
          if (fl < 48 && fl > 1) { const sx = Math.round(ex + fx / fl * 16), sy = Math.round(ey + fy / fl * 10); if (freeAt(sx, sy)) { ex = sx; ey = sy; } }
          consider(ex, ey, 2, elite(p) ? 40 : 0, "enemy");
        }
        if (!best) for (const p of want) { const [ix, iy] = pos(p); consider(ix, iy, 1, 0, gear(m.r8(p + 0x60)) ? "gear" : "item"); }
        if (!best) {
          // Beside P1, on the side P2 is already on.
          if (Math.abs(x - px) > 10) side = x < px ? -1 : 1;
          let sx = px + side * 26, sy = py + 4;
          if (ranger) { sx = px + side * 34; sy = py + 10; }
          if (!freeAt(sx, sy)) { sx = px - side * 26; if (freeAt(sx, sy)) side = -side; else { sx = px; sy = py; } }
          if (Math.abs(sx - x) + Math.abs(sy - y) > 18) consider(sx, sy, 1, 0, "follow");
        }
        plan = { path: best, t: now, key, i: 0 }; lastGoalKey = key;
      }
      if (!plan.path) { hist = []; p2(0); return; }
      // Follow the plan: find where P2 is on the path, then head for the furthest point ahead it can see.
      const W = grid.W, path = plan.path, here = (x >> 3) + (y >> 3) * W;
      let bi = plan.i, bd = 1e9;
      for (let i = plan.i; i < Math.min(path.length, plan.i + 12); i++) { const c = path[i], d = Math.abs((c % W) * 8 + 4 - x) + Math.abs(((c / W) | 0) * 8 + 4 - y); if (d < bd) { bd = d; bi = i; } }
      plan.i = bi;
      if (bi >= path.length - 1 && bd < 6) { plan = null; p2(0); return; }
      let tgt = path[Math.min(bi + 1, path.length - 1)];
      for (let j = Math.min(path.length - 1, bi + 10); j > bi + 1; j--) { const c = path[j]; if (clear(x, y, (c % W) * 8 + 4, ((c / W) | 0) * 8 + 4)) { tgt = path[j]; break; } }
      const k = steerTo(x, y, (tgt % W) * 8 + 4, ((tgt / W) | 0) * 8 + 4);
      hist.push([x, y, now]); while (hist.length && now - hist[0][2] > 600) hist.shift();
      if (hist.length > 4 && Math.abs(hist[0][0] - x) + Math.abs(hist[0][1] - y) < 4) {
        hist = []; plan = null;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const b = tgt + dx + dy * W; if (b !== here && b >= 0) blocked.set(b, now + 8000); }
        seq(Math.random() < 0.5 ? [[k, 2], [K.B, 4], [0, 4]] : [[[K.U, K.D, K.LT, K.RT][(Math.random() * 4) | 0], 10]], f); return;
      }
      seq([[k, 6]], f);
    };
    let wearT = 0;
    // Backpack menu for P2 (state 10 in P2's game only; P1 plays on): Start until it opens, move the cursor
    // (grid 4 x 2) to slot k, A (item menu, sub 1), A (Equip), then B until P2 is back in play.
    let wearRun = null;
    const wearMacro = (k, f) => { wearRun = { k, phase: "open", t: f, tries: 0, outs: 0, log: [] }; };
    const runWear = (f, s1) => {
      const w = wearRun, sb = sub(1);
      if (f - w.t > 900 && w.phase !== "out") { w.log.push("timeout " + w.phase); w.phase = "out"; }
      if (w.phase === "open") {
        if (s1 === 10) { w.phase = "move"; w.t10 = f; p2(0); return; }
        if (++w.tries > 4) { w.log.push("no menu"); w.phase = "out"; return; }
        seq([[K.START, 8], [0, 40]], f); return;
      }
      if (w.phase === "move") {
        if (f - w.t10 < 40) { p2(0); return; }
        const st = []; for (let i = 0; i < (w.k & 3); i++) st.push([K.RT, 6], [0, 14]); for (let i = 0; i < (w.k >> 2); i++) st.push([K.D, 6], [0, 14]);
        st.push([K.A, 8], [0, 45]); w.phase = "a1"; seq(st, f); return;
      }
      if (w.phase === "a1") { w.log.push("a1 sub " + sb); if (s1 === 10 && sb === 1) { w.phase = "a2"; seq([[K.A, 8], [0, 60]], f); } else w.phase = "out"; return; }
      if (w.phase === "a2") { w.log.push("a2 sub " + sb); w.phase = "out"; return; }
      if (w.phase === "out") {
        if (s1 === 1) { p2eq.push(w.log.join(", ")); wearRun = null; p2(0); return; }
        if (++w.outs > 8) { p2eq.push(w.log.join(", ") + ", stuck in " + s1); wearRun = null; return; }
        seq([[K.B, 8], [0, 40]], f); return;
      }
    };
    // A short run of buttons: [keys, frames] each, played by frame count.
    const seq = (steps, f) => { let t = f; seqRun = steps.map(([k, n]) => { t += n; return { k, end: t }; }); p2(seqRun[0].k); };
    const bfs = (x, y) => {
      const { W, H: Hh } = grid, now = performance.now(), prev = new Int32Array(W * Hh).fill(-2), q = new Int32Array(W * Hh);
      let free = grid.free;
      if (blocked.size) { free = free.slice(); for (const [c, t] of blocked) { if (t < now) blocked.delete(c); else free[c] = 0; } }
      let qh = 0, qt = 0; const s = (x >> 3) + (y >> 3) * W;
      if (s < 0 || s >= W * Hh) return prev;
      prev[s] = -1; q[qt++] = s;
      if (!free[s]) for (let r = 1; r <= 3 && qt === 1; r++) for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const n = s + dx + dy * W; if (n >= 0 && n < W * Hh && free[n] && prev[n] === -2) { prev[n] = s; q[qt++] = n; } }
      const D = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];
      // Only search near P1's screen (keeps it quick).
      while (qh < qt && qh < 6000) {
        const c = q[qh++], cx = c % W, cy = (c / W) | 0;
        for (const [dx, dy] of D) {
          const nx = cx + dx, ny = cy + dy; if (nx < 1 || ny < 1 || nx >= W - 1 || ny >= Hh - 1) continue;
          const n = nx + ny * W; if (prev[n] !== -2 || !free[n]) continue;
          if (dx && dy && !(free[cx + dx + cy * W] && free[cx + ny * W])) continue;
          prev[n] = c; q[qt++] = n;
        }
      }
      return prev;
    };
    const pathTo = (prev, tx, ty, r) => {
      const { W, H: Hh } = grid; let best = -1, bd = 1e9;
      for (let cy = (ty >> 3) - r; cy <= (ty >> 3) + r; cy++) for (let cx = (tx >> 3) - r; cx <= (tx >> 3) + r; cx++) {
        if (cx < 0 || cy < 0 || cx >= W || cy >= Hh) continue;
        const i = cx + cy * W; if (prev[i] === -2) continue;
        const d = Math.abs(cx * 8 + 4 - tx) + Math.abs(cy * 8 + 4 - ty); if (d < bd) { bd = d; best = i; }
      }
      if (best < 0) return null;
      const path = []; for (let c = best; c >= 0; c = prev[c]) { path.push(c); if (path.length > 4000) break; }
      return path.reverse();
    };
    const loop = () => {
      try {
        if (seqRun && !boot && !macro) {
          const f = frames();
          while (seqRun.length && f >= seqRun[0].end) seqRun.shift();
          if (seqRun.length) { p2(seqRun[0].k); return; }
          seqRun = null;
        }
        tick();
      } catch (e) { p2(0); }
    };
    every(loop, 8);
    // If the 2-player engine ever stops, say so; the P2 button still goes back to 1 player (saved games are kept).
    let wdF = -1, wdT = performance.now(), wdSaid = false;
    every(() => {
      let f = -1; try { f = frames(); } catch (e) {}
      const now = performance.now();
      if (f !== wdF || document.visibilityState !== "visible") { wdF = f; wdT = now; return; }
      if (!wdSaid && now - wdT > 6000) { wdSaid = true; slog("engine stopped at frame " + f); say("The 2-player game stopped. Tap P2 to go back to 1 player."); }
    }, 1000);
    window.__p2Tick = () => { if (document.visibilityState === "hidden") loop(); };
    window.__p2 = { get boot() { return boot && boot.phase; }, get macro() { return macro && macro.phase; }, get keys() { return p2keys; }, get wrote() { return wrote; }, state: () => [state(0), sub(0), state(1), sub(1)], lastSave: () => lastSave, get dbg() { return dbg; }, casts: p2casts, costs: skillCost2, eq: p2eq };
    return ctl;
  }
  // Sharp HD for the wide view (Jordan, 2026-11-07: "Upgrade graphics"): the same passes as Classic's picture
  // (our scene pass, then ScaleFX at 3x), run here with WebGL2 because this engine draws its own pictures.
  // Returns null when the phone can't run it; the caller then draws plain pixels.
  function makeSharpHD(gl) {
    try {
      const src = {}; for (const r of SCALEFX_PRESET.resources) src[r.name] = r.type === "base64" ? atob(r.value) : r.value;
      src["rotk-enhance.glsl"] = ROTK_ENHANCE_GLSL;
      const order = ["rotk-enhance.glsl", "scalefx-pass0.glsl", "scalefx-pass1.glsl", "scalefx-pass2.glsl", "scalefx-pass3.glsl", "scalefx-pass4.glsl"];
      const floatFB = !!gl.getExtension("EXT_color_buffer_float") || !!gl.getExtension("EXT_color_buffer_half_float");
      const sh = (type, text) => { const s = gl.createShader(type); gl.shaderSource(s, text); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
      const prog = (text) => {
        const body = text.replace(/^\s*#version[^\n]*\n/, "").replace(/uniform\s+COMPAT_PRECISION\s+/g, "uniform highp ");
        const p = gl.createProgram();
        gl.attachShader(p, sh(gl.VERTEX_SHADER, "#version 300 es\n#define VERTEX\n" + body));
        gl.attachShader(p, sh(gl.FRAGMENT_SHADER, "#version 300 es\nprecision highp float;\nprecision highp int;\n#define FRAGMENT\n" + body));
        gl.bindAttribLocation(p, 0, "VertexCoord"); gl.bindAttribLocation(p, 1, "TexCoord");
        gl.linkProgram(p); if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
        const u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
        for (let i = 0; i < n; i++) { const a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); }
        return { p, u };
      };
      const BLIT = "#if defined(VERTEX)\nin vec4 VertexCoord; in vec4 TexCoord; out vec2 v; uniform mat4 MVPMatrix;\nvoid main(){ gl_Position = MVPMatrix * VertexCoord; v = TexCoord.xy; }\n#else\nprecision highp float; in vec2 v; out vec4 o; uniform sampler2D Texture;\nvoid main(){ o = vec4(texture(Texture, v).rgb, 1.0); }\n#endif\n";
      const passes = order.map((n) => prog(src[n])), blit = prog(BLIT);
      const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), gl.STATIC_DRAW);
      const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
      for (const loc of [0, 1]) { gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0); }
      const MVP = new Float32Array([2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, -1, -1, 0, 1]);
      const MVP_FLIP = new Float32Array([2, 0, 0, 0, 0, -2, 0, 0, 0, 0, 1, 0, -1, 1, 0, 1]);
      const tex = (w, h, fmt, filter) => {
        const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
        const f = { rgb: [gl.RGB8, gl.RGB, gl.UNSIGNED_BYTE], rgba: [gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE], float: [gl.RGBA16F, gl.RGBA, gl.HALF_FLOAT] }[fmt];
        gl.texImage2D(gl.TEXTURE_2D, 0, f[0], w, h, 0, f[1], f[2], null);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        return t;
      };
      let W = 0, Hh = 0, input = null, outs = [], fbs = [], frame = 0;
      const setup = (w, h) => {
        for (const t of outs) gl.deleteTexture(t); for (const f of fbs) gl.deleteFramebuffer(f); if (input) gl.deleteTexture(input);
        W = w; Hh = h; input = tex(w, h, "rgb", gl.NEAREST); outs = []; fbs = [];
        for (let i = 0; i < 6; i++) {
          const k = i === 5 ? 3 : 1, fl = (i === 1 || i === 2) && floatFB;
          const t = tex(w * k, h * k, fl ? "float" : "rgba", i === 5 ? gl.LINEAR : gl.NEAREST);
          const fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
          gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
          if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error("framebuffer " + i);
          outs.push(t); fbs.push(fb);
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      };
      // heap: bytes holding RGB888 rows of width `stride`; (sx, sy, w, h) is the part to show; dest is the
      // rectangle on the 960x720 canvas (top-left origin).
      // plain: skip the passes and show the pixels as they are (used when the phone is too slow for Sharp HD).
      return function draw(heap, off, stride, sx, sy, w, h, dest, plain) {
        if (gl.isContextLost()) return;
        if (w !== W || h !== Hh) setup(w, h);
        gl.bindVertexArray(vao); gl.disable(gl.BLEND); gl.disable(gl.DEPTH_TEST);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, input);
        gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1); gl.pixelStorei(gl.UNPACK_ROW_LENGTH, stride);
        gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, sx); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, sy);
        gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, w, h, gl.RGB, gl.UNSIGNED_BYTE, heap, off);
        gl.pixelStorei(gl.UNPACK_ROW_LENGTH, 0); gl.pixelStorei(gl.UNPACK_SKIP_PIXELS, 0); gl.pixelStorei(gl.UNPACK_SKIP_ROWS, 0);
        frame++;
        let srcTex = input;
        for (let i = 0; i < (plain ? 0 : 6); i++) {
          const P = passes[i], u = P.u, k = i === 5 ? 3 : 1;
          gl.useProgram(P.p); gl.bindFramebuffer(gl.FRAMEBUFFER, fbs[i]); gl.viewport(0, 0, w * k, h * k);
          gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, srcTex);
          if (u.Texture) gl.uniform1i(u.Texture, 0);
          if (u.MVPMatrix) gl.uniformMatrix4fv(u.MVPMatrix, false, MVP);
          if (u.TextureSize) gl.uniform2f(u.TextureSize, w, h);
          if (u.InputSize) gl.uniform2f(u.InputSize, w, h);
          if (u.OutputSize) gl.uniform2f(u.OutputSize, w * k, h * k);
          if (u.FrameCount) gl.uniform1i(u.FrameCount, frame);
          if (u.FrameDirection) gl.uniform1i(u.FrameDirection, 1);
          // In the preset, pass 3 reads pass 1's output (PassPrev2) and pass 5 reads pass 0's output (PassPrev5).
          const prev = i === 3 ? ["PassPrev2Texture", outs[1]] : i === 5 ? ["PassPrev5Texture", outs[0]] : null;
          if (prev && u[prev[0]]) {
            gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, prev[1]); gl.uniform1i(u[prev[0]], 1);
            const n = prev[0].replace("Texture", "");
            if (u[n + "TextureSize"]) gl.uniform2f(u[n + "TextureSize"], w, h);
            if (u[n + "InputSize"]) gl.uniform2f(u[n + "InputSize"], w, h);
          }
          gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
          srcTex = outs[i];
        }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null);
        const cw = gl.drawingBufferWidth, ch = gl.drawingBufferHeight;
        gl.viewport(0, 0, cw, ch); gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.viewport(dest[0], ch - dest[1] - dest[3], dest[2], dest[3]);
        gl.useProgram(blit.p); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, plain ? input : outs[5]);
        gl.uniform1i(blit.u.Texture, 0); gl.uniformMatrix4fv(blit.u.MVPMatrix, false, MVP_FLIP);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      };
    } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("sharp: " + (e && e.message || e)); return null; }
  }
  // Page side of the wide-view engine: pictures, buttons and sound go through one shared block in the engine's memory.
  window.__wideHold = (ms) => {
    WideHost.holdT = performance.now() + ms;
    const g = WideHost.gain; if (!g || !g.gain || g.gain.value === 0) return;
    const v = g.gain.value; g.gain.value = 0; setTimeout(() => { if (g.gain.value === 0) g.gain.value = v; }, ms);
  };
  const WideHost = {
    canvas: null, ctx: null, img: null, keys: 1023, audio: null, out: null, audioT: 0, frames: 0, front: 0, d: null,
    attach(getBuf, ptr, d) { this.getBuf = getBuf; this.ptr = ptr; this.d = d; this.st("audioReady", 1); this.st("hostRate", 48000); return true; },
    u32() { const b = this.getBuf(); if (this._b !== b) { this._b = b; this._u = new Uint32Array(b); this._u8 = new Uint8Array(b); this._i16 = new Int16Array(b); } return this._u; },
    ld(k) { return this.u32()[(this.ptr >> 2) + this.d.fields[k]] >>> 0; },
    st(k, v) { if (this.d && this.d.fields[k] !== undefined) this.u32()[(this.ptr >> 2) + this.d.fields[k]] = v >>> 0; },
    detach() { this.st("detached", 1); },
    configure() {}, fullscreenRequest() {}, configureTouch() {}, setPadVisible() {}, haptic() {}, requestSettings() {}, ended() {},
    // Canvas size = the picture area in the screen's own pixels (checked on resize and turning the phone).
    fit() {
      this.fitDue = false;
      const el = this.canvas, r = (el.parentElement || el).getBoundingClientRect(), d = window.devicePixelRatio || 1;
      const W = Math.max(1, Math.round(r.width * d)), H = Math.max(1, Math.round(r.height * d));
      if (r.width > 0 && r.height > 0 && (el.width !== W || el.height !== H)) { el.width = W; el.height = H; }
    },
    draw() {
      if (!this.d || !this.canvas) return;
      this.st("keys", this.keys);
      const m = this.ld("middle");
      if (m & 4) { this.st("middle", this.front); this.front = m & 3; this.frames++; } else { this.pumpAudio(); return; }
      if (this.holdT && performance.now() < this.holdT) { this.pumpAudio(); return; }   // picture held still (Undo's redraw flip)
      const base = this.ptr + this.d.video + this.front * this.d.videoStride, u = this.u32(), w = u[base >> 2], h = u[(base >> 2) + 1];
      if (w && h && w <= this.d.maxWidth && h <= this.d.maxHeight) {
        // The canvas matches the screen's own pixels and the picture fills the whole game area (Jordan, 2026-11-08).
        // Levels already have the area's shape (the view width is chosen to match); menus (240x160) are stretched.
        let native = false; try { native = !!(this.nativeView && this.nativeView()); } catch (e) {}
        if (this.fitDue !== false) this.fit();
        const CW = this.canvas.width, CH = this.canvas.height;
        let sx = 0, sy = 0, sw = w, sh = h;
        if (native && w >= 240 && h >= 160) { sx = (w - 240) >> 1; sy = (h - 160) >> 1; sw = 240; sh = 160; }
        let dest = [0, 0, CW, CH];
        // The 2-player game's narrower view keeps its shape (black bars at the sides) instead of stretching.
        if (this.keepAspect && !native && w > 0 && h > 0) { const k = Math.min(CW / w, CH / h), dw = Math.round(w * k), dh = Math.round(h * k); dest = [(CW - dw) >> 1, (CH - dh) >> 1, dw, dh]; }
        if (this.sharp) {
          // If the picture rate stays under 40 a second with Sharp HD on, this phone can't keep up: plain pixels from then on.
          const now = performance.now();
          if (!this.rateT || document.visibilityState !== "visible") { this.rateT = now; this.rateF = this.frames; }
          else if (now - this.rateT > 4000) {
            const fps = (this.frames - this.rateF) * 1000 / (now - this.rateT);
            this.slow = !this.plain && fps < 40 ? (this.slow || 0) + 1 : 0;
            if (this.slow >= 2) { this.plain = true; (window.__wideLog || (window.__wideLog = [])).push("sharp off, fps " + fps.toFixed(1)); }
            this.rateT = now; this.rateF = this.frames;
          }
          if (window.__capF) window.__capF(this._u8, base + this.d.pixels, w, h);
          this.sharp(this._u8, base + this.d.pixels, w, sx, sy, sw, sh, dest, this.plain);
          this.pumpAudio(); return;
        }
        if (!this.buf) { this.buf = document.createElement("canvas"); this.bctx = this.buf.getContext("2d"); }
        if (this.buf.width !== w || this.buf.height !== h || !this.img) { this.buf.width = w; this.buf.height = h; this.img = this.bctx.createImageData(w, h); }
        const src = this._u8, dst = this.img.data, n = w * h;
        for (let i = 0, s = base + this.d.pixels, t = 0; i < n; ++i, s += 3, t += 4) { dst[t] = src[s]; dst[t + 1] = src[s + 1]; dst[t + 2] = src[s + 2]; dst[t + 3] = 255; }
        this.bctx.putImageData(this.img, 0, 0);
        const c = this.ctx; c.imageSmoothingEnabled = false;
        c.fillStyle = "#000"; c.fillRect(0, 0, CW, CH);
        c.drawImage(this.buf, sx, sy, sw, sh, dest[0], dest[1], dest[2], dest[3]);
      }
      this.pumpAudio();
    },
    pumpAudio() {
      const d = this.d; let r = this.ld("audioRead"); const w = this.ld("audioWrite");
      if (this.ld("resetRequest") !== this.ld("resetAck")) { this.st("audioRead", w); this.st("resetAck", this.ld("resetRequest")); return; }
      const ac = this.audio;
      if (!ac || ac.state !== "running") { this.st("audioRead", w); return; }
      while (r !== w) {
        const p = this.ptr + d.audio + (r & (d.audioSlots - 1)) * d.audioStride, u = this.u32(), n = u[p >> 2], rate = u[(p >> 2) + 1]; r = (r + 1) >>> 0;
        if (n < 1 || n > d.audioSamples || !rate) continue;
        const pcm = this._i16.subarray((p + 12) >> 1, ((p + 12) >> 1) + n), outN = Math.max(1, Math.round(n * ac.sampleRate / rate));
        // The engine runs one game frame per screen refresh (0.45% fast on a 60 Hz screen), so sound arrives a little
        // quicker than it plays. When it piles up, play 1% faster until it catches up instead of cutting it off.
        const ahead = this.audioT - ac.currentTime, fast = ahead > 0.14 ? 1.01 : 1;
        const outN2 = Math.max(1, Math.round(outN / fast));
        const buf = ac.createBuffer(1, outN2, ac.sampleRate), ch = buf.getChannelData(0), step = rate / ac.sampleRate * fast;
        for (let i = 0; i < outN2; ++i) { const x = i * step, j = x | 0, f = x - j, a = pcm[j] || 0, b = pcm[Math.min(n - 1, j + 1)] || 0; ch[i] = (a + (b - a) * f) / 32768; }
        const now = ac.currentTime;
        if (this.audioT < now + 0.02 || this.audioT > now + 0.3) this.audioT = now + 0.08;
        const s = ac.createBufferSource(); s.buffer = buf; s.connect(this.out || ac.destination); s.start(this.audioT); this.audioT += outN2 / ac.sampleRate;
      }
      this.st("audioRead", r);
    },
  };
