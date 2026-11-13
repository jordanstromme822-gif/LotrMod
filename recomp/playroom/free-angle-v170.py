# Free-angle joystick + Frodo's 16 facings (test). Patches a Play Room page (v169+):
#   python3 free-angle-v170.py in.html out.html fr16.bin turn16.bin
# fr16.bin = tools/turn16/gen16.py output (made from the game's own pictures: keep it out of the repo),
# turn16.bin = tools/turn16/build.py output.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
p, out, frp, tp = sys.argv[1:5]
s = open(p, encoding="utf-8").read()
fr = open(frp, "rb").read(); t = open(tp, "rb").read()
assert len(fr) <= 0x9E400 - 0x8A000 and len(t) <= 0x1000
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a))
    s = s.replace(a, b)
# 1. ROM: pictures in the freed German text bank, hook in the free 0x9F000 block (both unused by anything else).
rep("      // All four Bonus Maps paths open (tools/unlockpaths.py).",
    "      // Smooth 360-degree walking test (tools/turn16): Frodo's in-between facing pictures (0x8A000, freed German text bank)\n"
    "      // and the free-angle hook (0x9F000). Nothing runs them until the page points the hero's update at 0x0809F001.\n"
    '      game.set(hexBytes("%s"), 0x8A000); // in-between pictures (tools/turn16/gen16.py)\n'
    '      game.set(hexBytes("%s"), 0x9F000); // free-angle hook (tools/turn16/turn16.c)\n'
    "      window.__turn16 = true;\n"
    "      // All four Bonus Maps paths open (tools/unlockpaths.py)." % (fr.hex(), t.hex()))
# 2. Page code (top-level script scope, next to the engine-speed chip code).
js = open(os.path.join(HERE, "free-angle.js"), encoding="utf-8").read().rstrip("\n")
js = "\n".join(("  " + ln) if ln else "" for ln in js.split("\n"))
rep("  // Engine speed (Jordan, 2026-11-10: lift the GBA limits", js + "\n  // Engine speed (Jordan, 2026-11-10: lift the GBA limits")
# 3. Stick: in free mode, the exact angle goes to the game and the d-pad gets the matching one of 8 directions.
rep("""        const dd = Math.hypot(dx, dy);
        if (dd < 10) { setSector(-1); return; }""",
"""        const dd = Math.hypot(dx, dy);
        if (dd < 10) { setSector(-1); return; }
        if (window.__freeActive && window.__freeActive()) {
          const fa = Math.round(((Math.atan2(dx, -dy) * 128 / Math.PI) + 256)) % 256;   // 0 = up, clockwise
          setSector((window.__freeDir8(fa) + 6) % 8, fa);
          slice.style.transform = "rotate(" + (fa * 360 / 256) + "deg)";
          return;
        }""")
rep("""      const setSector = (sec) => {
        sector = sec; const on = sec >= 0 ? SECTOR_DIRS[sec] : [];""",
"""      const setSector = (sec, fa) => {
        try { window.__freeStick && window.__freeStick(sec >= 0 && fa !== undefined, fa | 0); } catch (e) {}
        sector = sec; const on = sec >= 0 ? SECTOR_DIRS[sec] : [];""")
# 4. Setup chip under Engine speed.
CHIP = '<button id="freeSetup" class="chip" type="button" style="display:block;margin:8px auto 0" onclick="window.__toggleFree&&__toggleFree()">Joystick: Free 360°</button>\n'
rep('<button id="cpuSetup"', CHIP + '    <button id="cpuSetup"')
open(out, "w", encoding="utf-8").write(s)
print("patched", len(s))
