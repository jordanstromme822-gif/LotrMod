// Play Room v111: the walk animation keeps pace with speed boosts (1 player). Cut from the page (Auto scope);
// r8/r16/w8, heap(), findEw(), playerAddr(), inMenu() are the page's own memory helpers.
        // Speed boosts (items with "% Speed", Fleet of Foot, Rohan Sprint; all add to the hero's speed stat at player + 0xD4)
        // make the hero walk faster but the game keeps the walking pictures at their normal pace, so the feet slide
        // (Jordan, 2026-11-08). While the hero walks, the page moves the walk cycle (hero + 0x22, 12 steps) on by the same
        // extra share: +25% speed shows 1 extra step for every 4 the game plays. Measured: speed +25 walks 1.25x as fast,
        // +100 about 1.7x (the game's cap), so the share stops there. 1 player only (a page write would split linked games).
        let walkA = -1, walkX = -1, walkY = -1, walkAcc = 0;
        setInterval(() => {
          try {
            if (iwram < 0 || inMenu() || (window.__mp && window.__mp.M && window.__mp.M._rotk_link_on && window.__mp.M._rotk_link_on())) { walkA = -1; return; }
            H8 = heap(); ew = findEw(); if (ew < 0) return;
            const P = playerAddr(), hero = r32(P); if (hero >>> 24 !== 2) { walkA = -1; return; }
            const a = r8(hero + 0x22), x = r16(hero + 0xae), y = r16(hero + 0xb2);
            if (a === walkA) return;
            const extra = Math.min(0.7, (r16(P + 0xD4) << 16 >> 16) / 100), moved = walkA >= 0 && (x !== walkX || y !== walkY);
            const d = (a - walkA + 12) % 12;
            walkA = a; walkX = x; walkY = y;
            if (!moved || extra <= 0.01 || a >= 12 || d < 1 || d > 3) { walkAcc = 0; return; }
            walkAcc += d * extra;
            const add = Math.floor(walkAcc); if (add < 1) return;
            walkAcc -= add; const n = (a + add) % 12;
            w8(hero + 0x22, n); w8(hero + 0x23, n); walkA = n;
          } catch (e) {}
        }, 8);
