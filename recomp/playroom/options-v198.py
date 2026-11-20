"""Play Room v198: no options on the setup screen, best settings always (Jordan, 2026-11-19: "run the game at optimal max
setting ... remove all the extra options from the play room outside of the maps and play button").
Usage: options-v198.py live-page.html out.html (page only).
- Setup screen keeps Play game and Story map (Story / Bonus maps / Siege tabs). Chips removed: Skin (test), Graphics,
  Rich lighting, Joystick, Engine speed. The built-in game file card is hidden (the file picker still shows if the
  built-in file can't load).
- Fixed values, old saved choices ignored: Graphics High, Rich lighting On (G key no longer turns it off), Free 360
  joystick, Engine speed 1x (4x froze Helm's Deep), Skin test Off (seams, no visible gain).
- The automatic slow-phone step down (High -> Low -> plain) stays, but only for that game: it is no longer saved, so
  every new game starts at full quality again. Before, one slow moment kept Low forever."""
import sys
src, out = sys.argv[1:3]
t = open(src).read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)
import re
# setup chips
for cid in ['skinSetup', 'gfxSetup', 'lightSetup', 'freeSetup', 'cpuSetup']:
    m = re.findall(r'\n *<button id="%s"[^\n]*</button>' % cid, t); assert len(m) == 1, cid; t = t.replace(m[0], '')
rep('<span class="label">Game file</span>', '<span class="label" hidden>Game file</span>')
rep('<div class="drop ready" id="romBuiltIn" style="border-style:solid" hidden>', '<div class="drop ready" id="romBuiltIn" style="border-style:solid;display:none" hidden>')
# graphics: Low only for this game (auto step down), never saved
rep('''window.__gfxLow = () => { try { return localStorage.getItem("rotk-gfx") === "low"; } catch (e) { return !!window.__gfxLowMem; } };''',
    '''window.__gfxLow = () => !!window.__gfxLowMem;   // v198: always High at start; the slow check may step down for this game only''')
rep('''window.__gfxSet = (low, auto) => { window.__gfxLowMem = low; try { localStorage.setItem("rotk-gfx", low ? "low" : "high"); } catch (e) {} gfxShow();''',
    '''window.__gfxSet = (low, auto) => { window.__gfxLowMem = low; try { localStorage.removeItem("rotk-gfx"); } catch (e) {} gfxShow();''')
# lighting always on
rep('''const lightOn = () => { try { return localStorage.getItem("rotk-light") !== "0"; } catch (e) { return true; } };''',
    '''const lightOn = () => true;   // v198: always on''')
rep('''const lightSet = (on) => { try { localStorage.setItem("rotk-light", on ? "1" : "0"); } catch (e) {}''',
    '''const lightSet = (on) => { try { localStorage.removeItem("rotk-light"); } catch (e) {}''')
rep('''window.__toggleLight = () => lightSet(!lightOn());''', '''window.__toggleLight = () => {};''')
rep('''let lit = false; try { lit = !plain && !!glowP && localStorage.getItem("rotk-light") !== "0"; } catch (e) { lit = !plain && !!glowP; }''',
    '''const lit = !plain && !!glowP;   // v198: Rich lighting always on''')
# free 360 joystick always
rep('''const freeOn = () => { try { return localStorage.getItem("rotk-free") !== "0"; } catch (e) { return true; } };''',
    '''const freeOn = () => true;   // v198: always Free 360''')
rep('''window.__toggleFree = () => { try { localStorage.setItem("rotk-free", freeOn() ? "0" : "1"); } catch (e) {} freeLabel(); };''',
    '''window.__toggleFree = () => {};''')
# engine speed 1x
rep('''const cpuGet = () => { try { const v = parseInt(localStorage.getItem("rotk-cpu") || "100", 10); return CPU_STEPS.includes(v) ? v : 100; } catch (e) { return 100; } };''',
    '''const cpuGet = () => 100;   // v198: always 1x''')
rep('''window.__toggleCpu = () => { const v = CPU_STEPS[(CPU_STEPS.indexOf(cpuGet()) + 1) % CPU_STEPS.length]; try { localStorage.setItem("rotk-cpu", String(v)); } catch (e) {} cpuShow(); try { window.__applyCpu(); } catch (e) {} };''',
    '''window.__toggleCpu = () => {};''')
# skin test off
rep('''const SKIN = { on: (() => { try { return localStorage.getItem("rotk-skin") === "1"; } catch (e) { return false; } })(), map: null, img: null };''',
    '''const SKIN = { on: false, map: null, img: null };   // v198: Skin test off (no option)''')
rep('''window.__toggleSkin = () => { SKIN.on = !SKIN.on;''', '''window.__toggleSkin = () => { return;''')
open(out, 'w').write(t)
print('ok', len(t))
