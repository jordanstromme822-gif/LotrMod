"""Play Room v236 (Jordan, 2026-11-21: yes to "Rebuild the game engine to speed up Moria on your iPhone").
Usage: engine-v236.py in.html out.html   (in.html = live v235 page). Ships with the new wide/rotk-link.js + rotk-link-0..2.wasm
(engine build in recomp/link/one/README.md, "v236").

Measured first (headless Chromium, Moria level 82, CPU profiler on so the box is CPU bound like the iPhone):
- ~40% of the engine's time is drawing the 320x240 wide picture; the game's own code is a few percent.
- The 60 fps smoothing (an in-between picture before each new game picture; odd steps drawn twice and averaged) costs
  ~40% of the engine's time on top.
Engine (v236):
- Rebuilt with the current compiler, the renderer's front-to-back wide rows (hidden pixels skipped, whole tiles at a
  time; checked pixel-identical against the old path in Moria, Fangorn and Helm's Deep) and a per-tile cache for the
  level-edge tiles. ~15% less engine time per picture in Moria.
- rotk_smooth(level): 2 = full smoothing (as before), 1 = in-between pictures drawn once, 0 = the game's own pictures.
Page (this script):
- Engine files get a new cache key (?v=236).
- Smoothing steps down only while the screen can't keep up: the engine's ticks (one per display refresh, tick stats)
  under 52 a second for 3 s in a level -> one step down. After 20 s at 55 or more it tries one step up; if the game
  slows again within 6 s it steps back and waits twice as long next time (up to 160 s). Menus, loads, door turbo and
  readings under 15/s (paused or stalled) don't count. Works the same in 1-player, P2 and online (each page only changes its own pictures).
"""
import sys
src, out = sys.argv[1:3]
t = open(src, encoding="utf-8").read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)

rep('const V = isLink ? "?v=209" : "?v=hd2";', 'const V = isLink ? "?v=236" : "?v=hd2";   // v236: faster engine build + rotk_smooth')

rep('''  window.__toggleCpu = () => {};''', '''  window.__toggleCpu = () => {};
  // v236: 60 fps smoothing steps down only while the screen can't keep up (the engine's ticks a second, one per refresh),
  // and back up when there is room again. window.__smooth = { level, rate } for tests; window.__smoothFix = n pins it.
  (() => {
    // Speed = the screen's pictures a second (the engine's ticks: one per display refresh). Behind = under 52 for 3 s, room = 55 or more.
    let lvl = 2, last = null, lowN = 0, goodN = 0, wait = 20, up = 0;
    const S = (window.__smooth = { level: 2, rate: 0 });
    const set = (M, k, why) => { lvl = k; S.level = k; try { M._rotk_smooth(k); } catch (e) {} (window.__wideLog || (window.__wideLog = [])).push("smooth " + k + " (" + why + ", " + S.rate.toFixed(1) + "/s)"); };
    setInterval(() => {
      const M = window.__wideM; if (!M || typeof M._rotk_smooth !== "function" || typeof M._rotk_tick_stats !== "function") { last = null; return; }
      if (typeof window.__smoothFix === "number") { if (lvl !== window.__smoothFix) set(M, window.__smoothFix, "pinned"); return; }
      const now = performance.now();
      let n = 0; try { const p = M._rotk_tick_stats() >> 2, h = M.HEAP32; n = h[p] + h[p + 1] + h[p + 2]; } catch (e) { return; }
      if (!last || document.hidden) { last = { n, now }; return; }
      const dt = (now - last.now) / 1000, rate = (n - last.n) / dt; last = { n, now };
      let playing = false;
      try { const iw = M._rotk_iwram(), ew = M._rotk_ewram(); playing = M.HEAPU8[iw + 0x41B0] === 1 && !(ew && M.HEAPU8[ew + 0x3FFF1]) && !window.__seamTurbo; } catch (e) {}
      if (!playing || dt > 3 || dt < 0.5 || rate < 15) { lowN = 0; return; }   // paused, loading or a stalled tab: not a speed reading
      S.rate = rate;
      if (rate < 52) { lowN++; goodN = 0; } else if (rate >= 55) { goodN++; lowN = 0; } else lowN = 0;
      if (up && now - up > 6000) up = 0;   // the step up held
      if (lowN >= 3 && lvl > 0) { if (up) { wait = Math.min(160, wait * 2); up = 0; } lowN = 0; goodN = 0; set(M, lvl - 1, "behind"); }
      else if (lvl < 2 && goodN >= wait) { goodN = 0; up = now; set(M, lvl + 1, "room"); }
    }, 1000);
  })();''')
open(out, "w", encoding="utf-8").write(t)
print("ok", len(t))
