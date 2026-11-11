# Frodo's traps and the B button (Jordan, 2026-11-11): "Frodo's drop all trap ability doesn't have a timer", "traps won't let
# you pick one up with the grab button refunding partial spirit", "sometimes when I use the B button it casts L".
# Page-only patch of the live Play Room (v165 base; re-read the live page before publishing, other threads publish too).
#   python3 frodo-traps-v166.py <live page.html> <out.html>
# 1. B no longer casts the skill on L. L is held in play for Quick Skill, and B lets it go for a moment. The old single flag
#    and uncancelled timers let a late "give L back" land while B was down again (fast taps, taps under 40 ms, Grab while
#    holding B), so the game read L + B. Measured headless: 20 L+B overlaps and a stuck B on the old page, 0 now; tapping
#    B as Frodo cast Bolt Trap on the old page, not now.
# 2. Quick Drop: the game's cooldown worked (tested: a second cast is refused until EWRAM 0x0203F500 passes), but the
#    button showed the old Galadriel's Cloak 2 s timer. Now the button goes dark and counts down the real cooldown.
# 3. Grab next to one of Frodo's own crossbows picks it up: half of Bolt Trap's Spirit back, a tenth less per bolt fired.
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:80]!r}")
    s = s.replace(old, new)

# ---- 1. L is let go for named reasons (B, Grab, the walk-to-item), so one ending can't bring L back while another is still on ----
rep('''      let qsOn = true, qsHeld = false, lTouch = false, lCast = false, bNoL = false, stepping = false;''',
'''      let qsOn = true, qsHeld = false, lTouch = false, lCast = false, stepping = false;
      // Who wants L let go right now (v166): "b" while B is down, "grab" during Grab, "step" while walking to an item. Before v166
      // this was one flag, so a quick second B press (or Grab while B was held) had a late timer give L back while B was down,
      // and the game read L + B as a Quick Skill: B cast the skill on L (Jordan, 2026-11-11).
      const noL = new Set();
      let bDown = false, bPressT = 0, bFreeT = 0;''')
rep('''      const sendL = () => { try { emu.gameManager.simulateInput(0, 10, (qsHeld || lTouch || lCast) && !bNoL ? 1 : 0); } catch (e) {} };''',
'''      const sendL = () => { try { emu.gameManager.simulateInput(0, 10, (qsHeld || lTouch || lCast) && !noL.size ? 1 : 0); } catch (e) {} };''')
rep('''      window.__lBlip = () => { try { emu.gameManager.simulateInput(0, 10, (qsHeld || lTouch || lCast) && !bNoL ? 0 : 1); } catch (e) {} setTimeout(sendL, 110); };''',
'''      window.__lBlip = () => { try { emu.gameManager.simulateInput(0, 10, (qsHeld || lTouch || lCast) && !noL.size ? 0 : 1); } catch (e) {} setTimeout(sendL, 110); };''')
# stepPick
rep('''        const L0 = qsHeld || lTouch; if (L0) { bNoL = true; sendL(); }''',
'''        noL.add("step"); sendL();''')
rep('''          setTimeout(() => { stepping = false; if (bNoL) { bNoL = false; sendL(); } }, pick ? 270 : 0);''',
'''          setTimeout(() => { stepping = false; noL.delete("step"); sendL(); }, pick ? 270 : 0);''')
# grab
rep('''          grabbing = true; bNoL = true; sendL(); setTimeout(() => gi(11, 1), 40);''',
'''          if (window.__xbPick && window.__xbPick()) return;
          grabbing = true; noL.add("grab"); sendL(); setTimeout(() => gi(11, 1), 40);''')
rep('''          setTimeout(() => { gi(11, 0); setTimeout(() => { grabbing = false; bNoL = false; sendL(); }, 50); }, 120);''',
'''          setTimeout(() => { gi(11, 0); setTimeout(() => { grabbing = false; noL.delete("grab"); sendL(); }, 50); }, 120);''')
# B button
rep('''          if (id === 0) {
            if (on && (qsHeld || lTouch)) { bNoL = true; sendL(); }
            sid = 0;
            if (!on && bNoL) { try { emu.gameManager.simulateInput(0, sid, 0); } catch (e) {} setTimeout(() => { bNoL = false; sendL(); }, 50); return; }
            if (on && bNoL) { setTimeout(() => { try { emu.gameManager.simulateInput(0, sid, 1); } catch (e) {} }, 40); return; }
          }''',
'''          if (id === 0) {
            // L is let go first and B goes down 40 ms later (only if the finger is still on it); after B comes up, L comes back
            // 50 ms later unless B went down again. Pending timers are cancelled, so fast tapping never leaves L + B together.
            clearTimeout(bPressT); clearTimeout(bFreeT);
            if (on) {
              bDown = true;
              const lWasOn = (qsHeld || lTouch || lCast) && !noL.size;
              noL.add("b"); sendL();
              if (lWasOn) bPressT = setTimeout(() => { if (bDown) try { emu.gameManager.simulateInput(0, 0, 1); } catch (e) {} }, 40);
              else try { emu.gameManager.simulateInput(0, 0, 1); } catch (e) {}
            } else {
              bDown = false;
              try { emu.gameManager.simulateInput(0, 0, 0); } catch (e) {}
              bFreeT = setTimeout(() => { if (!bDown) { noL.delete("b"); sendL(); } }, 50);
            }
            return;
          }''')
# extra skill buttons press L themselves: let B go in the game for that moment, so the cast can't also read L + B
rep('''        const btn = xBtns[k]; btn.classList.add("on"); skillPressed(btn, v);
        try { emu.gameManager.simulateInput(0, 10, 1); } catch (e) {}''',
'''        const btn = xBtns[k]; btn.classList.add("on"); skillPressed(btn, v);
        if (bDown) try { emu.gameManager.simulateInput(0, 0, 0); } catch (e) {}
        try { emu.gameManager.simulateInput(0, 10, 1); } catch (e) {}''')
rep('''        setTimeout(() => { try { emu.gameManager.simulateInput(0, 11, 0); } catch (e) {} sendL(); btn.classList.remove("on"); }, 200);''',
'''        setTimeout(() => { try { emu.gameManager.simulateInput(0, 11, 0); } catch (e) {} sendL(); btn.classList.remove("on"); if (bDown) setTimeout(() => { if (bDown) try { emu.gameManager.simulateInput(0, 0, 1); } catch (e) {} }, 40); }, 200);''')

# ---- 2. Quick Drop cooldown on its button ----
rep('''      const SK_DUR = { 0: { 2: [2, 2], 3: [5, 2], 4: [10, 5] },''', '''      const SK_DUR = { 0: { 3: [5, 2], 4: [10, 5] },''')
rep('''            } else setTimeout(() => { if (!skActive.has(btn)) btn.classList.remove("used"); }, 500);
          } else if (now - skPend.t > 900) { if (!skActive.has(btn)) btn.classList.remove("used"); skPend = null; }''',
'''            } else setTimeout(() => { if (!skActive.has(btn) && !btn.__qd) btn.classList.remove("used"); }, 500);
          } else if (now - skPend.t > 900) { if (!skActive.has(btn) && !btn.__qd) btn.classList.remove("used"); skPend = null; }''')
rep('''      xBtns.forEach((b, k) => b.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); castExtra(k); }));''',
'''      xBtns.forEach((b, k) => b.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); castExtra(k); }));
      // Quick Drop's cooldown on its button (Jordan, 2026-11-11: "no timer"). The game keeps the cooldown itself (EWRAM 0x0203F500
      // + 4 * player = game tick when it ends, ticks at 0x030041A4, 30 a second; tools/orcslots/crossbow.c); the button turns dark
      // and counts down the seconds left, the same look as the timed skills.
      const qdEw = () => { try { const mp = window.__mp; if (mp && mp.ewram) return mp.ewram(); if (mp && mp.M && mp.M._rotk_ewram) return mp.M._rotk_ewram(); } catch (e) {} return iwram >= 0x40000 ? iwram - 0x40000 : -1; };
      setInterval(() => {
        let left = 0, total = 60;
        try {
          const h = emu.Module.HEAPU8;
          if (iwram >= 0 && h && !inMenu()) {
            const pl = h[iwram + 0x3F59] & 1, P = iwram + 0x3C00 + 0x1AC * pl, ew = qdEw();
            if (h[P + 0x19F] === 0 && ew >= 0) {
              const u32 = (o) => (h[o] | h[o + 1] << 8 | h[o + 2] << 16 | h[o + 3] << 24) >>> 0;
              const d = (u32(ew + 0x3F500 + 4 * pl) - u32(iwram + 0x41A4)) >>> 0;
              if (d && d <= 1800) { left = d / 30; total = 60 - 7 * (Math.max(1, Math.min(5, h[P + 0x172])) - 1); }
            }
          }
        } catch (e) {}
        const isQd = (v) => !!(v && v[0] === 0 && v[1] === 2);
        const btns = skIcons.map((el) => [el.parentElement, isQd(el.__v) && el.classList.contains("show")]).concat(xBtns.map((b, k) => [b, isQd(xList[k])]));
        for (const [btn, qd] of btns) {
          if (!btn) continue;
          if (qd && left > 0) {
            btn.__qd = true; btn.classList.add("used");
            let c = btn.querySelector(".cd"); if (!c) { c = document.createElement("b"); c.className = "cd"; btn.appendChild(c); }
            c.textContent = String(Math.ceil(left)); c.style.setProperty("--p", Math.min(1, left / total).toFixed(3));
          } else if (btn.__qd) { btn.__qd = false; if (!skActive.has(btn)) { btn.classList.remove("used"); const c = btn.querySelector(".cd"); if (c) c.remove(); } }
        }
      }, 200);''')

# ---- 3. Grab picks up one of Frodo's crossbows (Bolt Traps) for part of its Spirit back ----
rep('''        window.__bPick = (any, range) => {''',
'''        // Grab next to one of Frodo's own crossbows, with nothing else to take, open or talk to, picks it up (Jordan, 2026-11-11):
        // the crossbow goes away and Frodo gets half of Bolt Trap's Spirit back, less a tenth of that for each bolt it fired
        // (an unused one: 50%, after 5 bolts: 25%). The crossbow list is EWRAM 0x0203F360 [player][3] x 8 bytes (object,
        // u16 timer, shots left, reload) and 0x0203F390 [player] = how many; setting the timer to 1 lets the game's own crossbow
        // code take it down next tick (silently, like an old one being replaced). Not in online games: a page write there would
        // split the two games. In a P2 game the same write goes to P2's game too.
        const XB_UPD = null;
        window.__xbPick = () => {
          try {
            if (iwram < 0 || inMenu() || (window.__mp && window.__mp.online)) return false;
            ew = findEw(); H8 = heap(); if (ew < 0) return false;
            const P = playerAddr(), hero = r32(P); if (hero >>> 24 !== 2 || r8(P + 0x19F) !== 0) return false;
            const g = window.__grabInfo && window.__grabInfo(); if (g && g.open) return false;
            if (bAct({ r8, r16, r32 }, P, entities(), true, true, 22)) return false;
            const pl = r8(0x03003F59) & 1, n = Math.min(3, r8(0x0203F390 + pl)), [x, y] = pos(hero);
            let best = -1, bd = 1e9;
            for (let k = 0; k < n; k++) {
              const e = 0x0203F360 + pl * 24 + k * 8, o = r32(e);
              if (o >>> 24 !== 2 && o >>> 24 !== 3) continue;
              if (r8(o + 0x62) === 4) continue;
              const [ox, oy] = pos(o), d = Math.max(Math.abs(ox - x), Math.abs(oy - y));
              if (d <= 22 && d < bd) { bd = d; best = k; }
            }
            if (best < 0) return false;
            const e = 0x0203F360 + pl * 24 + best * 8, shots = Math.min(10, r8(e + 6));
            const wEw = (a, v) => {   // EWRAM write, in both games when P2 plays
              const mp = window.__mp, M = mp && mp.M;
              if (M && M._rotk_link_on && M._rotk_link_on() && M._rotk_link_ewram) { for (const m of [0, 1]) M.HEAPU8[M._rotk_link_ewram(m) + (a & 0x3ffff)] = v; }
              else H8[at(a)] = v;
            };
            wEw(e + 4, 1); wEw(e + 5, 0);
            const cost = skCostOf(P, 1), back = cost > 0 ? Math.floor(cost * 0.5 * shots / 10) : 0;
            if (back > 0) {
              const sp = Math.min(r16(P + 0xD2) || 0xffff, r16(P + 0x17E) + back);
              w8(P + 0x17E, sp & 255); w8(P + 0x17F, sp >> 8);
            }
            return true;
          } catch (e) { return false; }
        };
        window.__bPick = (any, range) => {''')
rep('''        const XB_UPD = null;
''', '')
open(dst, "w", encoding="utf-8").write(s)
print("ok")
