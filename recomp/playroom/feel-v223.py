#!/usr/bin/env python3
"""Play Room v223: smoother play (Jordan, 2026-11-20: "Game feels glitchy slow and buttons are unresponsive",
"gameplay doesn't feel smooth character glides a lot", "if I swing near an enemy and I'm just out of reach it should
move my character a few steps so when I swing it reaches the enemy that I'm nearest to if using melee attacks").

  python3 feel-v223.py in.html out.html

1. Gliding: with the free joystick, the d-pad direction the page gives the game (__freeDir8, 16 facings) and the
   facing the 32-facing hook (tools/turn16/turn16.c, compiled into the engine) sets (+0xF8 = f8_of(F32[angle])) did not
   agree for about a quarter of all stick angles (11-34 degrees off each diagonal on the ground). Every tick the game
   turned the hero back to the d-pad way and restarted the walk picture, so his legs froze while he slid along.
   __freeDir8 now uses the hook's own table and rounding (F32, same hysteresis), so the two always agree.
2. Buttons: the game reads the buttons once a tick (30 a second) and only swings when B was down for 2 reads, so a
   quick tap (under ~60 ms, measured: 40 and 55 ms taps never swung, 70 ms 3 of 5) did nothing. Now a press lasts at
   least 2 ticks (B 3) and a let-go 1 tick, queued per button, and a change goes to the engine at once instead of on
   the next picture (one screen refresh sooner).
3. Melee step: B with no enemy in reach but one a few steps away (up to 38 px past reach) walks the hero to the
   nearest one (joystick angle straight at it, up to ~0.65 s) and swings when in reach. Not for Legolas (bow), not while
   Moria Auto plays; moving the stick to another way cancels the walk and swings at once. Only buttons and the stick
   angle are used (no game memory writes), so it works the same in 1-player, P2 and online.
"""
import sys
src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8").read()

def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"expected {n} got {c}: {old[:100]!r}")
    s = s.replace(old, new)

F32 = "0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,4,4,4,4,4,4,4,5,5,5,5,5,6,6,6,6,7,7,7,7,8,8,8,8,8,9,9,9,9,10,10,10,10,11,11,11,11,11,12,12,12,12,12,12,12,13,13,13,13,13,13,13,13,14,14,14,14,14,14,14,14,14,14,14,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,16,16,16,16,16,16,16,16,16,16,16,16,16,16,16,17,17,17,17,17,17,17,17,17,17,17,17,17,17,17,18,18,18,18,18,18,18,18,18,18,18,19,19,19,19,19,19,19,19,20,20,20,20,20,20,20,21,21,21,21,21,22,22,22,22,23,23,23,23,24,24,24,24,24,25,25,25,25,26,26,26,26,27,27,27,27,27,28,28,28,28,28,28,28,29,29,29,29,29,29,29,29,30,30,30,30,30,30,30,30,30,30,30,31,31,31,31,31,31,31,31,31,31,31,31,31,31,31,0,0,0,0,0,0,0"
assert F32.count(",") == 255

# 1. d-pad direction = the hook's facing
rep("""  window.__freeDir8 = (ang) => {
    const t = ang * Math.PI / 128, phi = ((Math.atan2(Math.sin(t), 2 * Math.cos(t)) * 180 / Math.PI) + 360) % 360;
    const f = Math.round(phi / 22.5) % 16;
    return !(f & 1) ? f >> 1 : f < 8 ? (f - 1) >> 1 : ((f + 1) >> 1) & 7;
  };""",
"""  // v223 (Jordan: "character glides a lot"): the same table, rounding and border hold as the 32-facing hook
  // (tools/turn16/turn16.c: want = F32[angle], kept until 3 steps into the next facing, +0xF8 = (want + 2) >> 2), so the
  // game's d-pad way always matches the facing the hook gives him. Before, about a quarter of the stick's angles
  // disagreed: each tick the game turned him back and restarted his walk picture, so he slid with his legs still.
  const F32T = [""" + F32 + """];
  let fd8Last = -1;
  window.__freeDir8 = (ang) => {
    const a = ang & 255; let w = F32T[a];
    if (fd8Last >= 0 && w !== fd8Last && (F32T[(a + 3) & 255] === fd8Last || F32T[(a - 3) & 255] === fd8Last)) w = fd8Last;
    fd8Last = w;
    return ((w + 2) >> 2) & 7;
  };""")

# stick: remember the player's own stick, and let the melee step steer it
rep("""  window.__freeStick = (held, ang) => {
    const M = freeM(); if (!M) return;""",
"""  window.__freeStick = (held, ang, mine) => {
    if (!mine) { window.__stickUser = [held, ang]; if (window.__hitStepLock) return; }   // v223: the melee step steers for a moment
    const M = freeM(); if (!M) return;""")

# 2. buttons: at least one game tick per press, sent at once
rep("""        simulateInput: (p, id, v) => { const b = LIBRETRO_TO_GBA[id]; if (!b) return; held = v ? (held | b) : (held & ~b); if (boot === null) H.keys = 1023 & ~held; },""",
"""        simulateInput: (p, id, v) => { const b = LIBRETRO_TO_GBA[id]; if (!b) return; keyEv(b, v ? 1 : 0); },""")
rep("""    const readSave = () => { try { return M.FS.readFile("/data/saves/rotk-modded.sav"); } catch (e) { return null; } };
    const fake = {""",
"""    const readSave = () => { try { return M.FS.readFile("/data/saves/rotk-modded.sav"); } catch (e) { return null; } };
    // v223 (Jordan: "buttons are unresponsive"): the game reads the buttons once a game tick (30 a second). A quick tap
    // that went down and up between two reads never reached it, more often when the phone fell behind. Now each button
    // change waits until the game has had a tick with the one before it (queued per button), and changes are written
    // to the engine at once instead of on the next picture.
    let kShown = 0; const kSt = {};
    const kTick = () => { try { const H8 = M.HEAPU8, a = M._rotk_iwram() + 0x41A4; return (H8[a] | H8[a + 1] << 8 | H8[a + 2] << 16 | H8[a + 3] << 24) >>> 0; } catch (e) { return -1; } };
    // A press lasts 2 game ticks (B 3: the game only swings when B was down for 2 of its reads - a 40-55 ms tap did
    // nothing, measured), a let-go 1 tick. Without the tick count (menus): pictures or time.
    const kReady = (s) => { if (s.t === null) return true; const need = s.v ? (s.b === 2 ? 3 : 2) : 1, t = kTick();
      return (t >= 0 && ((t - s.t) >>> 0) >= need) || H.frames - s.pic >= 2 * need + 1 || performance.now() - s.ms > 40 * need + 40; };
    const kApply = () => { if (boot !== null) return; H.keys = 1023 & ~kShown; try { H.st("keys", H.keys); } catch (e) {} };
    const kSet = (b, v, s) => { kShown = v ? (kShown | b) : (kShown & ~b); s.v = v; s.t = kTick(); s.pic = H.frames; s.ms = performance.now(); };
    const keyEv = (b, v) => {
      held = v ? (held | b) : (held & ~b);
      const s = kSt[b] || (kSt[b] = { b, v: 0, t: null, pic: 0, ms: 0, q: [] });
      const last = s.q.length ? s.q[s.q.length - 1] : (kShown & b ? 1 : 0);
      if (last === v) return;
      if (!s.q.length && kReady(s)) { kSet(b, v, s); kApply(); return; }
      s.q.push(v); if (s.q.length > 4) s.q.splice(0, 2);   // very fast tapping: drop the oldest tap
    };
    const kPump = () => {
      let ch = false;
      for (const k in kSt) { const s = kSt[k], b = +k; if (s.q.length && kReady(s)) { kSet(b, s.q.shift(), s); ch = true; } }
      if (ch) kApply();
    };
    window.__keyPump = kPump;
    window.__keyBusy = (b) => !!(kShown & b) || !!(kSt[b] && kSt[b].q.length);   // the game still sees (or will see) b down
    const fake = {""")
rep("""    const draw = () => { H.draw(); requestAnimationFrame(draw); };
    window.__wideM = M;""",
"""    const draw = () => { kPump(); H.draw(); requestAnimationFrame(draw); };
    setInterval(kPump, 8);   // v223: queued button changes also go out between pictures
    window.__wideM = M;""")
# setBoot(null) hands back the shown buttons, not the raw ones
rep("""    const setBoot = (k) => { boot = k; H.keys = 1023 & ~(boot === null ? held : boot); try { H.st("keys", H.keys); } catch (e) {} };""",
"""    const setBoot = (k) => { boot = k; H.keys = 1023 & ~(boot === null ? kShown : boot); try { H.st("keys", H.keys); } catch (e) {} };""")

# 3. melee step
rep("""      const held = { 4: 0, 5: 0, 6: 0, 7: 0 };
      const setDir = (id, on) => {""",
"""      // v223 melee step (Jordan, 2026-11-20): B with no enemy in reach but one a few steps away walks the hero to the
      // nearest one and swings when he gets there. Reach as Moria Auto's hit check (22 x 14 px); up to 38 px more is
      // walked (about 0.4 s). Buttons and the stick angle only, so 1-player, P2 and online all play it the same.
      const HIT_X = 22, HIT_Y = 14, STEP_GAP = 38, FOE_DEAD = new Set([0x11, 0x15, 4, 0x1b, 0x13]);
      let hitStepping = false;
      const foeMem = () => {
        const M = window.__wideM; if (!M || typeof M._rotk_ewram !== "function") return null;
        const H8 = M.HEAPU8, iw = M._rotk_iwram(), ew = M._rotk_ewram();
        const r8 = (a) => a >= 0x03000000 ? H8[iw + (a - 0x03000000)] : H8[ew + (a & 0x3ffff)];
        const r16 = (a) => r8(a) | r8(a + 1) << 8, r32 = (a) => (r8(a) | r8(a + 1) << 8 | r8(a + 2) << 16 | r8(a + 3) << 24) >>> 0;
        return { r8, r16, r32, P: 0x03003C00 + 0x1AC * (r8(0x03003F59) & 1) };
      };
      const foeAlive = (m, p) => m.r32(p + 0x14) === 0x0801b9d1 && !FOE_DEAD.has(m.r8(p + 0x62)) && m.r8(p + 0x63) !== 0x2f && !(m.r32(p + 0xe8) & 2);
      const foeNear = () => {
        const m = foeMem(); if (!m) return null;
        const hero = m.r32(m.P); if (hero >>> 24 !== 2) return null;
        if (m.r8(m.P + 0x19F) === 1) return null;                         // Legolas: his B is the bow
        const st = m.r8(hero + 0x62); if (st !== 1 && st !== 2) return null;   // only from standing or walking
        const x = m.r16(hero + 0xAE), y = m.r16(hero + 0xB2);
        let p = hero, n = 0; while (n++ < 400) { const nx = m.r32(p); if (!nx || nx >>> 24 !== 2) break; p = nx; }
        let best = null, bd = 1e9, inReach = false;
        for (n = 0; p >>> 24 === 2 && n < 400; n++, p = m.r32(p + 4)) {
          if (!foeAlive(m, p)) continue;
          const dx = m.r16(p + 0xAE) - x, dy = m.r16(p + 0xB2) - y;
          if (Math.abs(dx) <= HIT_X && Math.abs(dy) <= HIT_Y) inReach = true;
          const d = Math.hypot(dx, dy * 1.5); if (d < bd) { bd = d; best = { dx, dy, p }; }
        }
        return { m, hero, best, inReach };
      };
      window.__stepHit = (stillDown) => {
        if (stepping || hitStepping || inMenu()) return false;
        { const ab = document.getElementById("autoBtn"); if (ab && ab.classList.contains("on")) return false; }
        let f = null; try { f = foeNear(); } catch (e) {}
        if (!f || !f.best || f.inReach || Math.abs(f.best.dx) > HIT_X + STEP_GAP || Math.abs(f.best.dy) > HIT_Y + 24) return false;
        hitStepping = true; window.__hitStepLock = true;
        const { m, hero } = f, foe = f.best.p, sec0 = sector, t0 = performance.now();
        const gi = (k, on) => { try { emu.gameManager.simulateInput(0, k, on); } catch (e) {} };
        let lastXY = "", still = 0, ended = false;
        const aim = (dx, dy) => {
          const ang = Math.round(Math.atan2(dx, -dy) * 128 / Math.PI + 256) % 256;
          try { window.__freeStick && window.__freeStick(true, ang, true); } catch (e) {}
          let on;
          if (window.__freeActive && window.__freeActive() && window.__freeDir8) on = SECTOR_DIRS[(window.__freeDir8(ang) + 6) % 8];
          else { on = []; if (dx > 2) on.push(7); if (dx < -2) on.push(6); if (dy > 2) on.push(5); if (dy < -2) on.push(4); }
          [4, 5, 6, 7].forEach((k) => gi(k, on.includes(k) ? 1 : 0));
        };
        const finish = () => {
          if (ended) return; ended = true;
          [4, 5, 6, 7].forEach((k) => gi(k, 0));
          gi(0, 1);                                                      // swing (he faces the foe: the stick pointed at it)
          setTimeout(() => {
            window.__hitStepLock = false; hitStepping = false;
            const u = window.__stickUser; try { window.__freeStick && window.__freeStick(!!(u && u[0]), u ? u[1] | 0 : 0, true); } catch (e) {}
            [4, 5, 6, 7].forEach((k) => gi(k, held[k]));
            if (!stillDown()) gi(0, 0);
          }, 90);
        };
        const tick = () => {
          if (ended) return;
          try {
            if (sector !== sec0 || inMenu() || m.r32(m.P) !== hero || !foeAlive(m, foe) || performance.now() - t0 > 650) { finish(); return; }
            const x = m.r16(hero + 0xAE), y = m.r16(hero + 0xB2), dx = m.r16(foe + 0xAE) - x, dy = m.r16(foe + 0xB2) - y;
            if (Math.abs(dx) <= HIT_X - 3 && Math.abs(dy) <= HIT_Y - 3) { finish(); return; }
            const xy = x + "," + y; still = xy === lastXY ? still + 1 : 0; lastXY = xy;
            if (still >= 4) { finish(); return; }                           // a wall in the way: swing from here
            aim(dx, dy);
          } catch (e) { finish(); return; }
          setTimeout(tick, 25);
        };
        tick(); return true;
      };
      const held = { 4: 0, 5: 0, 6: 0, 7: 0 };
      const setDir = (id, on) => {""")
rep("""            clearTimeout(bPressT); clearTimeout(bFreeT);
            if (on) {""",
"""            // v223: a let-go no longer cancels a B that is still waiting its 40 ms (Quick Skill Select keeps L down in play,
            // so every tap waited): a tap shorter than 40 ms used to be dropped. L comes back only once the game has seen
            // B let go (buttons can be held a tick longer now), so L + B never meet.
            clearTimeout(bFreeT); if (on) { clearTimeout(bPressT); bPressT = 0; }
            const bFreeAfter = () => { bFreeT = setTimeout(function w() { if (bDown) return; if (window.__hitStepLock || bPressT || (window.__keyBusy && window.__keyBusy(2))) { bFreeT = setTimeout(w, 15); return; } noL.delete("b"); sendL(); }, 50); };
            if (on) {""")
rep("""              if (lWasOn) bPressT = setTimeout(() => { if (bDown) try { emu.gameManager.simulateInput(0, 0, 1); } catch (e) {} }, 40);
              else try { emu.gameManager.simulateInput(0, 0, 1); } catch (e) {}
            } else {
              bDown = false;
              try { emu.gameManager.simulateInput(0, 0, 0); } catch (e) {}
              bFreeT = setTimeout(() => { if (!bDown) { noL.delete("b"); sendL(); } }, 50);""",
"""              if (window.__stepHit && window.__stepHit(() => bDown)) return;   // v223: a few steps to the nearest foe, then the swing
              if (lWasOn) bPressT = setTimeout(() => { bPressT = 0; try { emu.gameManager.simulateInput(0, 0, 1); if (!bDown) { emu.gameManager.simulateInput(0, 0, 0); bFreeAfter(); } } catch (e) {} }, 40);
              else try { emu.gameManager.simulateInput(0, 0, 1); } catch (e) {}
            } else {
              bDown = false;
              if (window.__hitStepLock || bPressT) { bFreeAfter(); return; }   // v223: the step (or the waiting press) swings and lets go itself
              try { emu.gameManager.simulateInput(0, 0, 0); } catch (e) {}
              bFreeAfter();""")
open(dst, "w", encoding="utf-8").write(s)
print("v223 page ok", len(s))
