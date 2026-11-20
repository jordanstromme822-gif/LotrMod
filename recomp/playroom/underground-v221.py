# No day and night underground (Jordan, 2026-11-20: "Moria doesn't need day night cycles because it's under ground
# along with any cave map"). Moria (Dwarf halls 49, 81-84) and the Caves group were already a fixed look, but:
#  - Ice Caves (48) was in "Snow & ice", so it turned to night with the clock. It now uses the Caves look, fixed.
#  - Rooms with no sky (Orc Tower Top Room 4 / Tower 5, the Corsair ship's Below 15, Orthanc 53 / Tower Levels 57,
#    Steward's Tomb 67) keep their own look but no longer turn to night or move the sun.
#  - Coming back from the pause menu, backpack or a loading screen, the picture eased from the bright menu look back
#    to the dark cave look over a second or two, which reads like dusk falling. Underground levels now snap to their
#    look as play resumes.
# Usage: python3 underground-v221.py in.html out.html
import sys
p, out = sys.argv[1], sys.argv[2]; s = open(p).read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a)); s = s.replace(a, b)
rep('    const FIXED = { Mordor: 1, Lava: 1, Wasteland: 1, Caves: 1, "Dwarf halls": 1 };\n',
    '    const FIXED = { Mordor: 1, Lava: 1, Wasteland: 1, Caves: 1, "Dwarf halls": 1 };\n'
    '    // v221: no day and night underground or indoors. Level -> the group whose look it keeps (fixed, no clock).\n'
    '    const UNDER = { 48: "Caves", 4: "Fortress", 5: "Fortress", 15: "Ships & docks", 53: "Fortress", 57: "Fortress", 67: "City" };\n')
rep('      const g = byLevel[n], day = g === "Helm\'s Deep" ? looks.Fortress : looks[g] || looks.level;\n'
    '      if (FIXED[g]) return Object.assign({}, looks[g], { SunDX: 0.25, SunDY: 0.32, Warm: 0 });\n',
    '      const g = byLevel[n], day = g === "Helm\'s Deep" ? looks.Fortress : looks[g] || looks.level;\n'
    '      if (UNDER[n]) return Object.assign({}, looks[UNDER[n]], { SunDX: 0.25, SunDY: 0.32, Warm: 0 });\n'
    '      if (FIXED[g]) return Object.assign({}, looks[g], { SunDX: 0.25, SunDY: 0.32, Warm: 0 });\n')
rep('    return { looks, sunNow, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled, nightness, names: byLevel, tick, playTime: () => playT };\n',
    '    const under = (n) => !!(UNDER[n] || FIXED[byLevel[n]] && (byLevel[n] === "Caves" || byLevel[n] === "Dwarf halls"));\n'
    '    return { looks, sunNow, forLevel: (n) => looks[byLevel[n]] || looks.level, cycled, nightness, names: byLevel, tick, playTime: () => playT, under };\n')
rep('      LIGHT_LOOKS.tick(st === 1);\n'
    '      if (st === 1) window.__rotkLook = LIGHT_LOOKS.cycled(lv);\n',
    '      LIGHT_LOOKS.tick(st === 1);\n'
    '      if (st === 1 && window.__rotkWasMenu !== false && LIGHT_LOOKS.under(lv)) window.__rotkLookSnap = 1;   // v221: back underground, no fade\n'
    '      window.__rotkWasMenu = st !== 1;\n'
    '      if (st === 1) window.__rotkLook = LIGHT_LOOKS.cycled(lv);\n')
rep('      const ease = () => { const t = window.__rotkLook || LIGHT_LOOKS.looks.menu; for (const k in cur) {'
    ' if (Array.isArray(cur[k])) for (let j = 0; j < 3; j++) cur[k][j] += (t[k][j] - cur[k][j]) * 0.06; else cur[k] += (t[k] - cur[k]) * 0.06; } };\n',
    '      const ease = () => { const t = window.__rotkLook || LIGHT_LOOKS.looks.menu, e = window.__rotkLookSnap ? 1 : 0.06; window.__rotkLookSnap = 0; for (const k in cur) {'
    ' if (Array.isArray(cur[k])) for (let j = 0; j < 3; j++) cur[k][j] += (t[k][j] - cur[k][j]) * e; else cur[k] += (t[k] - cur[k]) * e; } };\n')
open(out, "w").write(s); print("ok v221 underground")
