# Play Room v242: stop maps snapping back ("rubber banding") in MOVE.
# 1. A drag follows only the finger that grabbed the map (a second finger within 0.3 s, before the map moved, still pinches). A second finger touching mid-drag used to switch to pinch
#    and drop the move without saving it, so the map jumped back at the next rebuild. Now the move is kept and saved
#    when the grabbing finger lifts, and extra fingers are ignored until then.
# 2. The camera's look-at height is kept across the rebuild after each drop, so the view doesn't dip and spring back.
# 3. The saved layout loaded from the account at start no longer overwrites moves made before it arrived.
# Usage: python3 world3d-v242.py index.html|world3d.js
import sys
p = sys.argv[1]; s = open(p).read()
def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (old[:70], s.count(old))
    s = s.replace(old, new)

# 3. late account load never undoes this session's moves
rep("""      if (JSON.stringify(m) !== JSON.stringify(OFF)) { OFF = m;""",
    """      if (offHist.length) docSave();
      else if (JSON.stringify(m) !== JSON.stringify(OFF)) { OFF = m;""")
# 2. keep the look-at height
rep("""keep = { cam: Object.assign({}, a.cam), hero: a.hero ? a.hero() : -1 };""",
    """keep = { cam: Object.assign({}, a.cam), hero: a.hero ? a.hero() : -1, ty: a.ty ? a.ty() : 0 };""")
rep("""if (keep) { const kp = keep; keep = null; touched = true; Object.assign(cam, kp.cam);""",
    """if (keep) { const kp = keep; keep = null; touched = true; ty = kp.ty || 0; Object.assign(cam, kp.cam);""")
rep("""hero: () => hero, moves:""", """hero: () => hero, ty: () => ty, moves:""")
# 1. drag owns one pointer
rep("""          g0 = { mode: "drag", l, k, hit: hitTop || hit, cx: k.cx, cz: k.cz, dx: 0, dz: 0 }; dragVis(k, true); return; }""",
    """          g0 = { mode: "drag", pid: ps[0].id, t0: performance.now(), l, k, hit: hitTop || hit, cx: k.cx, cz: k.cz, dx: 0, dz: 0 }; dragVis(k, true); return; }""")
rep("""      ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY, btn: e.button, shift: e.shiftKey });
      tap = ptrs.size === 1 ? { x: e.clientX, y: e.clientY, t: performance.now() } : null;
""", """      ptrs.set(e.pointerId, { id: e.pointerId, x: e.clientX, y: e.clientY, btn: e.button, shift: e.shiftKey });
      if (g0 && g0.mode === "drag") {   // a second finger right away = pinch/turn, not a drag; later, it waits
        if (performance.now() - g0.t0 < 300 && !g0.dx && !g0.dz) { const g = g0; g0 = null; g.dx = g.dz = 0; dragEnd(g); }
        else { tap = null; return; }
      }
      tap = ptrs.size === 1 ? { x: e.clientX, y: e.clientY, t: performance.now() } : null;
""")
rep("""      if (g0.mode === "drag" && ps.length === 1) {""", """      if (g0.mode === "drag") {
        if (e.pointerId !== g0.pid) return;""")
rep("""      if (g0 && g0.mode === "drag") { const g = g0; g0 = null; tap = null; ptrs.clear(); dragEnd(g); return; }""",
    """      if (g0 && g0.mode === "drag") { if (e.pointerId !== g0.pid) return; const g = g0; g0 = null; tap = null; ptrs.clear(); dragEnd(g); return; }""")
open(p, "w").write(s)
