"""Play Room v246 (Jordan, 2026-11-22: "Replace the fallback to the wide screen"; "I kind of like it when it does it very
subtle to give changes in elevation a depth kind of feel but it's too aggressive"; "Let's just focus on the current area").
Usage: wideview-v246.py playroom-v245.html out.html (engine ?v=246, relinked with link_main.cpp v246).

In the joined Isengard level (slot 51) the engine no longer drops to the native 240x160 picture near edges and
elevation changes: the margins are placed from the camera instead, and rotk_view_held() says so. The page then eases
a slight zoom in (about 6%, bottom edge kept so the HUD stays whole) instead of the full zoom to the small screen.
Other areas keep the old behaviour for now. Works in 1-player, P2 and online (all draw through WideHost)."""
import sys
src, out = sys.argv[1:3]
t = open(src).read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)

rep('"?v=245"', '"?v=246"')
rep('H.canvas = cv; H.nativeView = () => M._rotk_native_view();',
    'H.canvas = cv; H.nativeView = () => M._rotk_native_view(); H.viewHeld = () => M._rotk_view_held ? M._rotk_view_held() : 0;', 2)
rep('''          this.zoom = w >= 240 && h >= 160 ? Math.max(0, (this.zoom || 0) - dtZ / 350) : 0;''',
'''          // v246: margins placed from the camera (edges, elevation changes): a slight zoom for depth, not the small screen.
          let held = false; try { held = !!(this.viewHeld && this.viewHeld()); } catch (e) {}
          if (held) this.zHeldT = nowZ;
          const zT = w >= 240 && h >= 160 && nowZ - (this.zHeldT || -1e9) < 600 ? 0.3 : 0, z0 = this.zoom || 0;
          this.zoom = w >= 240 && h >= 160 ? (z0 > 0.3 ? Math.max(zT, z0 - dtZ / 350) : z0 < zT ? Math.min(zT, z0 + dtZ / 900) : Math.max(zT, z0 - dtZ / 900)) : 0;''')
# a slight zoom keeps the bottom edge (HUD whole); the full zoom keeps the middle as before, blended in between
rep('''sy = ((h - 160) >> 1) * ez,''', '''sy = (h - 160) * ez * (0.5 + 0.5 * Math.min(1, Math.max(0, (0.6 - (this.zoom || 0)) / 0.3))),''')
open(out, 'w').write(t)
print('ok', len(t))
