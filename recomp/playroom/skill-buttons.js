// Play Room v110: skills always on (L held in play), skill buttons (icons inside, grey without Spirit, black when used,
// countdown), B's skill on L, Undo button (skill points, sold or thrown-away items), B rules shared by player, Auto and P2.
      // Skills are always on now (Jordan, 2026-11-08): the Skills button became Undo, and Quick Skill Select is gone from the
      // game's Options menu. While Auto plays it presses L itself, so the page lets go of L then.
      let qsOn = true, qsHeld = false, lTouch = false, lCast = false, bNoL = false, stepping = false;
      // L is held while Quick Skill is on, while the L button is down, or while L casts B's skill; never while B is pressed
      // (B always swings or picks up, Jordan 2026-11-08).
      const sendL = () => { try { emu.gameManager.simulateInput(0, 10, (qsHeld || lTouch || lCast) && !bNoL ? 1 : 0); } catch (e) {} };
      const qsOption = () => { if (emu.gameManager.mpQs) { emu.gameManager.mpQs(); return; } try { const h = emu.Module.HEAPU8; if (iwram < 0) return; h[iwram + 0x5820] |= 8; h[iwram + 0x3D9A] |= 2; h[iwram + 0x3F46] |= 2; [0x5820, 0x3D9A, 0x3F46].forEach((o) => { try { window.__mirrorIw && window.__mirrorIw(o); } catch (e) {} }); } catch (e) {} };
      const qsSync = () => { const want = qsOn && !inMenu() && !(window.__auto && window.__auto.on); if (want && iwram >= 0) qsOption(); if (want !== qsHeld) { qsHeld = want; sendL(); } };
      setInterval(qsSync, 100);
      // Skill icons under A, B and R (Jordan, 2026-11-07). In play, read the local hero's Quick Skill Select slots:
      // local player 0x03003F59, hero struct 0x03003C00 + 0x1AC * player, hero id +0x19F, slots +0x191 (A) +0x192 (B)
      // +0x193 (R), active skill levels +0x16A. A slot shows only once its skill has been learned.
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
        let sp = -1; try { const h = emu.Module.HEAPU8, P = heroPtr(); sp = h[P + 0x17E] | h[P + 0x17F] << 8; } catch (e) {}
        const short = (v) => { if (!v || sp < 0 || !window.__skCost) return false; const c = window.__skCost(v[1]); return c > 0 && sp < c; };
        skIcons.forEach((el, k) => { const v = st && st[k]; el.parentElement.classList.toggle("nosp", short(v)); });
        xBtns.forEach((b, k) => b.classList.toggle("nosp", short(xList[k])));
        skIcons.forEach((el, k) => {
          const v = st && st[k], key = v ? v.join(",") : "";
          if (el.__k === key) return; el.__k = key; el.__v = v; el.classList.toggle("show", !!v); el.parentElement.classList.toggle("has-sk", !!v);
          if (v) el.style.backgroundPosition = skPos(v);
        });
        document.body.classList.toggle("qs-on", qsOn);
        updateExtras();
      }, 250);
      // Undo (Jordan, 2026-11-08; was the Skills toggle). In the Skills tab it takes a skill point back as before. In any other
      // menu it brings back the last item sold or thrown away there (a sale also takes its gems back). Once the menu is
      // closed (back in play), those can't be undone any more. The page watches the hero's 8 worn + 8 backpack slots and
      // gems while a menu is open: an item that leaves the hero (not just moved or worn) is remembered, with the gems that
      // came in at the same moment. A brought-back item goes into the backpack (into its own slot when it was there).
      let undoList = [], undoSnap = null;
      const u32 = (h, o) => (h[o] | h[o + 1] << 8 | h[o + 2] << 16 | h[o + 3] << 24) >>> 0;
      const undoRead = () => { const h = emu.Module.HEAPU8, P = heroPtr(), it = []; for (let k = 0; k < 16; k++) it.push(u32(h, P + 0x3C + 4 * k)); return { P, it, gems: h[P + 0x184] | h[P + 0x185] << 8 }; };
      const undoNote = (msg) => { const n = $("saveNote"); if (!n) return; n.textContent = msg; n.hidden = false; clearTimeout(undoNote.t); undoNote.t = setTimeout(() => { n.hidden = true; }, 2200); };
      setInterval(() => {
        if (iwram < 0 || linked()) { undoList = []; undoSnap = null; return; }
        const st = gameState();
        if (st === 1 || st === 5 || st === 2 || st === 3) { undoList = []; undoSnap = null; $("qsBtn").classList.remove("can"); return; }
        let cur; try { cur = undoRead(); } catch (e) { return; }
        if (undoSnap && undoSnap.P === cur.P) {
          const left = cur.it.slice(), gone = [];
          undoSnap.it.forEach((w, k) => { if ((w & 15) === 15) return; const j = left.indexOf(w); if (j >= 0) left[j] = -1; else gone.push([k, w]); });
          const g = cur.gems - undoSnap.gems;
          gone.forEach(([k, w], i) => undoList.push({ k, w, gems: i === 0 && g > 0 ? g : 0 }));
          if (undoList.length > 20) undoList.shift();
        }
        undoSnap = cur;
        $("qsBtn").classList.toggle("can", undoList.length > 0 || inSkillsTab());
      }, 60);
      const undoItem = () => {
        const u = undoList[undoList.length - 1]; if (!u) return false;
        const h = emu.Module.HEAPU8, P = heroPtr();
        let at = u.k >= 8 ? P + 0x3C + 4 * u.k : -1;
        if (at < 0 || (u32(h, at) & 15) !== 15) { at = -1; for (let k = 0; k < 8; k++) { const o = P + 0x5C + 4 * k; if ((u32(h, o) & 15) === 15) { at = o; break; } } }
        if (at < 0) { undoNote("No room in the backpack to bring it back."); return true; }
        const gems = h[P + 0x184] | h[P + 0x185] << 8;
        if (u.gems > gems) { undoNote("Not enough gems left to take the sale back."); return true; }
        undoList.pop();
        for (let b = 0; b < 4; b++) h[at + b] = (u.w >>> (8 * b)) & 255;
        const ng = gems - u.gems; h[P + 0x184] = ng & 255; h[P + 0x185] = ng >> 8;
        try { if (window.__mirrorIw) { for (let b = 0; b < 4; b++) window.__mirrorIw(at - iwram + b); window.__mirrorIw(P + 0x184 - iwram); window.__mirrorIw(P + 0x185 - iwram); } } catch (e) {}
        undoSnap = undoRead();
        // The Backpack screen only redraws its items when it is opened, so flip to the next tab and back.
        if (gameState() === 0x0A) {
          const gi = (k, on) => { try { emu.gameManager.simulateInput(0, k, on); } catch (e) {} };
          gi(11, 1); setTimeout(() => gi(11, 0), 90); setTimeout(() => gi(10, 1), 750); setTimeout(() => { gi(10, 0); sendL(); }, 840);
        }
        undoNote(u.gems ? "Sale taken back (" + u.gems + " gems)." : "Item brought back.");
        return true;
      };
      const undo = () => {
        if (inSkillsTab()) { refundPulse(); return; }
        if (!inMenu() || !undoItem()) return;
        $("qsBtn").classList.add("on"); setTimeout(() => $("qsBtn").classList.remove("on"), 140);
      };
      window.__undo = undo;
      window.addEventListener("keydown", (e) => { if ((e.key === "c" || e.key === "C") && !e.repeat && inMenu()) { e.preventDefault(); undo(); } });
        // Spirit a skill needs: the game's own table for that hero (ROM pointer at player + 0x1C, 40 bytes per skill, cost at
        // +4), the same number the game checks before playing a Quick Skill (0x080430E8).
        const skCostOf = (P, s) => { const t = r32(P + 0x1C), R = rom(); if (t >>> 24 !== 8 || !R) return -1; const o = t - 0x08000000 + 40 * s; return (R[o] | R[o + 1] | R[o + 2] | R[o + 3]) ? R[o + 4] | R[o + 5] << 8 : -1; };
        window.__skCost = (s) => { try { if (iwram < 0) return -1; H8 = heap(); ew = findEw(); if (ew < 0) return -1; return skCostOf(playerAddr(), s); } catch (e) { return -1; } };
        const pickSkill = (P, now) => {
          const hero = r8(P + 0x19F), sp = r16(P + 0x17E), msp = r16(P + 0xD2) || 1;
          let best = -1, bc = -1;
          for (let s = 0; s < 6; s++) {
            if ((r8(P + 0x16A + s) << 24 >> 24) <= 0) continue;
            const key = hero * 8 + s; if ((noSkill.get(key) || 0) > now) continue;
            const real = skCostOf(P, s), cost = real > 0 ? real : skillCost.has(key) ? skillCost.get(key) : Math.round(msp * 0.3);
            if (sp < cost) continue;
            if (cost > bc) { bc = cost; best = s; }
          }
          return best;
        };
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
      };
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
