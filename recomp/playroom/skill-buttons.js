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

      document.querySelectorAll("#pad .btn[data-in]").forEach((el) => {
        const id = +el.dataset.in;
        // L and R are never swapped (Jordan undid the in-play swap, 2026-11-06).
        const press = (on) => {
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
