// Play Room v105: skill buttons (icons inside, black when used, countdown), B's skill on L, B picks up (window.__bPick).
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

        // B picks up too (Jordan, 2026-11-08): with an item at the hero's feet, B works as R unless it can't be taken
        // (gear with a full backpack, a full Kingsfoil pouch); then B swings. Auto and P2 also pick up before swinging.
        const herbRoom = (P, t) => t === 17 ? (r8(P + 0x1AA) >> 4) < 10 : t === 18 ? (r8(P + 0x1AA) & 15) < 10 : true;
        window.__bPick = () => {
          try {
            if (iwram < 0 || inMenu()) return false;
            ew = findEw(); H8 = heap(); if (ew < 0) return false;
            const P = playerAddr(), hero = r32(P); if (hero >>> 24 !== 2) return false;
            const [x, y] = pos(hero);
            for (const p of entities()) {
              if (r32(p + 0x14) !== ITEM_UPD || r8(p + 0x63) !== 3) continue;
              const [ix, iy] = pos(p); if (Math.abs(ix - x) > 10 || Math.abs(iy - y) > 10) continue;
              const t = r8(p + 0x60);
              const food = t === 15 || t === 16 || t === 19;   // eaten on the spot: only worth it when hurt
              if (t >= 25 ? !packFull(P) : food ? r16(P + 0x17C) < r16(P + 0xD0) : t >= 15 ? herbRoom(P, t) : false) return true;
            }
          } catch (e) {}
          return false;
        };
        // Some enemies are scenery standing inside the walls (no floor around them); those never fight and aren't counted.
