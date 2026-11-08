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
        let hist = [], stuck = 0, tries = new Map(), blocked = new Map(), skip = new Map(), macro = null, noEquip = new Set(), shrineAt = [1385, 1214], shopT = 0, shopNear = 30, shopDone = false, known = null, fresh = new Set(), dropOff = false, lastLog = 0, idleSince = 0, unreachSince = 0, userUntil = 0, oldHeal = null, lastSeen = 0, kills = 0;
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
        const w8 = (a, v) => { const o = at(a); if (o >= 0) H8[o] = v; };
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
          if (!packFull(P)) return true;
          const [k, ks] = cheapest(P); return k >= 0 && ks < sc;            // room can be made
        };
        // Backpack gear that a better item of the same kind (worn, or in the backpack and wearable at this level) makes useless.
        // Jordan equips gear by hand, so Auto never equips; it only throws away the weaker copy.
        // Only a copy that Auto just picked up can push an older item out: the older backpack item of the same
        // kind that is weaker than the new one is thrown away. Worn gear and anything else are never touched.
        const toDiscard = (P) => {
          if (dropOff) return -1;
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
          let tgt = null;
          for (const p of en) { const [ex, ey] = pos(p); if (Math.abs(ex - x) <= 22 && Math.abs(ey - y) <= 16) { tgt = { kind: "hit", p }; break; } }
          const close = en.some((p) => near(p, 70)), low = hp * 10 < mhp * 4;
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
          if (!tgt && (!close || low)) {
            for (const p of items) {
              if ((tries.get(p) || 0) > 6) continue;
              const t = r8(p + 0x60);
              const ok = (t >= 15 && t <= 24) || (t >= 25 && !close && wanted(P, r32(p + 0x88)));
              if (!ok) continue;
              const [ix, iy] = pos(p);
              if (Math.abs(ix - x) <= 8 && Math.abs(iy - y) <= 8) { tgt = { kind: "pick", p, gear: t >= 25 }; break; }
              const path = pathTo(prev, ix, iy, 1);
              if (path && path.length < 60 && (!tgt || path.length < tgt.len)) tgt = { kind: "go", p, len: path.length, path, item: true };
            }
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
          if (!tgt) for (const p of en) { const [ex, ey] = pos(p); const path = pathTo(prev, ex, ey, 2); if (path && (!tgt || path.length < tgt.len)) tgt = { kind: "go", p, len: path.length, path }; }
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
            queue = [{ k: steer(x, y, ex, ey), ms: 40 }, { k: [0], ms: 70 }, { k: [], ms: 70 }];
          } else if (tgt.kind === "pick") {
            tries.set(tgt.p, (tries.get(tgt.p) || 0) + 1);
            if (tgt.gear && packFull(P)) {
              // No room: throw away the least valuable backpack item first (Start, pick it, Discard).
              const [k] = dropOff ? [-1] : cheapest(P);
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
        window.__auto = { get on() { return on; }, set: setOn, kills: () => kills };
      })();