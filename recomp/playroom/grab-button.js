// Play Room v112+: the Undo button is Grab / Open / Full in play (the game's R action); B only hits, R only flips
// menu tabs and casts its skill. Cut from the page; __stepPick, __grabInfo, sendL, bNoL are page helpers.
      // In play the Undo button is Grab (Jordan, 2026-11-08): the game's action (pick up, open a chest or the Shrine, talk),
      // which R and B no longer do. It reads Open next to an unopened chest or the Shrine, Full when the backpack is full,
      // else Grab. Items a little beyond the feet are walked to first (window.__stepPick).
      const qsLbl = $("qsBtn");
      let grabbing = false;
      const grab = (on) => {
        const gi = (k, v) => { try { emu.gameManager.simulateInput(0, k, v); } catch (e) {} };
        if (on) {
          if (grabbing || stepping) return;
          qsLbl.classList.add("on"); setTimeout(() => qsLbl.classList.remove("on"), 160);
          if (window.__stepPick && window.__stepPick()) return;
          grabbing = true; bNoL = true; sendL(); setTimeout(() => gi(11, 1), 40);
        } else if (grabbing) {
          setTimeout(() => { gi(11, 0); setTimeout(() => { grabbing = false; bNoL = false; sendL(); }, 50); }, 120);
        }
      };
      window.__grab = grab;
      const qsDown = (e) => { e.preventDefault(); if (inMenu()) { undo(); return; } grab(1); };
      qsLbl.addEventListener("pointerdown", qsDown);
      window.addEventListener("pointerup", () => grab(0), true); window.addEventListener("pointercancel", () => grab(0), true);
      setInterval(() => {
        let t = "Undo";
        if (!inMenu() && iwram >= 0) { const g = window.__grabInfo ? window.__grabInfo() : null; t = g && g.open ? "Open" : g && g.full ? "Full" : "Grab"; }
        if (qsLbl.textContent !== t) qsLbl.textContent = t;
        qsLbl.classList.toggle("full", t === "Full");
      }, 120);
