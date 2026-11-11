# Day/night on play time (Jordan, 2026-11-11: "Day and night cycles in the game count as 4 minutes of play time").
# v161 ran the 4 min day + 4 min night cycle on the wall clock, so it kept turning in menus, on pause and with the tab
# hidden. Now it only advances while a level is being played (state 1) and the page is visible, and the count is kept
# in localStorage so a reload carries on where it was. Usage: python3 daynight_v170.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
rep("    // Day and night: the clock decides (so two players see the same sky). nightness 0 = day, 1 = night.\n",
    "    // Day and night run on play time (v170): 4 min of play is day, 4 min is night. nightness 0 = day, 1 = night.\n"
    "    let playT = 0; try { playT = +localStorage.getItem(\"rotk-playT\") || 0; } catch (e) {}\n")
rep("t = (Date.now() / 1000) % T, up", "t = (playT + r / 2) % T, up")   # a new player starts in full day
rep("    return { looks, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled, nightness, names: byLevel };\n",
    "    let lastTick = 0, lastSave = 0;\n"
    "    const tick = (playing) => {   // called every 400 ms; counts only time spent playing a level with the page in view\n"
    "      const now = performance.now(), dt = lastTick ? Math.min(1, (now - lastTick) / 1000) : 0; lastTick = now;\n"
    "      if (playing && !document.hidden) playT += dt;\n"
    "      if (now - lastSave > 10000) { lastSave = now; try { localStorage.setItem(\"rotk-playT\", String(Math.round(playT))); } catch (e) {} }\n"
    "    };\n"
    "    return { looks, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled, nightness, names: byLevel, tick, playTime: () => playT };\n")
rep("      const b = M._rotk_iwram(), st = M.HEAPU8[b + 0x41B0], lv = M.HEAPU8[b + 0x41F8];\n",
    "      const b = M._rotk_iwram(), st = M.HEAPU8[b + 0x41B0], lv = M.HEAPU8[b + 0x41F8];\n      LIGHT_LOOKS.tick(st === 1);\n")
open(out, "w").write(s); print("ok v170")
