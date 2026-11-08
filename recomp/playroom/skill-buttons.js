// Play Room v109: skill buttons (icons inside, black when used, countdown), B's skill on L, B rules shared by player, Auto and P2 (bAct), B's longer pickup reach (__stepPick).
      const skIcons = [...document.querySelectorAll("#pad .sk")].sort((a, b) => a.dataset.slot - b.dataset.slot);   // A, B's skill (on L), R
      const skPos = (v) => (v[1] * 20) + "% " + (v[0] * 100 / 7).toFixed(3) + "%";   // sheet: 6 skills across, 8 heroes down
      // Used skills (Jordan, 2026-11-08): the pressed skill's icon turns black. If the game took Spirit for it and it's a
      // skill that lasts a while (times from the Skills page text, at the skill's level), a countdown runs on the button
      // and the icon stays black until it ends; otherwise it comes back after a moment.
      const SK_DUR = { 0: { 2: [2, 2], 3: [5, 2], 4: [10, 5] }, 1: { 4: [2.5, 0.5] }, 2: { 3: [5, 5] }, 3: { 0: [8, 8] },
        4: { 1: [10, 2], 2: [10, 0] }, 5: { 2: [3, 2], 3: [3, 2] }, 6: { 2: [2, 2] }, 7: { 2: [1.5, 0.5] } };
      let skPend = null; const skActive = new Map();
      const skillPressed = (btn, v) => {
        if (!btn || !v) return;
        try { const h = emu.Module.HEAPU8, P = heroPtr(); skPend = { btn, v, sp0: h[P + 0x17E] | h[P + 0x17F] << 8, lv: h[P + 0x16A + v[1]] << 24 >> 24, t: performance.now() }; } catch (e) { return; }
        btn.classList.add("used");
      };
      const skDone = (btn) => { btn.classList.remove("used"); const c = btn.querySelector(".cd"); if (c) c.remove(); skActive.delete(btn); };
      setInterval(() => {
        const now = performance.now();
        if (skPend) {
          let sp = skPend.sp0; try { const h = emu.Module.HEAPU8, P = heroPtr(); sp = h[P + 0x17E] | h[P + 0x17F] << 8; } catch (e) {}
          const { btn, v, lv } = skPend;
          if (skPend.sp0 - sp > 3) {
            skPend = null;
            const d = SK_DUR[v[0]] && SK_DUR[v[0]][v[1]], secs = d ? d[0] + d[1] * Math.max(0, lv - 1) : 0;
            if (secs > 0) {
              let c = btn.querySelector(".cd"); if (!c) { c = document.createElement("b"); c.className = "cd"; btn.appendChild(c); }
              skActive.set(btn, { end: now + secs * 1000, total: secs * 1000 });
            } else setTimeout(() => { if (!skActive.has(btn)) btn.classList.remove("used"); }, 500);
          } else if (now - skPend.t > 900) { if (!skActive.has(btn)) btn.classList.remove("used"); skPend = null; }
        }
        for (const [btn, a] of skActive) {
          const left = a.end - now; if (left <= 0 || inMenu()) { skDone(btn); continue; }
          const c = btn.querySelector(".cd"); if (!c) continue;
          c.textContent = String(Math.ceil(left / 1000)); c.style.setProperty("--p", (left / a.total).toFixed(3));
        }
      }, 100);
      [["b-a", 0], ["b-r", 2]].forEach(([c, k]) => {
        const b = document.querySelector("#pad ." + c);
        if (b) b.addEventListener("pointerdown", () => { const el = skIcons[k]; if (document.body.classList.contains("qs-on") && el && el.classList.contains("show")) skillPressed(b, el.__v); });
      });
      setInterval(() => {
        if (xCast) return;  // an extra skill button is borrowing the R slot for a moment
        let st = null;
        try {
          const h = emu.Module.HEAPU8;
          if (iwram >= 0 && h && !inMenu()) {
            const pl = h[iwram + 0x3F59] & 1, P = iwram + 0x3C00 + 0x1AC * pl, hero = h[P + 0x19F];
            if (hero < 8) st = [0, 1, 2].map((k) => { const s = h[P + 0x191 + k]; const lv = s < 6 ? (h[P + 0x16A + s] << 24 >> 24) : 0; return lv > 0 ? [hero, s] : null; });
          }
        } catch (e) {}
        skIcons.forEach((el, k) => {
          const v = st && st[k], key = v ? v.join(",") : "";
          if (el.__k === key) return; el.__k = key; el.__v = v; el.classList.toggle("show", !!v); el.parentElement.classList.toggle("has-sk", !!v);
          if (v) el.style.backgroundPosition = skPos(v);
        });
        document.body.classList.toggle("qs-on", qsOn);
        updateExtras();
      }, 250);
      // Extra skill buttons (Jordan, 2026-11-07): each learned active skill that isn't on A, B or R gets a button above A
      // and B. A tap puts that skill in the R slot for a moment, presses the game's own L + R (Quick Skill Select), then
      // puts the R skill back, so the game itself checks Spirit and plays the skill. Solo and Wide only: in a 2-player
      // link game changing memory on one side would split the two games apart. Keys 1, 2, 3 on a PC.
      const xBtns = [...document.querySelectorAll("#pad .xs")];
      const sheet = getComputedStyle(skIcons[0] || document.body).backgroundImage;
      xBtns.forEach((b) => { b.querySelector(".xi").style.backgroundImage = sheet; });
      const linked = () => !!(window.__mp && !window.__mp.wide);
      let xList = [];
      const heroPtr = () => { const h = emu.Module.HEAPU8; const pl = h[iwram + 0x3F59] & 1; return iwram + 0x3C00 + 0x1AC * pl; };
      function updateExtras() {
        let list = [];
        try {
          const h = emu.Module.HEAPU8;
          if (iwram >= 0 && h && !inMenu() && !linked()) {
            const P = heroPtr(), hero = h[P + 0x19F];
            if (hero < 8) {
              const slots = [h[P + 0x191], h[P + 0x192], h[P + 0x193]];
              for (let s = 0; s < 6 && list.length < 3; s++) if ((h[P + 0x16A + s] << 24 >> 24) > 0 && !slots.includes(s) && !(xCast && xCast.skill === s)) list.push([hero, s]);
              if (xCast) list = xList;  // keep the buttons steady while a skill is going off
            }
          }
        } catch (e) {}
        xList = list;
        const key = list.map((v) => v.join(",")).join(";");
        if (key === updateExtras.key) return; updateExtras.key = key;
        xBtns.forEach((b, k) => {
          const v = list[k]; b.classList.toggle("show", !!v);
          if (v) b.querySelector(".xi").style.backgroundPosition = skPos(v);
        });
        document.body.classList.toggle("has-xs", list.length > 0);
      }
      let xCast = null;
      const castExtra = (k) => {
        const v = xList[k]; if (!v || xCast || inMenu() || linked()) return;
        let P, h;
        try { h = emu.Module.HEAPU8; P = heroPtr(); } catch (e) { return; }
        const skill = v[1], old = h[P + 0x193];
        xCast = { skill };
        qsOption();
        h[P + 0x193] = skill; try { window.__mirrorIw && window.__mirrorIw(P + 0x193 - iwram); } catch (e) {}
        const btn = xBtns[k]; btn.classList.add("on"); skillPressed(btn, v);
        try { emu.gameManager.simulateInput(0, 10, 1); } catch (e) {}
        setTimeout(() => { try { emu.gameManager.simulateInput(0, 11, 1); } catch (e) {} }, 70);
        setTimeout(() => { try { emu.gameManager.simulateInput(0, 11, 0); } catch (e) {} sendL(); btn.classList.remove("on"); }, 200);
        setTimeout(() => {
          try { const h2 = emu.Module.HEAPU8, P2 = heroPtr(); if (h2[P2 + 0x193] === skill) { h2[P2 + 0x193] = old; try { window.__mirrorIw && window.__mirrorIw(P2 + 0x193 - iwram); } catch (e) {} } } catch (e) {}
          xCast = null; updateExtras.key = null; updateExtras();
        }, 420);
      };
      xBtns.forEach((b, k) => b.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); castExtra(k); }));
      window.addEventListener("keydown", (e) => { const k = "123".indexOf(e.key); if (k >= 0 && e.key.length === 1 && !e.repeat) castExtra(k); });
      // Auto mode for the Moria bonus map (Jordan, 2026-11-08). A button at the top left turns it on: the hero walks to the
      // nearest enemy (around walls, using the level's own collision map) and uses the main attack (B), picks up herbs and
      // food, turns the game's Auto Healing option on, and picks up gear only when it beats what the hero wears (gear the
      // hero can't wear is skipped, unless the only reason is the level). It visits the level's enemy triggers so every
      // wave appears, and turns itself off once no enemies are left. Solo and Wide only, like the extra skill buttons.
      (() => {
        const MORIA = 82, ENEMY_UPD = 0x0801b9d1, ITEM_UPD = 0x0802f131, TRIG_UPD = 0x0802ed21;
        // Pots and barrels (smash with B), chests (open with R) and the Spirit Shrine (R opens its shop; herbs are its third tab).
        const POT_UPD = 0x08046125, CHEST_UPD = 0x08014a3d, SHOP_UPD = 0x080200c9;
        const DEAD = new Set([0x11, 0x15, 4, 0x1b, 0x13]);
        const btn = $("autoBtn"), note = $("saveNote");
        let on = false, ew = -1, H8 = null, grid = null, gridT = 0, queue = [], qUntil = 0, keysDown = new Set();
        let picks = {}, lastHp = 0, hurtAt = 0, itemTriesT = 0, hist = [], stuck = 0, tries = new Map(), blocked = new Map(), skip = new Map(), macro = null, noEquip = new Set(), shrineAt = [1385, 1214], shopT = 0, shopNear = 30, shopDone = false, known = null, fresh = new Set(), dropOff = false, lastLog = 0, idleSince = 0, unreachSince = 0, userUntil = 0, oldHeal = null, lastSeen = 0, kills = 0;
        const rom = () => window.__romFull;
        const heap = () => emu.Module.HEAPU8;
        const findEw = () => {
          try { if (window.__mp && window.__mp.wide && window.__mp.M._rotk_ewram) return window.__mp.M._rotk_ewram(); } catch (e) {}
          return iwram >= 0x40000 ? iwram - 0x40000 : -1;
        };
        const at = (a) => ((a >>> 24) === 3 ? iwram + (a & 0x7fff) : (a >>> 24) === 2 ? ew + (a & 0x3ffff) : -1);
        const r8 = (a) => { const o = at(a); return o >= 0 ? H8[o] : 0; };
        const r16 = (a) => { const o = at(a); return o >= 0 ? H8[o] | H8[o + 1] << 8 : 0; };
        const r32 = (a) => { const o = at(a); return o >= 0 ? (H8[o] | H8[o + 1] << 8 | H8[o + 2] << 16 | H8[o + 3] << 24) >>> 0 : 0; };
        // In a P2 game the same change is made in P2's game too (window.__mirrorIw), so the two games stay identical.
        const w8 = (a, v) => { const o = at(a); if (o >= 0) { H8[o] = v; if ((a >>> 24) === 3) try { window.__mirrorIw && window.__mirrorIw(a & 0x7fff); } catch (e) {} } };
        const rr8 = (a) => rom()[a - 0x08000000];
        const rr32 = (a) => { const R = rom(), o = a - 0x08000000; return (R[o] | R[o + 1] << 8 | R[o + 2] << 16 | R[o + 3] << 24) >>> 0; };
        const playerAddr = () => 0x03003C00 + 0x1AC * (r8(0x03003F59) & 1);
        const pos = (p) => [r16(p + 0xae), r16(p + 0xb2)];
        const inMoria = (menuOk) => { try { if (iwram < 0 || linked()) return false; if (menuOk) return true; if (inMenu()) return false; ew = findEw(); H8 = heap(); return ew >= 0 && r8(0x030041F8) === MORIA && r32(playerAddr()) >>> 24 === 2; } catch (e) { return false; } };
        // Items: 32-bit words (category bits 0-3, index 8-15, prefix 16-23, suffix 24-31). Category table at 0x08068F50, 0x28 bytes each.
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
        const slotOf = (f) => { for (let s = 0; s < 8; s++) if (f & (1 << (18 + s))) return s; return -1; };
        const empty = (it) => (it & 15) === 15;
        // Level an item needs (same sums as the game's own function at 0x0802D2F8); the hero may wear it up to its level + 1.
        const reqLevel = (it) => {
          const c = it & 15, i = (it >>> 8) & 255, pre = (it >>> 16) & 255, suf = it >>> 24, f = iflags(it);
          let r = rr8(catw(c, 0) + 12 * i + 2);
          if (f & 0x80) r += 5; if (f & 0x100) r += 5;
          if (pre !== 255 && c !== 7) { r += rr8(catw(c, 2) + 12 * pre + 2) >> 1; const pf = rr32(catw(c, 3) + 4 * pre); r += 5 * !!(pf & 1) + 5 * !!(pf & 2); }
          if (suf !== 255) { r += rr8(catw(c, 5) + 12 * suf + 2); const sf = rr32(catw(c, 6) + 4 * suf); r += 5 * !!(sf & 1) + 5 * !!(sf & 2); }
          if (f & 0x10000) r = 1;
          return r & 255;
        };
        // Gear this hero can wear in some slot (level not checked): returns the slot, or -1.
        const gearSlot = (P, it) => {
          if (empty(it) || (it & 15) === 7) return -1;
          const f = iflags(it); if (f & 0x10000) return -1;               // backpack-only item
          let hero = r8(P + 0x19F); if (hero === 6) hero = 0;
          if (hero >= 6 || !(f & (0x04000000 << hero))) return -1;        // this hero can't wear it
          const s = slotOf(f); if (s < 0) return -1;
          const wpn = r32(P + 0x40), sh = r32(P + 0x44);
          if (s === 2 && !empty(wpn) && (iflags(wpn) & 0x20000)) return -1;  // shield while holding a two-handed weapon
          if (s === 1 && (f & 0x20000) && !empty(sh)) return -1;             // two-handed weapon while holding a shield
          return s;
        };
        const packFull = (P) => { for (let k = 0; k < 8; k++) if (empty(r32(P + 0x5c + 4 * k))) return false; return true; };
        // Least valuable backpack item that may be thrown away for something better (runes and the like are kept).
        const cheapest = (P) => { let b = -1, bs = 1e9; for (let k = 0; k < 8; k++) { const it = r32(P + 0x5c + 4 * k); if (empty(it) || (it & 15) === 7) continue; const sc = score(it); if (sc < bs) { bs = sc; b = k; } } return [b, bs]; };
        const wanted = (P, it) => {
          const s = gearSlot(P, it); if (s < 0) return false;
          let best = empty(r32(P + 0x3c + 4 * s)) ? -1e9 : score(r32(P + 0x3c + 4 * s));
          for (let k = 0; k < 8; k++) { const b = r32(P + 0x5c + 4 * k); if (!empty(b) && slotOf(iflags(b)) === s) best = Math.max(best, score(b)); }
          const sc = score(it); if (sc <= best + 0.01) return false;
          return !packFull(P);                                              // never makes room by discarding
        };
        // Backpack gear that a better item of the same kind (worn, or in the backpack and wearable at this level) makes useless.
        // Jordan equips gear by hand, so Auto never equips; it only throws away the weaker copy.
        // Only a copy that Auto just picked up can push an older item out: the older backpack item of the same
        // kind that is weaker than the new one is thrown away. Worn gear and anything else are never touched.
        const toDiscard = (P) => {
          return -1;  // Jordan (2026-11-08): Auto never throws anything away.
          const lvl = r8(P + 0x19C) + 1;
          for (let k = 0; k < 8; k++) {
            const it = r32(P + 0x5c + 4 * k); if (noEquip.has(it) || fresh.has(it)) continue;
            const s = gearSlot(P, it); if (s < 0) continue;
            for (let j = 0; j < 8; j++) { if (j === k) continue; const b = r32(P + 0x5c + 4 * j);
              if (fresh.has(b) && gearSlot(P, b) === s && reqLevel(b) <= lvl && score(b) > score(it) + 0.01) return k; }
          }
          return -1;
        };
        const packNow = (P) => { const a = []; for (let k = 0; k < 8; k++) a.push(r32(P + 0x5c + 4 * k)); return a; };
        // After a discard exactly the chosen slot must be empty and every other slot unchanged; if not, the menu
        // cursor was somewhere else, so Auto stops discarding for this run instead of risking more items.
        const checkDrop = (P, before, k) => { const now = packNow(P);
          const ok = empty(now[k]) && now.every((x, j) => j === k || x === before[j]);
          if (!ok) { dropOff = true; slog("discard touched the wrong slot, Auto stops discarding"); } };
        // Menu macros: button taps sent while the game is in a menu. Backpack grid is 4 x 2 and the cursor starts on slot 0.
        const tapSteps = (id, n) => { const out = []; for (let i = 0; i < (n === undefined ? 1 : n); i++) out.push({ k: [id], ms: 160 }, { k: [], ms: 340 }); return out; };
        const gridSteps = (k) => [...tapSteps(7, k & 3), ...tapSteps(5, k >> 2)];
        const slog = (m) => { try { window.__slog && window.__slog("auto: " + m); } catch (e) {} };
        // Walls: the level's 8x8 collision cells (block map *0x0300206C, cell data *0x03002068); values 1 and 2 block.
        const buildGrid = () => {
          const W = r16(0x03005F90), Hh = r16(0x03005F88), bm = r32(0x0300206C), ct = r32(0x03002068);
          if (!W || !Hh || W > 512 || Hh > 512) return null;
          const bw = W >> 2, cell = new Uint8Array(W * Hh);
          for (let cy = 0; cy < Hh; cy++) for (let cx = 0; cx < W; cx++) {
            const b = r16(bm + 2 * ((cx >> 2) + (cy >> 2) * bw)) & 0xfff, v = r8(ct + (b << 4) + ((cx & 3) | ((cy & 3) << 2))) & 7;
            cell[cx + cy * W] = v === 1 || v === 2 ? 0 : 1;
          }
          const free = new Uint8Array(W * Hh);
          for (let cy = 1; cy < Hh - 1; cy++) for (let cx = 1; cx < W - 1; cx++) { const i = cx + cy * W; free[i] = cell[i] & cell[i - 1] & cell[i + 1]; }
          return { W, H: Hh, free };
        };
        const bfs = (x, y) => {
          const { W, H } = grid, now = performance.now(), prev = new Int32Array(W * H).fill(-2), q = new Int32Array(W * H);
          let free = grid.free;
          if (blocked.size) { free = free.slice(); for (const [c, t] of blocked) { if (t < now) blocked.delete(c); else free[c] = 0; } }
          let qh = 0, qt = 0; const s = (x >> 3) + (y >> 3) * W;
          prev[s] = -1; q[qt++] = s;
          if (!free[s]) for (let r = 1; r <= 3 && qt === 1; r++) for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
            const n = s + dx + dy * W; if (n >= 0 && n < W * H && free[n] && prev[n] === -2) { prev[n] = s; q[qt++] = n; }
          }
          const D = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];
          while (qh < qt) {
            const c = q[qh++], cx = c % W, cy = (c / W) | 0;
            for (const [dx, dy] of D) {
              const nx = cx + dx, ny = cy + dy; if (nx < 1 || ny < 1 || nx >= W - 1 || ny >= H - 1) continue;
              const n = nx + ny * W; if (prev[n] !== -2 || !free[n]) continue;
              if (dx && dy && !(free[cx + dx + cy * W] && free[cx + ny * W])) continue;
              prev[n] = c; q[qt++] = n;
            }
          }
          return prev;
        };
        const pathTo = (prev, tx, ty, r) => {
          const { W, H } = grid; let best = -1, bd = 1e9;
          for (let cy = (ty >> 3) - r; cy <= (ty >> 3) + r; cy++) for (let cx = (tx >> 3) - r; cx <= (tx >> 3) + r; cx++) {
            if (cx < 0 || cy < 0 || cx >= W || cy >= H) continue;
            const i = cx + cy * W; if (prev[i] === -2) continue;
            const d = Math.abs(cx * 8 + 4 - tx) + Math.abs(cy * 8 + 4 - ty); if (d < bd) { bd = d; best = i; }
          }
          if (best < 0) return null;
          const path = []; for (let c = best; c >= 0; c = prev[c]) { path.push(c); if (path.length > 20000) break; }
          return path.reverse();
        };
        const entities = () => {
          const out = []; let p = r32(playerAddr()), n = 0;
          while (p && n++ < 400) { const nx = r32(p); if (!nx || nx >>> 24 !== 2) break; p = nx; }
          n = 0; while (p && p >>> 24 === 2 && n++ < 400) { out.push(p); p = r32(p + 4); }
          return out;
        };
        // B picks up too (Jordan, 2026-11-08): with an item at the hero's feet, B works as R unless it can't be taken
        // (gear with a full backpack, a full Kingsfoil pouch); then B swings. Auto and P2 also pick up before swinging.
        const herbRoom = (P, t) => t === 17 ? (r8(P + 0x1AA) >> 4) < 10 : t === 18 ? (r8(P + 0x1AA) & 15) < 10 : true;
        // any = true: is there any item at the hero's feet (R no longer picks up, Jordan 2026-11-08).
        // What B does next to things (Jordan, 2026-11-08), the same for the player, Auto and P2: with a takeable item at
        // the feet (gear with backpack room, food when hurt, herbs with pouch room), an unopened chest (+0x85) or the
        // Spirit Shrine (player only) B works as R; otherwise B swings. rd = memory reader of that game, P = hero struct.
        // any = true: anything of the kind is there (R alone then does nothing).
        // range: how far from the feet an item counts (10 = where the game picks it up). The answer is the item's offset
        // from the hero ([dx, dy], [0, 0] for a chest or the Shrine), or false.
        const bAct = (rd, P, list, shrine, any, range = 10) => {
          const hero = rd.r32(P); if (hero >>> 24 !== 2) return false;
          const at = (p) => [rd.r16(p + 0xae), rd.r16(p + 0xb2)], [x, y] = at(hero);
          for (const p of list) {
            const u = rd.r32(p + 0x14);
            if (u === CHEST_UPD && !rd.r8(p + 0x85)) { const [bx, by] = at(p); if (bx - x >= -18 && bx - x <= 22 && Math.abs(by - y) <= 24) return [0, 0]; continue; }
            if (u === SHOP_UPD) { if (!shrine) continue; const [sx, sy] = at(p); if (Math.abs(sx - x) <= 30 && Math.abs(sy - y) <= 30) return [0, 0]; continue; }
            if (u !== ITEM_UPD || rd.r8(p + 0x63) !== 3) continue;
            const [ix, iy] = at(p); if (Math.abs(ix - x) > range || Math.abs(iy - y) > range) continue;
            const t = rd.r8(p + 0x60), off = [ix - x, iy - y];
            if (any && t >= 15) return off;
            const food = t === 15 || t === 16 || t === 19, hb = rd.r8(P + 0x1AA);
            const pack = () => { for (let k = 0; k < 8; k++) if ((rd.r32(P + 0x5c + 4 * k) & 15) === 15) return true; return false; };
            if (t >= 25 ? pack() : food ? rd.r16(P + 0x17C) < rd.r16(P + 0xD0) : t === 17 ? (hb >> 4) < 10 : t === 18 ? (hb & 15) < 10 : t >= 19) return off;
          }
          return false;
        };
        window.__bAct = bAct;
        window.__bPick = (any, range) => {
          try {
            if (iwram < 0 || inMenu()) return false;
            ew = findEw(); H8 = heap(); if (ew < 0) return false;
            return bAct({ r8, r16, r32 }, playerAddr(), entities(), true, any, range);
          } catch (e) { return false; }
        };
        // Some enemies are scenery standing inside the walls (no floor around them); those never fight and aren't counted.
        const onFloor = (p) => { const [ex, ey] = pos(p), { W, H, free } = grid, cx = ex >> 3, cy = ey >> 3;
          for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { const X = cx + dx, Y = cy + dy; if (X >= 0 && Y >= 0 && X < W && Y < H && free[X + Y * W]) return true; }
          return false; };
        const alive = (p) => !DEAD.has(r8(p + 0x62)) && r8(p + 0x63) !== 0x2f && !(r32(p + 0xe8) & 2);
        // Buttons (libretro ids): 0 B, 11 R, 4 up, 5 down, 6 left, 7 right.
        const setKeys = (ids) => {
          const want = new Set(ids);
          for (const id of keysDown) if (!want.has(id)) { try { emu.gameManager.simulateInput(0, id, 0); } catch (e) {} keysDown.delete(id); }
          for (const id of want) if (!keysDown.has(id)) { try { emu.gameManager.simulateInput(0, id, 1); } catch (e) {} keysDown.add(id); }
        };
        const steer = (x, y, tx, ty) => { const k = []; if (tx - x > 2) k.push(7); if (tx - x < -2) k.push(6); if (ty - y > 2) k.push(5); if (ty - y < -2) k.push(4); return k; };
        const show = (msg, ms) => { note.textContent = msg; note.hidden = false; clearTimeout(show.t); show.t = setTimeout(() => { note.hidden = true; }, ms || 2500); };
        const setHeal = (want) => {
          const P = playerAddr();
          if (want) { if (oldHeal === null) oldHeal = [r8(P + 0x19A) & 1, r8(0x03005820) & 0x10]; w8(P + 0x19A, r8(P + 0x19A) | 1); w8(0x03005820, r8(0x03005820) | 0x10); }
          else if (oldHeal) { if (!oldHeal[0]) w8(P + 0x19A, r8(P + 0x19A) & ~1); if (!oldHeal[1]) w8(0x03005820, r8(0x03005820) & ~0x10); oldHeal = null; }
        };
        const setOn = (v, msg) => {
          if (on === v) return; on = v;
          btn.classList.toggle("on", on); btn.setAttribute("aria-pressed", on ? "true" : "false");
          queue = []; setKeys([]); hist = []; stuck = 0; tries.clear(); blocked.clear(); skip.clear(); noEquip.clear(); shopDone = false; known = null; fresh.clear(); dropOff = false; macro = null; idleSince = unreachSince = 0; kills = 0;
          try { H8 = heap(); ew = findEw(); setHeal(on); } catch (e) {}
          if (msg) show(msg, 3500);
        };
        // Casting: put the skill on the R slot (+0x193), press L + R (the game's Quick Skill Select checks Spirit and
        // plays it), put the old skill back. The Spirit each skill used is remembered; a skill that used none is
        // skipped for a minute (passive, or it can't be used here).
        const skillCost = new Map(), noSkill = new Map();
        let castT = 0;
        const pickSkill = (P, now) => {
          const hero = r8(P + 0x19F), sp = r16(P + 0x17E), msp = r16(P + 0xD2) || 1;
          let best = -1, bc = -1;
          for (let s = 0; s < 6; s++) {
            if ((r8(P + 0x16A + s) << 24 >> 24) <= 0) continue;
            const key = hero * 8 + s; if ((noSkill.get(key) || 0) > now) continue;
            const cost = skillCost.has(key) ? skillCost.get(key) : Math.round(msp * 0.3);
            if (sp < cost) continue;
            if (cost > bc) { bc = cost; best = s; }
          }
          return best;
        };
        const castSteps = (P, s, face, now) => {
          const key = r8(P + 0x19F) * 8 + s; let old = 0, sp0 = 0;
          return [{ k: face, ms: 40 }, { k: [10], ms: 80, run: () => { w8(0x03005820, r8(0x03005820) | 8); w8(P + 0x19A, r8(P + 0x19A) | 2); old = r8(P + 0x193); sp0 = r16(P + 0x17E); w8(P + 0x193, s); } },
            { k: [10, 11], ms: 140 }, { k: [10], ms: 60 },
            { k: [], ms: 350, run: () => { if (r8(P + 0x193) === s) w8(P + 0x193, old); const d = sp0 - r16(P + 0x17E); if (d > 3) skillCost.set(key, d); else noSkill.set(key, now + 60000); casts[s] = (casts[s] || 0) + 1; } }];
        };
        let casts = {};
        const decide = (now) => {
          const P = playerAddr(), hero = r32(P), hp = r16(P + 0x17C), mhp = r16(P + 0xD0);
          { const pk = packNow(P); if (!known) known = new Set(pk); for (const it of pk) if (!empty(it) && !known.has(it)) { known.add(it); fresh.add(it); } }
          if (!hero || !hp || hp > 5000) { setKeys([]); return; }                  // knocked out or loading
          if (!grid || now - gridT > 2000) { grid = buildGrid(); gridT = now; if (!grid) return; }
          const [x, y] = pos(hero), list = entities();
          if (list.length < 6) { setKeys([]); return; }                           // level still setting up
          const en = [], items = [], trig = [], boxes = [], shops = [];
          for (const [p, t] of skip) if (t < now) skip.delete(p);
          for (const p of list) {
            const u = r32(p + 0x14);
            if (skip.has(p)) continue;
            if (u === ENEMY_UPD) { if (alive(p) && onFloor(p)) en.push(p); }
            else if (u === ITEM_UPD) { if (r8(p + 0x63) === 3) items.push(p); }
            else if (u === TRIG_UPD && r8(p + 0x63) === 0) trig.push(p);
            else if (u === POT_UPD && r8(p + 0x63) === 0 && onFloor(p)) boxes.push(p);
            else if (u === CHEST_UPD && r8(p + 0x85) === 0 && onFloor(p)) boxes.push(p);    // +0x85 stays 1 once opened
            else if (u === SHOP_UPD && r8(p + 0x60) === 2) shops.push(p);
          }
          if (en.length < lastSeen) kills += lastSeen - en.length; lastSeen = en.length;
          const prev = bfs(x, y);
          const near = (p, d) => { const [ex, ey] = pos(p); return Math.abs(ex - x) + Math.abs(ey - y) < d; };
          // Elite enemies (Jordan, 2026-11-08): the stronger version of an enemy has an even tier byte (+0x60; e.g.
          // tier 2 orc 72 HP next to tier 1 orc 19 HP) or lots of HP (+0x5A); Auto hits and walks to those first.
          const elite = (p) => (r8(p + 0x60) & 1) === 0 || (r16(p + 0x5A) << 16 >> 16) >= 40;
          let tgt = null;
          for (const p of [...en].sort((a, b) => elite(b) - elite(a))) { const [ex, ey] = pos(p); if (Math.abs(ex - x) <= 22 && Math.abs(ey - y) <= 16) { tgt = { kind: "hit", p }; break; } }
          // Picking up beats swinging (Jordan, 2026-11-08): an item at the hero's feet is taken first, unless there's no
          // room for it (then Auto swings).
          for (const p of items) {
            if ((tries.get(p) || 0) > 6) continue;
            const [ix, iy] = pos(p); if (Math.abs(ix - x) > 8 || Math.abs(iy - y) > 8) continue;
            const t = r8(p + 0x60);
            const ok = t === 15 || t === 16 || t === 19 ? hp < mhp : t >= 25 ? !packFull(P) && wanted(P, r32(p + 0x88)) : t >= 17 && t <= 24 ? herbRoom(P, t) : false;
            if (ok) { tgt = { kind: "pick", p, gear: t >= 25 }; break; }
          }
          const close = en.some((p) => near(p, 70)), low = hp * 10 < mhp * 4;
          // Taking damage = HP went down in the last 3 seconds: then Auto fights and only goes for food that heals.
          if (hp < lastHp) hurtAt = now; lastHp = hp;
          const hurt = now - hurtAt < 3000, fighting = hurt && close;
          const gems = r16(P + 0x184), herbs = r8(P + 0x1AA) >> 4;
          if (!tgt && !close) {
            // Throw away weaker copies (Start, pick it, Discard). Gear is equipped by the player, never by Auto.
            const k = toDiscard(P);
            if (k >= 0) {
              const it = r32(P + 0x5c + 4 * k);
              macro = "discard"; slog("discard weaker " + (it >>> 0).toString(16));
              const before = packNow(P);
              queue = [...tapSteps(3), { k: [], ms: 900 }, ...gridSteps(k), ...tapSteps(8), { k: [], ms: 250 }, ...tapSteps(5), ...tapSteps(8), { k: [], ms: 500 },
                { k: [], ms: 10, run: () => { if (r32(P + 0x5c + 4 * k) === it) { noEquip.add(it); slog("discard failed"); } else checkDrop(P, before, k); } }, ...tapSteps(0), { k: [], ms: 500, end: true }];
              return;
            }
          }
          // Herbs and food (Jordan, 2026-11-08). Ground item types (+0x60, name text 568 + type): 15 fruit, 16 mushrooms,
          // 19 lembas bread are eaten at once (heal); 17/18 dried/fresh Kingsfoil and 20-24 Shire/Elven/Mirkwood/Rivendell/
          // Lothlorien herbs go to the herb pouch. Food is eaten whenever the hero is hurt; while taking damage only food is
          // picked up, and only when it's close or HP is low. Gear only when nothing is fighting the hero.
          if (now - itemTriesT > 20000) { itemTriesT = now; for (const p of items) tries.delete(p); }  // give items another go
          if (!tgt || low) {
            const food = (t) => t === 15 || t === 16 || t === 19, herb = (t) => t === 17 || t === 18 || (t >= 20 && t <= 24);
            let best = null;
            for (const p of items) {
              if ((tries.get(p) || 0) > 6) continue;
              const t = r8(p + 0x60);
              let ok, maxLen = 60;
              if (food(t)) { ok = hp < mhp && (!fighting || low); if (fighting) maxLen = low ? 25 : 12; }
              else if (herb(t)) ok = !fighting;
              else ok = t >= 25 && !close && !hurt && wanted(P, r32(p + 0x88));
              if (!ok) continue;
              const [ix, iy] = pos(p);
              if (Math.abs(ix - x) <= 8 && Math.abs(iy - y) <= 8) { best = { kind: "pick", p, gear: t >= 25 }; break; }
              const path = pathTo(prev, ix, iy, 1);
              if (path && path.length < maxLen && (!best || path.length < best.len)) best = { kind: "go", p, len: path.length, path, item: true };
            }
            if (best && (!tgt || best.kind === "pick" || best.len < 12)) tgt = best;   // low HP: food next to the hero beats hitting
          }
          // Pots, barrels and chests: smash or open the ones next to the hero, walk to near ones when no enemy is close.
          if (!tgt && !close) for (const p of boxes) {
            const [bx, by] = pos(p), chest = r32(p + 0x14) === CHEST_UPD;
            if (chest) {
              // A chest opens with R alone (no direction held) from anywhere close: about 20 px left/right of it and 24 px above/below.
              if (bx - x >= -18 && bx - x <= 22 && Math.abs(by - y) <= 24) { tgt = { kind: "open", p }; break; }
            } else if (Math.abs(bx - x) <= 22 && Math.abs(by - y) <= 18) { tgt = { kind: "smash", p }; break; }
          }
          const goBox = (maxLen) => { for (const p of boxes) { const [bx, by] = pos(p); const path = pathTo(prev, bx, by, 2); if (path && path.length < maxLen && (!tgt || path.length < tgt.len)) tgt = { kind: "go", p, len: path.length, path }; } };
          if (!tgt && !close) goBox(40);
          // The Shrine is only in the entity list while the hero is near it, so its spot is remembered (Moria's is at 1385,1214).
          for (const p of shops) shrineAt = pos(p);
          const shopGo = (force) => { if (!shopDone && herbs < 10 && gems >= 50 && now - shopT > 90000) {
            const [sx, sy] = shrineAt;
            if (Math.abs(sx - x) <= shopNear && Math.abs(sy - y) <= shopNear) { if (shops.length) tgt = { kind: "shop", p: shops[0] }; return; }
            const path = pathTo(prev, sx, sy, shopNear < 30 ? 1 : 3); if (!path && now - lastLog > 20000) { lastLog = now; slog("no path to shrine from " + x + "," + y); } if (path && (force || !tgt || path.length < tgt.len)) tgt = { kind: "go", p: "shrine", len: path.length, path };
          } };
          // Low on herbs, or passing close by: go restock first (pots and far enemies wait).
          if (!close && !skip.has("shrine")) {
            const near = Math.abs(shrineAt[0] - x) + Math.abs(shrineAt[1] - y) < 400;
            if (!tgt || tgt.kind === "go") { if (herbs <= 2 || near) shopGo(true); }
          }                       // low on herbs: restock before going on
          // Walk to the nearest enemy, counting an elite as 40 steps nearer than it is.
          if (!tgt) { let bs = 1e9; for (const p of en) { const [ex, ey] = pos(p); const path = pathTo(prev, ex, ey, 2); if (!path) continue; const sc = path.length - (elite(p) ? 40 : 0); if (sc < bs) { bs = sc; tgt = { kind: "go", p, len: path.length, path }; } } }
          if (!tgt) goBox(1e9);
          // Spirit Shrine: buy herbs until the hero carries 10 or the gems run out.
          if (!tgt) shopGo();
          if (!tgt) for (const p of trig) { const [tx, ty] = pos(p); const path = pathTo(prev, tx, ty, 3); if (path && (!tgt || path.length < tgt.len)) tgt = { kind: "go", p, len: path.length, path }; }
          if (!tgt) {
            setKeys([]);
            if (!en.length) { if (!idleSince) idleSince = now; else if (now - idleSince > 3000) { slog("done, kills " + kills); setOn(false, "Auto off: every enemy is gone."); } }
            else { if (!unreachSince) unreachSince = now; else if (now - unreachSince > 20000) setOn(false, "Auto off: can't reach the last " + en.length + " enemies."); }
            queue = [{ k: [], ms: 200 }];
            return;
          }
          idleSince = unreachSince = 0;
          if (tgt.kind === "hit") {
            const [ex, ey] = pos(tgt.p);
            // Skills (Jordan, 2026-11-08): against an elite or two or more enemies close by, cast a learned active
            // skill when there's Spirit for it (Spirit +0x17E, max +0xD2), the dearest one first.
            const group = en.filter((p) => near(p, 56)).length >= 2;
            const sk = (elite(tgt.p) || group) && now - castT > 1200 ? pickSkill(P, now) : -1;
            if (sk >= 0) { castT = now; queue = castSteps(P, sk, steer(x, y, ex, ey), now); return; }
            const bk = bAct({ r8, r16, r32 }, P, list, false) ? 11 : 0;   // Auto's B works like the player's B
            queue = [{ k: steer(x, y, ex, ey), ms: 40 }, { k: [bk], ms: 70 }, { k: [], ms: 70 }];
          } else if (tgt.kind === "pick") {
            tries.set(tgt.p, (tries.get(tgt.p) || 0) + 1);
            { const t = r8(tgt.p + 0x60); picks[t] = (picks[t] || 0) + 1; }
            if (tgt.gear && packFull(P)) {
              // No room: throw away the least valuable backpack item first (Start, pick it, Discard).
              const k = -1;  // never discard to make room (Jordan, 2026-11-08)
              if (k >= 0) {
                const before = packNow(P);
                macro = "discard"; slog("discard " + (r32(P + 0x5c + 4 * k) >>> 0).toString(16) + " for " + (r32(tgt.p + 0x88) >>> 0).toString(16));
                queue = [...tapSteps(3), { k: [], ms: 900 }, ...gridSteps(k), ...tapSteps(8), { k: [], ms: 250 }, ...tapSteps(5), ...tapSteps(8), { k: [], ms: 500 }, { k: [], ms: 10, run: () => checkDrop(P, before, k) }, ...tapSteps(0), { k: [], ms: 500, end: true }];
                return;
              }
            }
            queue = [{ k: [11], ms: 60 }, { k: [], ms: 90 }];
          } else if (tgt.kind === "open") {
            const n = (tries.get(tgt.p) || 0) + 1; tries.set(tgt.p, n);
            if (n > 10) { skip.set(tgt.p, now + 60000); slog("chest gave up at " + x + "," + y + " (chest " + pos(tgt.p).join(",") + ")"); }
            const p = tgt.p;
            queue = [{ k: [], ms: 200 }, { k: [11], ms: 120 }, { k: [], ms: 400 }, { k: [], ms: 10, run: () => { if (r8(p + 0x85)) slog("chest opened"); } }];
          } else if (tgt.kind === "smash") {
            const n = (tries.get(tgt.p) || 0) + 1; tries.set(tgt.p, n);
            if (n > 14) { skip.set(tgt.p, now + 60000); slog("smash gave up at " + x + "," + y); }
            const [bx, by] = pos(tgt.p);
            queue = [{ k: steer(x, y, bx, by), ms: 50 }, { k: [...steer(x, y, bx, by), 0], ms: 80 }, { k: [], ms: 120 }];
          } else if (tgt.kind === "shop") {
            shopT = now; macro = "shop";
            const g0 = gems;
            // R opens the shop, Left moves to the herb tab, A then A (Yes) buys one; repeat until the gems stop going down.
            // Buying goes on only while the herb count goes up, so nothing else gets bought.
            const buy = () => { const before = r8(P + 0x1AA) >> 4; return [...tapSteps(8), { k: [], ms: 200 }, ...tapSteps(8), { k: [], ms: 400 },
              { k: [], ms: 10, run: () => { const h = r8(P + 0x1AA) >> 4; if (h > before && h < 10 && r16(P + 0x184) >= 50) queue.unshift(...buy()); } }]; };
            // If R didn't open the shop (game state 20), stop here and walk right up to the Shrine before trying again.
            const opened = { k: [], ms: 10, run: () => { if ((r32(0x030041B0) & 255) !== 20) { shopT = 0; shopNear = 10; slog("shrine didn't open at " + x + "," + y); queue = [{ k: [], ms: 10, end: true }]; } } };
            queue = [...tapSteps(11), { k: [], ms: 900 }, opened, ...tapSteps(6), { k: [], ms: 300 }, ...buy(), ...tapSteps(0), { k: [], ms: 400 }, ...tapSteps(0), { k: [], ms: 600 },
              { k: [], ms: 10, run: () => { shopNear = 30; if (r16(P + 0x184) < g0) shopDone = true; slog("shrine: spent " + (g0 - r16(P + 0x184)) + " gems, herbs " + (r8(P + 0x1AA) >> 4)); } }, { k: [], ms: 10, end: true }];
          } else {
            const W = grid.W, c = tgt.path[Math.min(3, tgt.path.length - 1)], k = steer(x, y, (c % W) * 8 + 4, ((c / W) | 0) * 8 + 4);
            hist.push([x, y, now]); while (hist.length && now - hist[0][2] > 600) hist.shift();
            if (hist.length > 4 && Math.abs(hist[0][0] - x) + Math.abs(hist[0][1] - y) < 4) {
              stuck++; hist = [];
              // Stuck on the same target again and again: leave it for a while and do something else.
              const n = (tries.get("s" + tgt.p) || 0) + 1; tries.set("s" + tgt.p, n);
              if (n >= 5) { skip.set(tgt.p, now + 30000); tries.delete("s" + tgt.p); if (now - lastLog > 5000) { lastLog = now; slog("stuck at " + x + "," + y + " going to " + (typeof tgt.p === "string" ? tgt.p : pos(tgt.p).join(",")) + ", skipping it for 30 s"); } }
              if (tgt.item) tries.set(tgt.p, (tries.get(tgt.p) || 0) + 1);
              // Mark the cells ahead as blocked for 15 s (a statue or other object the wall map doesn't know about), so the path goes around.
              const here = (x >> 3) + (y >> 3) * W;
              for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const b = c + dx + dy * W; if (b !== here && b >= 0) blocked.set(b, now + 15000); }
              // Something is in the way (often a pot): swing at it, and now and then step aside.
              queue = stuck % 3 ? [{ k, ms: 40 }, { k: [0], ms: 70 }, { k: [], ms: 70 }] : [{ k: [[4], [5], [6], [7]][(Math.random() * 4) | 0], ms: 170 }];
            } else queue = [{ k, ms: 70 }];
          }
        };
        const loop = () => {
          // While a menu macro runs the game is in its menu (the level number reads 0 there), so only the macro keeps going.
          const ok = inMoria(!!macro && on);
          btn.hidden = !ok && !macro;
          if (!ok) { if (on) { queue = []; macro = null; setKeys([]); } return; }
          if (!on) return;
          const now = performance.now();
          if (now < userUntil) { queue = []; macro = null; setKeys([]); return; }
          if (now < qUntil) return;
          try { if (!queue.length) { macro = null; decide(now); } } catch (e) { queue = []; setKeys([]); return; }
          const step = queue.shift(); if (!step) return;
          if (step.run) { try { step.run(); } catch (e) {} }
          if (step.end) macro = null;
          setKeys(step.k); qUntil = now + step.ms;
        };
        setInterval(loop, 16);
        window.__autoTick = () => { if (document.visibilityState === "hidden") loop(); };
        btn.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); setOn(!on, on ? "" : "Auto on"); });
        btn.addEventListener("click", (e) => e.preventDefault());
        window.addEventListener("keydown", (e) => { if ((e.key === "o" || e.key === "O") && !e.repeat && !btn.hidden) setOn(!on, on ? "" : "Auto on"); });
        // Touching the controls pauses auto for a moment so the player can take over.
        $("pad").addEventListener("pointerdown", () => { if (on) userUntil = performance.now() + 1500; }, true);
        window.__auto = { get on() { return on; }, set: setOn, kills: () => kills, picks: () => picks, casts: () => casts, costs: () => [...skillCost], get macro() { return macro; } };
      })();
      // Fast-forward through level setup (tools/fastloads.py sets EWRAM 0x0203FFF1 while the screen is black).
      // mGBA keeps IWRAM right after the 256 KB of EWRAM, so EWRAM starts 0x40000 before IWRAM in memory.
      // Never longer than 4 seconds per load, in case the byte is ever left set.
      let ffOn = false, ffFlag = false, ffSince = 0;
      setInterval(() => {
        let flag = false;
        try { if (iwram >= 0x40000) flag = emu.Module.HEAPU8[iwram - 0x40000 + 0x3FFF1] !== 0; } catch (e) {}
        if (flag && !ffFlag) ffSince = performance.now();
        ffFlag = flag;
        const want = flag && performance.now() - ffSince < 4000;
        if (want !== ffOn) { ffOn = want; try { emu.gameManager.setFastForwardRatio(8); emu.gameManager.toggleFastForward(want ? 1 : 0); } catch (e) {} }
      }, 16);
      // In the game's Skills tab (state 0x0F) the Skills button takes a point back instead (Jordan, 2026-11-06): it presses
      // L + Select together for a moment, which the Modded game reads as "refund the skill under the cursor" (tools/skillrefund.py).
      // C on the keyboard does the same. Everywhere else the button is the Quick Skill toggle as before.
      const inSkillsTab = () => !window.__forcePlay && gameState() === 0x0F;
      let refundT = null;
      const refundPulse = () => {
        if (refundT) return;
        try { emu.gameManager.simulateInput(0, 10, 1); emu.gameManager.simulateInput(0, 2, 1); } catch (e) {}
        $("qsBtn").classList.add("on");
        refundT = setTimeout(() => {
          refundT = null;
          try { emu.gameManager.simulateInput(0, 2, 0); } catch (e) {}
          sendL(); $("qsBtn").classList.toggle("on", qsOn);
        }, 140);
      };
      window.addEventListener("keydown", (e) => { if ((e.key === "c" || e.key === "C") && !e.repeat && inSkillsTab()) { e.preventDefault(); refundPulse(); } });
      $("qsBtn").addEventListener("pointerdown", (e) => { e.preventDefault(); if (inSkillsTab()) { refundPulse(); return; } qsOn = !qsOn; $("qsBtn").classList.toggle("on", qsOn); qsSync(); });
      document.querySelectorAll("#pad .btn[data-in]").forEach((el) => {
        const id = +el.dataset.in;
        // L and R are never swapped (Jordan undid the in-play swap, 2026-11-06).
        const press = (on) => {
          if (id === 0 && on && !inMenu() && window.__stepPick && window.__stepPick()) { el.__bAs = -1; return; }
          if (id === 0 && el.__bAs === -1) { if (!on) el.__bAs = 0; return; }
          el.classList.toggle("on", !!on);
          if (id === 10) {
            // The skill on the game's B slot is cast with L (Jordan, 2026-11-08): L, then B for a moment (the game's own
            // L + B Quick Skill), so the game checks Spirit and plays it. Without a skill there, L is just L.
            lTouch = !!on; sendL();
            const sk = skIcons[1];
            if (on && !lCast && sk && sk.classList.contains("show") && !inMenu()) {
              lCast = true; sendL(); skillPressed(el, sk.__v);
              setTimeout(() => { try { emu.gameManager.simulateInput(0, 0, 1); } catch (e) {} }, 60);
              setTimeout(() => { try { emu.gameManager.simulateInput(0, 0, 0); } catch (e) {} }, 200);
              setTimeout(() => { lCast = false; sendL(); }, 240);
            }
            return;
          }
          // B also picks up (Jordan, 2026-11-08): with an item at the hero's feet that can be taken, B works as R. B never
          // casts (its skill is on L), so L is let go while B is down even with Quick Skill on.
          let sid = id;
          // R no longer picks up or opens chests and the Shrine (Jordan, 2026-11-08; B does): next to any of those, R alone
          // does nothing. With L held (Quick Skill) R still casts its skill.
          if (id === 11) {
            if (on) el.__rBlock = !(qsHeld || lTouch || lCast) && !!(window.__bPick && window.__bPick(true));
            if (el.__rBlock) { if (!on) el.__rBlock = false; return; }
          }
          if (id === 0) {
            if (on) { el.__bAs = window.__bPick && window.__bPick() ? 11 : 0; if (qsHeld || lTouch) { bNoL = true; sendL(); } }
            sid = el.__bAs || 0;
            if (!on && bNoL) { try { emu.gameManager.simulateInput(0, sid, 0); } catch (e) {} setTimeout(() => { bNoL = false; sendL(); }, 50); return; }
            if (on && bNoL) { setTimeout(() => { try { emu.gameManager.simulateInput(0, sid, 1); } catch (e) {} }, 40); return; }
          }
          try { emu.gameManager.simulateInput(0, sid, on); } catch (e) {}
        };
        // Only the finger that pressed a button can let it go, so a stick drag passing over it never touches it.
        let bp = null;
        el.__release = () => { bp = null; press(0); };
        el.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); if (pid !== null && e.pointerId === pid) return; bp = e.pointerId; try { el.setPointerCapture(e.pointerId); } catch (x) {} press(1); });
        const rel = (e) => { if (bp !== null && e.pointerId === bp) el.__release(); };
        el.addEventListener("lostpointercapture", rel);
        window.addEventListener("pointerup", rel, true); window.addEventListener("pointercancel", rel, true);
      });
      // Lift the black cover once the game is past the white power-on screen (about 70 frames).
      const lift = setInterval(() => { const f = frames(); if (f > 75) { $("bootCover").classList.add("gone"); clearInterval(lift); } }, 100);
      setTimeout(() => { $("bootCover").classList.add("gone"); clearInterval(lift); }, 8000);
      // Watchdog: if no frames run, ask for a tap; only restart if a tap does not get it going.

      // Longer pickup reach (Jordan, 2026-11-08): B with a takeable item a little beyond the feet (up to PICK_REACH
      // pixels) walks the hero the last few steps to it and picks it up. Moving the stick stops it. True = B was used.
      const PICK_REACH = 22;
      window.__stepPick = () => {
        if (stepping || !window.__bPick || window.__bPick()) return false;
        const v0 = window.__bPick(false, PICK_REACH); if (!v0) return false;
        stepping = true; const sec0 = sector; let n = 0;
        const gi = (k, on) => { try { emu.gameManager.simulateInput(0, k, on); } catch (e) {} };
        const restore = () => [4, 5, 6, 7].forEach((k) => gi(k, held[k]));
        const L0 = qsHeld || lTouch; if (L0) { bNoL = true; sendL(); }
        const done = (pick) => {
          restore();
          // The hero settles for a moment before R, or the game can miss it.
          if (pick) { setTimeout(() => gi(11, 1), 70); setTimeout(() => gi(11, 0), 220); }
          setTimeout(() => { stepping = false; if (bNoL) { bNoL = false; sendL(); } }, pick ? 270 : 0);
        };
        const tick = () => {
          if (sector !== sec0 || inMenu()) { done(false); return; }
          const v = window.__bPick(false, PICK_REACH + 4);
          if (!v) { done(false); return; }
          if ((Math.abs(v[0]) <= 5 && Math.abs(v[1]) <= 5) || n++ > 20) { done(true); return; }
          const on = []; if (v[0] > 2) on.push(7); if (v[0] < -2) on.push(6); if (v[1] > 2) on.push(5); if (v[1] < -2) on.push(4);
          [4, 5, 6, 7].forEach((k) => gi(k, on.includes(k) ? 1 : 0));
          setTimeout(tick, 33);
        };
        tick(); return true;

        // What B does next to things (Jordan, 2026-11-08), the same for the player, Auto and P2: with a takeable item at
        // the feet (gear with backpack room, food when hurt, herbs with pouch room), an unopened chest (+0x85) or the
        // Spirit Shrine (player only) B works as R; otherwise B swings. rd = memory reader of that game, P = hero struct.
        // any = true: anything of the kind is there (R alone then does nothing).
        // range: how far from the feet an item counts (10 = where the game picks it up). The answer is the item's offset
        // from the hero ([dx, dy], [0, 0] for a chest or the Shrine), or false.
        const bAct = (rd, P, list, shrine, any, range = 10) => {
          const hero = rd.r32(P); if (hero >>> 24 !== 2) return false;
          const at = (p) => [rd.r16(p + 0xae), rd.r16(p + 0xb2)], [x, y] = at(hero);
          for (const p of list) {
            const u = rd.r32(p + 0x14);
            if (u === CHEST_UPD && !rd.r8(p + 0x85)) { const [bx, by] = at(p); if (bx - x >= -18 && bx - x <= 22 && Math.abs(by - y) <= 24) return [0, 0]; continue; }
            if (u === SHOP_UPD) { if (!shrine) continue; const [sx, sy] = at(p); if (Math.abs(sx - x) <= 30 && Math.abs(sy - y) <= 30) return [0, 0]; continue; }
            if (u !== ITEM_UPD || rd.r8(p + 0x63) !== 3) continue;
            const [ix, iy] = at(p); if (Math.abs(ix - x) > range || Math.abs(iy - y) > range) continue;
            const t = rd.r8(p + 0x60), off = [ix - x, iy - y];
            if (any && t >= 15) return off;
            const food = t === 15 || t === 16 || t === 19, hb = rd.r8(P + 0x1AA);
            const pack = () => { for (let k = 0; k < 8; k++) if ((rd.r32(P + 0x5c + 4 * k) & 15) === 15) return true; return false; };
            if (t >= 25 ? pack() : food ? rd.r16(P + 0x17C) < rd.r16(P + 0xD0) : t === 17 ? (hb >> 4) < 10 : t === 18 ? (hb & 15) < 10 : t >= 19) return off;
          }
          return false;
        };
        window.__bAct = bAct;
        window.__bPick = (any, range) => {
          try {
            if (iwram < 0 || inMenu()) return false;
            ew = findEw(); H8 = heap(); if (ew < 0) return false;
            return bAct({ r8, r16, r32 }, playerAddr(), entities(), true, any, range);
          } catch (e) { return false; }
        };
