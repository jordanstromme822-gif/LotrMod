// Play Room v98: the P2 helper (inside the page's main script; uses $, WideHost and startWide's engine).
  // ---------------- P2 helper (Jordan, 2026-11-08) ----------------
  // A P2 button next to Auto. In the wide view it lists the saved heroes that aren't the one being played; picking one
  // restarts as a 2-player link game (the PC app's engine runs both games side by side): both games load their own
  // slot, and P2 is played by the page like Auto, but it stays on P1's screen: it fights enemies near P1, picks up herbs
  // and food near P1, and otherwise follows P1. Only P1's picture is shown. When P1 saves (pause, Save Game), P2 saves
  // its own slot too, and both slots go into the one saved-games file. Tap P2 again to stop it.
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
  function wideP2({ M, H, readSave, save, link, setBoot, keepSave }) {
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
      const m = mem(0), cur = m.ok ? m.r8(0x03005834) : -1, lvl = m.ok ? m.r8(0x030041F8) : 0;
      const list = p2SlotInfo(readSave() || save).filter((s) => s && s.slot !== cur);
      h.textContent = list.length ? "Pick P2's hero" : "No other saved heroes";
      const n = document.createElement("div"); n.className = "p2-note";
      n.textContent = list.length ? "The game starts again from your saved games with both heroes" + (lvl === 82 ? " in Moria" : "") + ", so save first." : "Start another hero in a free slot first, then P2 can play it.";
      panel.appendChild(n);
      for (const s of list) add((P2_HEROES[s.hero] || "Hero") + " · level " + s.level, () => { close(); restart({ p1: cur, p2: s.slot, moria: lvl === 82, at: Date.now() }); }, "p2-hero");
      add("Cancel", close);
    };
    btn.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); if (!panel.hidden) close(); else open(); });
    btn.addEventListener("click", (e) => e.preventDefault());
    btn.classList.toggle("on", linkOn); btn.setAttribute("aria-pressed", linkOn ? "true" : "false");
    // Page changes to game memory (skill slots, options) are copied into P2's game so both stay identical.
    if (linkOn) window.__mirrorIw = (off) => { const H8 = M.HEAPU8; H8[M._rotk_link_iwram(1) + off] = H8[M._rotk_link_iwram(0) + off]; };
    // The button shows while a hero is loaded in a level (state 1) or the game is paused, and always in a P2 game.
    setInterval(() => {
      let vis = linkOn;
      if (!vis) try { const m = mem(0); const st = m.r32(0x030041B0) & 255; vis = m.ok && (st === 1 || st === 16) && m.r8(0x03005834) < 4; } catch (e) {}
      btn.hidden = !vis; if (!vis && !panel.hidden) close();
    }, 500);
    if (!link) return;
    if (!linkOn) { try { sessionStorage.removeItem("rotk-p2"); } catch (e) {} show("P2 couldn't start, playing 1 player.", 5000); return; }

    // ---- 2-player game ----
    const K = { A: 1, B: 2, SEL: 4, START: 8, RT: 16, LT: 32, U: 64, D: 128, R: 256, L: 512 };
    const frames = () => M._rotk_link_frames() >>> 0;
    const state = (i) => mem(i).r32(0x030041B0) & 255, sub = (i) => mem(i).r8(0x030041C0), cursor = (i) => mem(i).r8(0x030041BC);
    let p2keys = 0; const p2 = (k) => { p2keys = k; try { M._rotk_link_p2(k); } catch (e) {} };
    // Presses: [frame to start, p1 keys, p2 keys, frames held]. The boot runs from the title to the level start.
    let boot = { phase: "title", t: 0, presses: [], tries: 0 }, macro = null;
    const press = (p1k, p2k, hold, after) => { const f0 = boot.presses.length ? boot.presses[boot.presses.length - 1].end : frames(); boot.presses.push({ at: f0, p1: p1k, p2: p2k, until: f0 + hold, end: f0 + hold + after }); };
    if (link.moria) try { M._rotk_link_level(82); } catch (e) {}
    setBoot(0);
    const say = (t) => { $("mpBanner").textContent = t; $("mpBanner").hidden = !t; };
    say("Starting the 2-player game…");
    const bootTick = () => {
      const f = frames();
      if (boot.presses.length) {
        const p = boot.presses[0];
        if (f < p.at) { setBoot(0); p2(0); return; }
        if (f < p.until) { setBoot(p.p1); p2(p.p2); return; }
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
    const fail = (why) => { slog("boot failed: " + why); boot = null; setBoot(null); p2(0); say(""); show("P2 couldn't start the game: " + why + ". You can play on as P1.", 6000); };
    const done = () => { slog("boot done, P1 slot " + link.p1 + ", P2 slot " + link.p2 + ", level " + mem(0).r8(0x030041F8)); boot = null; setBoot(null); p2(0); say(""); show("P2 joined", 2500); };

    // ---- Saves: both games keep their own copy; slot p2 comes from P2's game, the rest from P1's. ----
    const buf = M._malloc(512), copies = [save.slice(0, 512), save.slice(0, 512)], so = 0x40 + link.p2 * 0x70;
    let wrote = 0;
    setInterval(() => {
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
    const play = (f) => {
      const m = mem(1), now = performance.now();
      const me = 0x03003C00 + 0x1AC * (m.r8(0x03003F59) & 1), other = 0x03003C00 + 0x1AC * (1 - (m.r8(0x03003F59) & 1));
      const hero = m.r32(me), hp = m.r16(me + 0x17C), oh = m.r32(other);
      if (!hero || !hp || hp > 5000 || !oh) { p2(0); return; }
      const pos = (p) => [m.r16(p + 0xae), m.r16(p + 0xb2)];
      const [x, y] = pos(hero), [px, py] = pos(oh);
      if (!grid || now - gridT > 2000) {
        gridT = now; grid = null;
        const W = m.r16(0x03005F90), Hh = m.r16(0x03005F88), bm = m.r32(0x0300206C), ct = m.r32(0x03002068);
        if (W && Hh && W <= 512 && Hh <= 512) {
          const bw = W >> 2, cell = new Uint8Array(W * Hh), free = new Uint8Array(W * Hh);
          for (let cy = 0; cy < Hh; cy++) for (let cx = 0; cx < W; cx++) { const b = m.r16(bm + 2 * ((cx >> 2) + (cy >> 2) * bw)) & 0xfff, v = m.r8(ct + (b << 4) + ((cx & 3) | ((cy & 3) << 2))) & 7; cell[cx + cy * W] = v === 1 || v === 2 ? 0 : 1; }
          for (let cy = 1; cy < Hh - 1; cy++) for (let cx = 1; cx < W - 1; cx++) { const i = cx + cy * W; free[i] = cell[i] & cell[i - 1] & cell[i + 1]; }
          grid = { W, H: Hh, free };
        }
      }
      if (!grid) { p2(0); return; }
      // Entities: walk back to the list head from P2's hero, then forward.
      const list = []; { let p = hero, n = 0; while (p && n++ < 400) { const nx = m.r32(p); if (!nx || nx >>> 24 !== 2) break; p = nx; } n = 0; while (p && p >>> 24 === 2 && n++ < 400) { list.push(p); p = m.r32(p + 4); } }
      // P2 stays on P1's screen: everything it goes for is within this box around P1.
      const inView = (tx, ty) => Math.abs(tx - px) <= 100 && Math.abs(ty - py) <= 62;
      const en = [], items = [];
      for (const p of list) {
        const u = m.r32(p + 0x14);
        if (u === ENEMY_UPD) { if (!DEAD.has(m.r8(p + 0x62)) && m.r8(p + 0x63) !== 0x2f && !(m.r32(p + 0xe8) & 2)) { const [ex, ey] = pos(p); if (inView(ex, ey)) en.push(p); } }
        else if (u === ITEM_UPD && m.r8(p + 0x63) === 3) { const t = m.r8(p + 0x60); if (t >= 15 && t <= 24) { const [ix, iy] = pos(p); if (inView(ix, iy)) items.push(p); } }
      }
      dbg = { x, y, px, py, en: en.length, items: items.length };
      const steer = (tx, ty) => { let k = 0; if (tx - x > 2) k |= K.RT; if (tx - x < -2) k |= K.LT; if (ty - y > 2) k |= K.D; if (ty - y < -2) k |= K.U; return k; };
      // Same rules as Auto (Jordan, 2026-11-08): elites first (even tier byte +0x60 or 40+ HP at +0x5A); while
      // taking damage (HP down in the last 3 s) with an enemy near, fight and only take food that heals; food
      // (fruit 15, mushrooms 16, lembas 19) whenever hurt; herbs (17, 18, 20-24) when not fighting.
      const mhp = m.r16(me + 0xD0), low = hp * 10 < mhp * 4;
      if (hp < p2Hp) p2HurtAt = now; p2Hp = hp;
      const elite = (p) => (m.r8(p + 0x60) & 1) === 0 || (m.r16(p + 0x5A) << 16 >> 16) >= 40;
      const close = en.some((p) => { const [ex, ey] = pos(p); return Math.abs(ex - x) + Math.abs(ey - y) < 70; });
      const fighting = now - p2HurtAt < 3000 && close;
      const food = (t) => t === 15 || t === 16 || t === 19;
      const want = items.filter((p) => { const t = m.r8(p + 0x60); return food(t) ? hp < mhp && (!fighting || low) : !fighting; });
      en.sort((a, b) => elite(b) - elite(a));
      // Low HP: food right next to P2 comes before hitting.
      if (low) for (const p of want) { const [ix, iy] = pos(p); if (food(m.r8(p + 0x60)) && Math.abs(ix - x) <= 8 && Math.abs(iy - y) <= 8) { seq([[K.R, 4], [0, 6]], f); return; } }
      // Hit an enemy right next to P2 (elites first).
      for (const p of en) { const [ex, ey] = pos(p); if (Math.abs(ex - x) <= 22 && Math.abs(ey - y) <= 16) { seq([[steer(ex, ey), 2], [K.B, 4], [0, 4]], f); return; } }
      for (const p of want) { const [ix, iy] = pos(p); if (Math.abs(ix - x) <= 8 && Math.abs(iy - y) <= 8) { seq([[K.R, 4], [0, 6]], f); return; } }
      // Walk: food when low, else the nearest enemy near P1 (an elite counts 40 steps nearer), else a herb or food
      // near P1, else back next to P1.
      const prev = bfs(x, y);
      let best = null, bestSc = 1e9;
      const consider = (tx, ty, r, bonus) => { const path = pathTo(prev, tx, ty, r); if (path && path.length - (bonus || 0) < bestSc) { best = path; bestSc = path.length - (bonus || 0); } };
      if (low) for (const p of want) { if (!food(m.r8(p + 0x60))) continue; const [ix, iy] = pos(p); consider(ix, iy, 1); }
      if (!best || best.length > 25) { best = null; bestSc = 1e9; for (const p of en) { const [ex, ey] = pos(p); consider(ex, ey, 2, elite(p) ? 40 : 0); } }
      if (!best) for (const p of want) { const [ix, iy] = pos(p); consider(ix, iy, 1); }
      if (!best && Math.abs(px - x) + Math.abs(py - y) > 36) consider(px, py, 2);
      if (!best) { hist = []; p2(0); return; }
      const W = grid.W, c = best[Math.min(3, best.length - 1)];
      let k = steer((c % W) * 8 + 4, ((c / W) | 0) * 8 + 4);
      hist.push([x, y, now]); while (hist.length && now - hist[0][2] > 600) hist.shift();
      if (hist.length > 4 && Math.abs(hist[0][0] - x) + Math.abs(hist[0][1] - y) < 4) {
        // Stuck: mark the cells ahead as blocked for a while, swing, or step aside.
        hist = []; const here = (x >> 3) + (y >> 3) * W;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const b = c + dx + dy * W; if (b !== here && b >= 0) blocked.set(b, now + 8000); }
        seq(Math.random() < 0.5 ? [[k, 2], [K.B, 4], [0, 4]] : [[[K.U, K.D, K.LT, K.RT][(Math.random() * 4) | 0], 10]], f); return;
      }
      seq([[k, 4]], f);
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
    setInterval(loop, 8);
    // If the 2-player engine ever stops, say so; the P2 button still goes back to 1 player (saved games are kept).
    let wdF = -1, wdT = performance.now(), wdSaid = false;
    setInterval(() => {
      let f = -1; try { f = frames(); } catch (e) {}
      const now = performance.now();
      if (f !== wdF || document.visibilityState !== "visible") { wdF = f; wdT = now; return; }
      if (!wdSaid && now - wdT > 6000) { wdSaid = true; slog("engine stopped at frame " + f); say("The 2-player game stopped. Tap P2 to go back to 1 player."); }
    }, 1000);
    window.__p2Tick = () => { if (document.visibilityState === "hidden") loop(); };
    window.__p2 = { get boot() { return boot && boot.phase; }, get macro() { return macro && macro.phase; }, get keys() { return p2keys; }, get wrote() { return wrote; }, state: () => [state(0), sub(0), state(1), sub(1)], lastSave: () => lastSave, get dbg() { return dbg; } };
  }
