# Play Room v241: JOIN mode in the 3D World. Tap JOIN, then tap maps to highlight them as a group you want connected.
# NEW starts another group (each group has its own colour), the group chip switches between groups, CLEAR empties the
# current group. Groups are saved with the layout (this device + the artifact db doc data/users/<id>/world3d-arrange,
# field `joins` = JSON [[level, ...], ...]) so Claude can read them. MOVE and JOIN are never on together.
# Usage: python3 world3d-v241.py index.html|world3d.js
import sys
p = sys.argv[1]; s = open(p).read()
def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (old[:70], s.count(old))
    s = s.replace(old, new)

# 1. saved groups next to the saved moves; one doc write carries both
rep("""  let offHist = [], arrDoc = null, arrOn = false, keep = null, lastMount = null;
  function offSave() {
    try { localStorage.setItem(ARR_KEY, JSON.stringify(OFF)); } catch (e) {}
    if (arrDoc) arrDoc.set({ moves: JSON.stringify(OFF), at: Date.now() }).catch(() => {});
  }
""", """  let offHist = [], arrDoc = null, arrOn = false, keep = null, lastMount = null;
  const JOIN_KEY = "w3d-joins-v1";   // v241: groups of screens the player wants connected
  let JG = []; try { JG = JSON.parse(localStorage.getItem(JOIN_KEY) || "[]") || []; } catch (e) { JG = []; }
  let joinOn = false, joinCur = 0;
  function docSave() { if (arrDoc) arrDoc.set({ moves: JSON.stringify(OFF), joins: JSON.stringify(JG.filter((g) => g.length)), at: Date.now() }).catch(() => {}); }
  function offSave() {
    try { localStorage.setItem(ARR_KEY, JSON.stringify(OFF)); } catch (e) {}
    docSave();
  }
  function joinSave() {
    try { localStorage.setItem(JOIN_KEY, JSON.stringify(JG)); } catch (e) {}
    docSave();
  }
""")
rep("""    if (d && d.moves) {
      let m = {}; try { m = JSON.parse(d.moves) || {}; } catch (e) {}
      if (JSON.stringify(m) !== JSON.stringify(OFF)) { OFF = m; try { localStorage.setItem(ARR_KEY, d.moves); } catch (e) {} if (cur && cur.api && lastMount) remount(); }
    } else if (Object.keys(OFF).length) offSave();
""", """    let jg = null; if (d && d.joins) { try { jg = JSON.parse(d.joins); } catch (e) {} }
    if (jg && Array.isArray(jg)) { JG = jg; joinCur = Math.min(joinCur, Math.max(0, JG.length - 1)); try { localStorage.setItem(JOIN_KEY, JSON.stringify(JG)); } catch (e) {} if (cur && cur.api && cur.api.joinDraw) cur.api.joinDraw(); }
    if (d && d.moves) {
      let m = {}; try { m = JSON.parse(d.moves) || {}; } catch (e) {}
      if (JSON.stringify(m) !== JSON.stringify(OFF)) { OFF = m; try { localStorage.setItem(ARR_KEY, d.moves); } catch (e) {} if (cur && cur.api && lastMount) remount(); }
      else if (!jg && JG.some((g) => g.length)) docSave();
    } else if (Object.keys(OFF).length || JG.some((g) => g.length)) docSave();
""")

# 2. CSS for the group chip
rep("""  #w3d .w-arr button:disabled{opacity:.4}
""", """  #w3d .w-arr button:disabled{opacity:.4}
  #w3d .w-arr button.grp{display:inline-flex;align-items:center;gap:6px}
  #w3d .w-arr button.grp i{width:10px;height:10px;border-radius:50%;box-shadow:0 0 0 1.5px #0d0b09,0 0 6px currentColor}
""")

# 3. JOIN button + bar
rep("""<button type="button" data-c="move" class="wide" aria-label="Arrange screens">MOVE</button>';""",
    """<button type="button" data-c="move" class="wide" aria-label="Arrange screens">MOVE</button><button type="button" data-c="join" class="wide" aria-label="Pick maps to connect">JOIN</button>';""")
rep("""    function arrUi() {
      const mb = ctl.querySelector('[data-c="move"]'); mb.classList.toggle("on", arrOn); arrBar.classList.toggle("on", arrOn);
""", """    const joinBar = document.createElement("div"); joinBar.className = "w-arr"; root.appendChild(joinBar);
    const JCOL = ["#ffd24a", "#4aa8ff", "#5ee07a", "#ff6a5a", "#c07bff", "#3fe0e0", "#ff9a3a", "#ff7ac8"];
    let joinMarks = [];
    function joinDraw() {   // a coloured glow and outline on every screen picked to be connected
      joinMarks.forEach((o) => { scene.remove(o); o.geometry.dispose(); o.material.dispose(); }); joinMarks = [];
      if (joinOn || JG.some((g) => g.length)) JG.forEach((g, gi) => g.forEach((l) => {
        const k = tiles[l]; if (!k) return; const col = new THREE.Color(JCOL[gi % JCOL.length]), cur = joinOn && gi === joinCur;
        const glow = new THREE.Mesh(new THREE.PlaneGeometry(k.w, k.d), new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: joinOn ? (cur ? 0.42 : 0.22) : 0.16, depthWrite: false }));
        glow.rotation.x = -Math.PI / 2; glow.position.set(k.cx, k.y + 0.12, k.cz); scene.add(glow); joinMarks.push(glow);
        const box = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(k.w + 0.6, 0.4, k.d + 0.6)), new THREE.LineBasicMaterial({ color: col }));
        box.position.set(k.cx, k.y + 0.2, k.cz); scene.add(box); joinMarks.push(box);
      }));
      joinUi(); dirty();
    }
    function joinUi() {
      ctl.querySelector('[data-c="join"]').classList.toggle("on", joinOn); joinBar.classList.toggle("on", joinOn);
      if (!JG.length) JG.push([]); if (joinCur >= JG.length) joinCur = JG.length - 1;
      const g = JG[joinCur] || [], c = JCOL[joinCur % JCOL.length];
      joinBar.innerHTML = '<span>Tap maps to connect</span><button type="button" class="grp" data-j="grp" style="color:' + c + '"><i style="background:' + c + '"></i><b style="color:#f3d27a">Group ' + (joinCur + 1) + " · " + g.length + (g.length === 1 ? " map" : " maps") + '</b></button><button type="button" data-j="new">NEW</button><button type="button" data-j="clear">CLEAR</button><button type="button" data-j="done">DONE</button>';
      joinBar.querySelector('[data-j="grp"]').disabled = JG.length < 2;
      joinBar.querySelector('[data-j="new"]').disabled = !g.length;
      joinBar.querySelector('[data-j="clear"]').disabled = !g.length;
    }
    function joinTap(l) {
      if (l < 0 || !tiles[l]) return;
      const g = JG[joinCur], had = g.indexOf(l) >= 0;
      JG.forEach((o) => { const i = o.indexOf(l); if (i >= 0) o.splice(i, 1); });
      if (!had) g.push(l);
      joinSave(); joinDraw();
    }
    joinBar.addEventListener("click", (e) => {
      const b = e.target.closest("[data-j]"); if (!b || b.disabled) return; e.preventDefault(); const r = b.dataset.j;
      if (r === "done") { joinOn = false; JG = JG.filter((g) => g.length); joinCur = 0; joinSave(); joinDraw(); return; }
      if (r === "grp") { JG = JG.filter((g, i) => g.length || i === joinCur); joinCur = (joinCur + 1) % JG.length; }
      else if (r === "new") { JG = JG.filter((g) => g.length); JG.push([]); joinCur = JG.length - 1; }
      else if (r === "clear") { JG[joinCur] = []; joinSave(); }
      joinDraw();
    });
    function arrUi() {
      const mb = ctl.querySelector('[data-c="move"]'); mb.classList.toggle("on", arrOn); arrBar.classList.toggle("on", arrOn);
""")
rep("""      else if (c === "move") { arrOn = !arrOn; arrUi(); if (arrOn) { showCard(-1); help.style.display = "none"; } return; }
""", """      else if (c === "move") { arrOn = !arrOn; if (arrOn && joinOn) { joinOn = false; joinDraw(); } arrUi(); if (arrOn) { showCard(-1); help.style.display = "none"; } return; }
      else if (c === "join") { joinOn = !joinOn; if (joinOn && arrOn) { arrOn = false; arrUi(); } if (joinOn) { showCard(-1); help.style.display = "none"; JG = JG.filter((g) => g.length); JG.push([]); joinCur = JG.length - 1; } else { JG = JG.filter((g) => g.length); joinCur = 0; } joinDraw(); return; }
""")
# MOVE's drag rebuilds the scene, so the marks follow the moved screens after a remount (drawn at mount below).
# 4. taps pick maps while JOIN is on
rep("""      if (tap && ptrs.size === 0 && performance.now() - tap.t < 450) { const l = pickAt(e.clientX, e.clientY); showCard(l === selL ? -1 : l); }
""", """      if (tap && ptrs.size === 0 && performance.now() - tap.t < 450) { const l = pickAt(e.clientX, e.clientY); if (joinOn) joinTap(l); else showCard(l === selL ? -1 : l); }
""")
# 5. api + draw on mount
rep("""arrange: (on) => { arrOn = !!on; arrUi(); } };""",
    """arrange: (on) => { arrOn = !!on; arrUi(); }, joins: () => JSON.parse(JSON.stringify(JG.filter((g) => g.length))), join: (on) => { if (!!on !== joinOn) ctl.querySelector('[data-c="join"]').click(); }, joinTap, joinDraw };""")
rep("""    arrUi(); applyCam(); dirty();
  }
""", """    arrUi(); joinDraw(); applyCam(); dirty();
  }
""")
open(p, "w").write(s)
