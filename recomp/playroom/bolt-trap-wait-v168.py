# Play Room v168 (Jordan 2026-11-11): Bolt Trap waits 3 s (90 game ticks) after each crossbow; page sets hero obj +0x9A = 0x7F so
# the game refuses the cast. Quick Drop exempt. Countdown on the button. Apply after freeze-log-v167.py.
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:80]!r}")
    s = s.replace(old, new)
rep('''        window.__bPick = (any, range) => {''', '''        // Bolt Trap waits 3 seconds after each crossbow (Jordan, 2026-11-11: "giving Quick Drop more of a usefulness"). Quick Drop
        // doesn't start the wait and isn't held up by it. The game itself refuses Bolt Trap (no Spirit taken) while Frodo's trap
        // count (hero object + 0x9A, which the crossbow code keeps at 0) is high, so the page sets it to 0x7F for 90 game ticks
        // (3 s at 30 a second, so pausing the game pauses the wait) after a new crossbow shows up in the list, then back to 0.
        // Not in online games (a page write there would split the two games); in a P2 game both games get the same write.
        const BT_TICKS = 90;
        let btSeen = new Set(), btObj = 0, btEnd = 0, btQd = -1, btLocked = false;
        const btWrite = (a, v) => {
          const mp = window.__mp, M = mp && mp.M;
          if (M && M._rotk_link_on && M._rotk_link_on() && M._rotk_link_ewram) { for (const m of [0, 1]) M.HEAPU8[M._rotk_link_ewram(m) + (a & 0x3ffff)] = v; }
          else { const o = at(a); if (o >= 0) H8[o] = v; }
        };
        const btNow = () => r32(0x030041A4);
        window.__btLeft = () => { try { if (!btLocked) return 0; const d = (btEnd - btNow()) | 0; return d > 0 ? d / 30 : 0; } catch (e) { return 0; } };
        setInterval(() => {
          try {
            if (iwram < 0 || (window.__mp && window.__mp.online)) return;
            ew = findEw(); H8 = heap(); if (ew < 0) return;
            const P = playerAddr(), hero = r32(P);
            if (hero >>> 24 !== 2 || r8(P + 0x19F) !== 0) { btSeen = new Set(); btObj = 0; btLocked = false; return; }
            if (hero !== btObj) { btObj = hero; btSeen = new Set(); btLocked = false; btQd = -1; }
            const pl = r8(0x03003F59) & 1, n = Math.min(3, r8(0x0203F390 + pl)), qd = r32(0x0203F500 + 4 * pl), now = btNow();
            const cur = new Set(); for (let k = 0; k < n; k++) cur.add(r32(0x0203F360 + pl * 24 + k * 8));
            let fresh = false; for (const o of cur) if (o && !btSeen.has(o)) fresh = true;
            const byQd = btQd >= 0 && qd !== btQd;
            if (btQd >= 0 && fresh && !byQd && !inMenu()) { btEnd = (now + BT_TICKS) | 0; btLocked = true; }
            btSeen = cur; btQd = qd;
            const want = btLocked && ((btEnd - now) | 0) > 0;
            if (!want) btLocked = false;
            const v = want ? 0x7F : 0;
            if (r8(hero + 0x9A) !== v && (want || r8(hero + 0x9A) === 0x7F)) btWrite(hero + 0x9A, v);
          } catch (e) {}
        }, 50);
        window.__bPick = (any, range) => {''')
# countdown on Bolt Trap's button, next to Quick Drop's
rep('''        const isQd = (v) => !!(v && v[0] === 0 && v[1] === 2);
        const btns = skIcons.map((el) => [el.parentElement, isQd(el.__v) && el.classList.contains("show")]).concat(xBtns.map((b, k) => [b, isQd(xList[k])]));
        for (const [btn, qd] of btns) {
          if (!btn) continue;
          if (qd && left > 0) {
            btn.__qd = true; btn.classList.add("used");
            let c = btn.querySelector(".cd"); if (!c) { c = document.createElement("b"); c.className = "cd"; btn.appendChild(c); }
            c.textContent = String(Math.ceil(left)); c.style.setProperty("--p", Math.min(1, left / total).toFixed(3));''',
'''        let btLeft = 0; try { btLeft = window.__btLeft ? window.__btLeft() : 0; } catch (e) {}
        const cdOf = (v) => !v || v[0] !== 0 ? null : v[1] === 2 && left > 0 ? [left, total] : v[1] === 1 && btLeft > 0 ? [btLeft, 3] : null;
        const btns = skIcons.map((el) => [el.parentElement, el.classList.contains("show") ? cdOf(el.__v) : null]).concat(xBtns.map((b, k) => [b, cdOf(xList[k])]));
        for (const [btn, cd] of btns) {
          if (!btn) continue;
          if (cd) {
            btn.__qd = true; btn.classList.add("used");
            let c = btn.querySelector(".cd"); if (!c) { c = document.createElement("b"); c.className = "cd"; btn.appendChild(c); }
            c.textContent = String(Math.ceil(cd[0])); c.style.setProperty("--p", Math.min(1, cd[0] / cd[1]).toFixed(3));''')
open(dst, "w", encoding="utf-8").write(s); print("ok")
