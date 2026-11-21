# Play Room v239: Arrange mode in the 3D World. A MOVE button lets you drag any screen to slide it; on release the
# joined ground and doors are rebuilt around the new place. Moves are saved per player (this device right away, and
# the artifact db doc data/users/<id>/world3d-arrange so it follows you and Claude can read it). UNDO and RESET.
# Only the 3D World uses the moves: World3D.layout() (read by the in-game seamless doors) is unchanged.
# Usage: python3 world3d-v239.py index.html|world3d.js
import sys
p = sys.argv[1]; s = open(p).read()
def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (old[:60], s.count(old))
    s = s.replace(old, new)

# 1. module state: saved moves + how to remount keeping the camera
rep("  let cur = null;   // the mounted view\n",
"""  let cur = null;   // the mounted view
  // ---------- v239 arrange: player's own moves of screens, in map px {l: [dx, dy]} ----------
  const ARR_KEY = "w3d-arrange-v1";
  let OFF = {}; try { OFF = JSON.parse(localStorage.getItem(ARR_KEY) || "{}") || {}; } catch (e) { OFF = {}; }
  let offHist = [], arrDoc = null, arrOn = false, keep = null, lastMount = null;
  function offSave() {
    try { localStorage.setItem(ARR_KEY, JSON.stringify(OFF)); } catch (e) {}
    if (arrDoc) arrDoc.set({ moves: JSON.stringify(OFF), at: Date.now() }).catch(() => {});
  }
  (async () => {
    const use = window.claude && window.claude.use; if (!use) return;
    const [db, user] = await Promise.all([use("db"), use("user")]); if (!db || !user) return;
    const id = await user.id(); if (!id) return;
    arrDoc = db.doc("data/users/" + id + "/world3d-arrange");
    const snap = await arrDoc.get().catch(() => null), d = snap && (snap.data ? snap.data() : snap);
    if (d && d.moves) {
      let m = {}; try { m = JSON.parse(d.moves) || {}; } catch (e) {}
      if (JSON.stringify(m) !== JSON.stringify(OFF)) { OFF = m; try { localStorage.setItem(ARR_KEY, d.moves); } catch (e) {} if (cur && cur.api && lastMount) remount(); }
    } else if (Object.keys(OFF).length) offSave();
  })().catch(() => {});
  function shifted(L0) {   // the layout with the player's moves applied (copies; World3D.layout stays as the game uses it)
    const T = {}; Object.keys(L0.T).forEach((k) => { const t = Object.assign({}, L0.T[k]), o = OFF[k]; if (o) { t.x += o[0]; t.y += o[1]; } T[k] = t; });
    const mv = (l, p) => { const o = OFF[l]; return o && p ? [p[0] + o[0], p[1] + o[1]] : p; };
    const links = L0.links.map((k) => Object.assign({}, k, { pa: mv(k.a, k.pa), pb: mv(k.b, k.pb) }));
    const ts = Object.values(T), B = { x0: Math.min(...ts.map((t) => t.x)), y0: Math.min(...ts.map((t) => t.y)), x1: Math.max(...ts.map((t) => t.x + t.w)), y1: Math.max(...ts.map((t) => t.y + t.h)) };
    return Object.assign({}, L0, { T, links, B });
  }
  function remount() {
    const v = cur; if (!v || !v.api || !lastMount) return;
    const a = v.api; keep = { cam: Object.assign({}, a.cam), hero: a.hero ? a.hero() : -1 };
    mount(lastMount[0], lastMount[1]);
  }
""")
rep("  function mount(sc, D) {\n    unmount();\n", "  function mount(sc, D) {\n    unmount(); lastMount = [sc, D];\n")
rep("    const L = layout(D), { T, links, B } = L;", "    const L = shifted(layout(D)), { T, links, B } = L;")

# 2. CSS for the arrange bar
rep("  #storyMap .sm-scroll.w3d-sc{",
"""  #w3d .w-ctl button.on{background:radial-gradient(circle at 50% 30%,#7a5a22,#3a2a10 60%,#1a1208);color:#fff3c8;box-shadow:0 0 0 2px #0d0b09,0 0 14px rgba(255,200,90,.8)}
  #w3d .w-arr{position:absolute;left:8px;bottom:8px;max-width:calc(100% - 74px);box-sizing:border-box;display:none;flex-wrap:wrap;align-items:center;gap:6px;padding:6px 8px 6px 12px;border-radius:16px;background:rgba(14,11,8,.9);border:1.5px solid #d8b25a;color:#f3e6c4;font:600 12px var(--ui,system-ui,sans-serif);z-index:3}
  #w3d .w-arr.on{display:flex}
  #w3d .w-arr button{height:28px;padding:0 11px;border-radius:14px;border:1.5px solid #c99a46;background:linear-gradient(#1c1a1f,#0d0c10);color:#f3d27a;font:700 11.5px/1 var(--display,Georgia,serif);cursor:pointer}
  #w3d .w-arr button:disabled{opacity:.4}
  #storyMap .sm-scroll.w3d-sc{""")

# 3. MOVE button + arrange bar
rep("""<button type="button" data-c="all" class="wide" aria-label="Whole campaign">ALL</button>';""",
"""<button type="button" data-c="all" class="wide" aria-label="Whole campaign">ALL</button><button type="button" data-c="move" class="wide" aria-label="Arrange screens">MOVE</button>';
    const arrBar = document.createElement("div"); arrBar.className = "w-arr"; root.appendChild(arrBar);
    arrBar.innerHTML = '<span>Drag a screen to slide it</span><button type="button" data-r="undo">UNDO</button><button type="button" data-r="reset">RESET</button><button type="button" data-r="done">DONE</button>';
    function arrUi() {
      const mb = ctl.querySelector('[data-c="move"]'); mb.classList.toggle("on", arrOn); arrBar.classList.toggle("on", arrOn);
      arrBar.querySelector('[data-r="undo"]').disabled = !offHist.length; arrBar.querySelector('[data-r="reset"]').disabled = !Object.keys(OFF).length;
    }
    arrBar.addEventListener("click", (e) => {
      const b = e.target.closest("[data-r]"); if (!b) return; e.preventDefault(); const r = b.dataset.r;
      if (r === "done") { arrOn = false; arrUi(); return; }
      if (r === "undo" && offHist.length) { OFF = offHist.pop(); offSave(); remount(); return; }
      if (r === "reset" && Object.keys(OFF).length) { offHist.push(JSON.parse(JSON.stringify(OFF))); OFF = {}; offSave(); remount(); }
    });""")
rep("""      else if (c === "all") { goal.az = 0; goal.pol = 0.5; fitTo(sel(hero)); }""",
"""      else if (c === "all") { goal.az = 0; goal.pol = 0.5; fitTo(sel(hero)); }
      else if (c === "move") { arrOn = !arrOn; arrUi(); if (arrOn) showCard(-1); return; }""")

# 4. dragging a screen in arrange mode
rep("""      if (ps.length === 1) g0 = { mode: ps[0].btn === 2 || ps[0].shift ? "orbit" : "pan", x: ps[0].x, y: ps[0].y, cam: Object.assign({}, cam), hit: groundAt(ps[0].x, ps[0].y) };""",
"""      if (ps.length === 1 && arrOn && ps[0].btn !== 2 && !ps[0].shift) {
        const l = pickAt(ps[0].x, ps[0].y), k = tiles[l];
        if (k) { const hit = groundAt(ps[0].x, ps[0].y); plane.constant = -k.y; const hitTop = groundAt(ps[0].x, ps[0].y); plane.constant = 0;
          g0 = { mode: "drag", l, k, hit: hitTop || hit, cx: k.cx, cz: k.cz, dx: 0, dz: 0 }; dragVis(k, true); return; }
      }
      if (ps.length === 1) g0 = { mode: ps[0].btn === 2 || ps[0].shift ? "orbit" : "pan", x: ps[0].x, y: ps[0].y, cam: Object.assign({}, cam), hit: groundAt(ps[0].x, ps[0].y) };""")
rep("""      if (g0.mode === "pan" && ps.length === 1) {""",
"""      if (g0.mode === "drag" && ps.length === 1) {
        plane.constant = -g0.k.y; const now = groundAt(p.x, p.y); plane.constant = 0;
        if (now && g0.hit) { const SN = 8 / U; g0.dx = Math.round((now.x - g0.hit.x) / SN) * SN; g0.dz = Math.round((now.z - g0.hit.z) / SN) * SN; dragMove(g0); }
        dirty(); return;
      } else if (g0.mode === "pan" && ps.length === 1) {""")
rep("""    const up = (e) => {
      if (!ptrs.has(e.pointerId)) return; ptrs.delete(e.pointerId);""",
"""    function dragVis(k, on) {   // while a screen moves: lift it, and hide the doors and joined ground (rebuilt on release)
      k.edges.material.color.set(on ? 0xfff0b0 : 0xc79a3e); roads.forEach((o) => { o.visible = !on && hero < 0; }); bridges.forEach((br) => { if (br.mesh) br.mesh.visible = !on; if (br.side3) br.side3.visible = !on; }); clearPath();
      if (selMark) selMark.visible = !on;
    }
    function dragMove(g) {
      const k = g.k; k.m.position.x = g.cx + g.dx; k.m.position.z = g.cz + g.dz; k.m.position.y = k.m.geometry.parameters.height / 2 - 0.6 + 0.8;
      k.edges.position.copy(k.m.position); k.cx = g.cx + g.dx; k.cz = g.cz + g.dz;
    }
    function dragEnd(g) {
      const dx = Math.round(g.dx * U), dy = Math.round(g.dz * U);
      if (!dx && !dy) { g.k.cx = g.cx; g.k.cz = g.cz; g.k.m.position.set(g.cx, g.k.m.geometry.parameters.height / 2 - 0.6, g.cz); g.k.edges.position.copy(g.k.m.position); dragVis(g.k, false); dirty(); return; }
      offHist.push(JSON.parse(JSON.stringify(OFF))); if (offHist.length > 40) offHist.shift();
      const o = OFF[g.l] || [0, 0]; OFF[g.l] = [o[0] + dx, o[1] + dy]; if (!OFF[g.l][0] && !OFF[g.l][1]) delete OFF[g.l];
      offSave(); remount();
    }
    const up = (e) => {
      if (!ptrs.has(e.pointerId)) return; ptrs.delete(e.pointerId);
      if (g0 && g0.mode === "drag") { const g = g0; g0 = null; tap = null; ptrs.clear(); dragEnd(g); return; }""")
# keep the stone sides of a bridge reachable so they hide during a drag
rep("const sm = new THREE.Mesh(sg2, new THREE.MeshLambertMaterial({ color: 0x4a4038, side: THREE.DoubleSide })); scene.add(sm);",
    "const sm = new THREE.Mesh(sg2, new THREE.MeshLambertMaterial({ color: 0x4a4038, side: THREE.DoubleSide })); scene.add(sm); br.side3 = sm;")
rep('setTimeout(() => { help.style.opacity = "0"; }, 5000);', 'setTimeout(() => { help.style.opacity = "0"; }, 5000); if (keep) help.style.display = "none";')
# 5. api + restoring the camera, hero and arrange mode after a remount
rep("    view.api = { pickHero, showCard, fitTo, cam, goal, tiles, layout: L, dirty, bridges };\n    fitTo(sel(-1), true); applyCam(); dirty();",
"""    view.api = { pickHero, showCard, fitTo, cam, goal, tiles, layout: L, dirty, bridges, hero: () => hero, moves: () => JSON.parse(JSON.stringify(OFF)), arrange: (on) => { arrOn = !!on; arrUi(); } };
    if (keep) { const kp = keep; keep = null; touched = true; Object.assign(cam, kp.cam); Object.assign(goal, kp.cam); if (kp.hero >= 0) pickHero(kp.hero); }
    else fitTo(sel(-1), true);
    arrUi(); applyCam(); dirty();""")
open(p, "w").write(s)
print("v239 applied")
