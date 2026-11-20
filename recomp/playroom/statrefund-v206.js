  // v206 Take attribute points back any time (Jordan, 2026-11-20: "stats placed should allow me to unplace them
  // whenever I want"). The game's own Stats page (state 0x0E) already takes a point back with Left, but only:
  //   - down to the value the attribute had when the page was opened (pending values 0x03001CE8 + 12 * player are
  //     compared with the hero's base attributes P + 0x2A..0x32 in 0x08028634), so points placed on an earlier visit
  //     were locked in for good, and
  //   - when the hero had spare points as the page opened (0x030041BC = points != 0, set in the enter function
  //     0x080274F4; Left / Right / Up / Down do nothing while it is 0).
  // So a short moment after the page opens, the page lowers the base attributes to the hero's starting values
  // (read from the game file: the hero table of tools/heroes.py if the game file has it, else the New Game code
  // 0x08025D6C) and sets 0x030041BC to 1. The game then does everything itself: Left removes a point (down to the
  // starting value), gives it back to the pool (P + 0x19D) and updates Hit Points / Spirit Points and the derived
  // attributes; Right places it again. Leaving the page writes the pending values back into the base (exit
  // 0x08027CDC), exactly as before, so nothing else changes. If the page opened with no spare points, the cursor
  // was drawn hidden, so the page taps Down then Up to make the game draw it.
  // Works in 1-player, P2 and online (writes go through __mirrorIw and travel with the buttons since v180).
  (function statRefund() {
    const ORDER = [0x2A, 0x2C, 0x2E, 0x30, 0x32];   // Courage, Defense, Health, Accuracy, Strength
    const floors = {};
    const floorOf = (hid) => {
      if (floors[hid]) return floors[hid];
      const R = window.__romFull; if (!R || hid > 7) return null;
      const u16 = (o) => R[o] | R[o + 1] << 8, u32 = (o) => (u16(o) | u16(o + 2) << 16) >>> 0;
      let out = null;
      if (String.fromCharCode(...R.subarray(0x9E6E0, 0x9E6EE)) === "LOTRMOD-HEROES") {
        out = ORDER.map((_, k) => u16(0x9E700 + 16 * hid + 2 * k));   // tools/heroes.py table
      } else {
        // original New Game code: one switch case per hero of movs rX,#n / strh rX,[r0,#off], ending in a b to a
        // shared strh r1,[r0,#0x32]
        const regs = {}, st = {};
        let a = (u32(0x25D8C + 4 * hid) & ~1) - 0x08000000;
        for (let n = 0; n < 40; n++, a += 2) {
          const h = u16(a);
          if ((h & 0xF800) === 0x2000) regs[(h >> 8) & 7] = h & 255;
          else if ((h & 0xF800) === 0x8000 && ((h >> 3) & 7) === 0) st[((h >> 6) & 31) * 2] = regs[h & 7];
          else if ((h & 0xF800) === 0xE000) { if (!(0x32 in st)) st[0x32] = regs[1]; break; }
        }
        if (ORDER.every((o) => st[o] !== undefined)) out = ORDER.map((o) => st[o]);
      }
      return out && (floors[hid] = out);
    };
    let seen = 0, done = false, left = null;
    const gi = (id, v) => { try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} };
    const tap = (id, at) => setTimeout(() => { gi(id, 1); setTimeout(() => gi(id, 0), 70); }, at);
    setInterval(() => {
      try {
        const M = window.__wideM;
        if (!M || !M.HEAPU8 || !M._rotk_iwram || (M._rotk_link_iwram && (!M._rotk_link_on() || (window.__mp && window.__mp.online && !window.__mp.sync)))) { seen = 0; done = false; return; }
        const onl = !!(window.__mp && window.__mp.online), me = onl ? window.__mp.me & 1 : 0;
        const iw = onl ? M._rotk_link_iwram(me) : M._rotk_iwram();
        const H8 = M.HEAPU8;
        const mirror = (o, n) => { try { if (window.__mirrorIw) for (let j = 0; j < n; j++) window.__mirrorIw(o - iw + j); } catch (e) {} };
        if (!iw || H8[iw + 0x41B0] !== 0x0E) {
          // page closed: hand the other game (P2's partner game / the online copy) the committed result too, since a
          // partner game that sat out the page never saw the Stats page messages
          // (a few ticks later: the game writes the pending values back a moment after the state changes)
          seen = 0; done = false;
          if (left && iw && left.iw === iw && ++left.t >= 10) { const P = left.P; mirror(P + 0x28, 12); mirror(P + 0xC6, 14); mirror(P + 0x19D, 1); left = null; }
          return;
        }
        if (done || ++seen < 6) return;   // ~0.3 s after the page opened (its link message has been handled)
        done = true;
        const p = H8[iw + 0x3F59] & 1, P = iw + 0x3C00 + 0x1AC * p, fl = floorOf(H8[P + 0x19F]);
        if (!fl) return;
        left = { iw, P, t: 0 };
        ORDER.forEach((o, k) => {
          const base = H8[P + o] | H8[P + o + 1] << 8;
          if (base > fl[k]) { H8[P + o] = fl[k] & 255; H8[P + o + 1] = fl[k] >> 8; mirror(P + o, 2); }
        });
        if (!(H8[iw + 0x41BC] | H8[iw + 0x41BD] | H8[iw + 0x41BE] | H8[iw + 0x41BF])) {
          H8[iw + 0x41BC] = 1; mirror(iw + 0x41BC, 1);
          tap(5, 150); tap(4, 400);   // Down, Up: the game draws the cursor it hid
        }
        window.__statRefund = { p, floors: fl };
      } catch (e) {}
    }, 50);
  })();
