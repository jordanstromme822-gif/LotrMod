// 3D World (Jordan, 2026-11-20: "a fully interactive interconnected 3d model of each character's campaign game maps,
// label game maps and areas ... I should be able to zoom out and see the full campaign as if they were connected").
// The Story map's first tab. Every screen of the game is a stone slab topped with its overhead picture (maps/t, the
// full picture maps/L once you are close or tap it), and the slabs are laid out as one world: each screen's exit sits
// against the screen it leads to, at that screen's way in (the exits and ways in the Story map read from the game, EE).
// Missions with no door between them (a story jump) continue from the far side of the screen. Gold roads are doors,
// dashed roads are story jumps. Pick a hero to light their path in story order with numbered missions; tap a screen
// for its card. v237: screens joined at an edge door have the in-between ground the game's seamless doors (v234)
// draw, blended from both screens' edges, so the world reads as one continuous land. One finger moves the map, two fingers zoom, turn and tilt; on PC drag, right-drag and the wheel.
// Data comes from the Story map (window.__smData). three.js r128 is lazy-loaded from lib/three.min.js.
(() => {
  const U = 100;                                   // picture pixels per world unit
  const GAP = 140, MARGIN = 60;                     // pixels between joined screens / any two screens
  const HERO_COL = ["#f1efe6", "#5b93f0", "#7fd49a", "#f2c230", "#e07b4f"];
  const HERO_TAB = [["All", ""], ["Gandalf", ""], ["Aragorn", "Legolas · Gimli"], ["Éowyn", ""], ["Frodo", "Sam"], ["Bonus", ""]];
  // How high each land sits (world units): mountains and Mordor up, rivers and fields low.
  const RISE = { "Crack of Doom": 9, "Mt Doom": 7, "Cirith Ungol": 6, "Orc Tower": 6.5, "Shelob's Lair": 4.5, "Morgul": 4, "Gorgoroth": 3.5,
    "White Mountains": 6, "Dimholt": 5, "Dunharrow": 4.5, "Paths of the Dead": 3.5, "Isengard": 2.5, "Rohan": 1.5, "Entwood": 2,
    "Hornburg": 3, "Minas Tirith": 5, "Balcony": 6, "Pelennor Beacon": 3, "Pelennor Battle": 1, "Pelennor Fields": 0.6, "Ithilien": 2,
    "Docks": 0.2, "Anduin River": 0, "Corsair Flagship": 0.3, "Ice Cave": 5, "Dwarf Halls": 1.5, "Amon Sul": 3 };

  let THREE = null, loading = null;
  function loadThree() {
    if (window.THREE) return Promise.resolve((THREE = window.THREE));
    if (loading) return loading;
    loading = new Promise((ok, no) => { const s = document.createElement("script"); s.src = "lib/three.min.js"; s.onload = () => ok((THREE = window.THREE)); s.onerror = () => { loading = null; no(new Error("three")); }; document.head.appendChild(s); });
    return loading;
  }

  // ---------- layout (plain numbers, no three.js) ----------
  function layout(D) {
    const { SZ, EE, HEROES, BONUS } = D;
    const T = {};
    Object.keys(SZ).forEach((k) => { const [w, h] = SZ[k]; T[k] = { l: +k, w, h, x: 0, y: 0, placed: false, grp: 0 }; });
    const exits = (l) => (EE[l] || []).filter((e) => e[0] === 1 && e[3] !== l && (e[3] !== 0 || l === 3) && T[e[3]]);
    const ents = (l) => (EE[l] || []).filter((e) => e[0] === 0);
    const seqs = HEROES.map((h) => [].concat(...h.m)).concat(BONUS.map((b) => b.s.map((v) => v[0])));
    const links = [], seen = {};
    const add = (a, b, real, e) => { const k = a + ">" + b; if (seen[k] || a === b || !T[a] || !T[b]) return; seen[k] = 1; links.push({ a, b, real, e }); };
    Object.keys(T).forEach((k) => exits(+k).forEach((e) => add(+k, e[3], true, e)));
    seqs.forEach((s) => s.forEach((l, i) => { if (i && !seen[s[i - 1] + ">" + l] && !seen[l + ">" + s[i - 1]]) add(s[i - 1], l, false); }));
    const edgeOf = (t, px, py) => { const d = [px, t.w - px, py, t.h - py]; return ["L", "R", "T", "B"][d.indexOf(Math.min(...d))]; };
    const OPP = { L: "R", R: "L", T: "B", B: "T" };
    const all = Object.values(T);
    const hit = (r) => all.some((o) => o.placed && o !== r.t && r.x < o.x + o.w + MARGIN && r.x + r.w + MARGIN > o.x && r.y < o.y + o.h + MARGIN && r.y + r.h + MARGIN > o.y);
    function joinPt(b, a, side) {
      const back = exits(b.l).find((e) => e[3] === a.l); if (back) return [back[1] * b.w / 1000, back[2] * b.h / 1000];
      const es = ents(b.l), sc = (e) => { const x = e[1] / 1000, y = e[2] / 1000; return side === "L" ? x : side === "R" ? 1 - x : side === "T" ? y : 1 - y; };
      if (es.length) { const e = es.slice().sort((p, q) => sc(p) - sc(q))[0]; if (sc(e) < 0.25) return [e[1] * b.w / 1000, e[2] * b.h / 1000]; }
      return side === "L" ? [0, b.h / 2] : side === "R" ? [b.w, b.h / 2] : side === "T" ? [b.w / 2, 0] : [b.w / 2, b.h];
    }
    // Put b against a's side (side = a's edge), with b's point (jx, jy) facing a's point (AX, AY); slide until it fits.
    function fit(b, a, side, AX, AY, jx, jy) {
      let bx, by;
      if (side === "R") { bx = a.x + a.w + GAP; by = AY - jy; } else if (side === "L") { bx = a.x - GAP - b.w; by = AY - jy; }
      else if (side === "B") { by = a.y + a.h + GAP; bx = AX - jx; } else { by = a.y - GAP - b.h; bx = AX - jx; }
      const horiz = side === "L" || side === "R", dx = side === "R" ? 1 : side === "L" ? -1 : 0, dy = side === "B" ? 1 : side === "T" ? -1 : 0;
      for (let push = 0; push < 40; push++) for (let k = 0; k < 44; k++) {
        const off = (k % 2 ? 1 : -1) * Math.ceil(k / 2) * 160;
        const r = { t: b, w: b.w, h: b.h, x: bx + dx * push * 300 + (horiz ? 0 : off), y: by + dy * push * 300 + (horiz ? off : 0) };
        if (!hit(r)) { b.x = r.x; b.y = r.y; b.placed = true; return; }
      }
      b.x = bx; b.y = by; b.placed = true;
    }
    function fromDoor(a, b, lk) {
      let ex, ey;
      if (lk.e) { ex = lk.e[1] * a.w / 1000; ey = lk.e[2] * a.h / 1000; }
      else { const en = ents(a.l)[0], ix = en ? en[1] * a.w / 1000 : 0, iy = en ? en[2] * a.h / 1000 : a.h / 2, s = OPP[edgeOf(a, ix, iy)];
        ex = s === "L" ? 0 : s === "R" ? a.w : a.w / 2; ey = s === "T" ? 0 : s === "B" ? a.h : a.h / 2; }
      const side = edgeOf(a, ex, ey), [jx, jy] = joinPt(b, a, OPP[side]);
      fit(b, a, side, a.x + ex, a.y + ey, jx, jy);
    }
    function intoDoor(b, a, e) {   // b's own exit leads into a (already placed)
      const ex = e[1] * b.w / 1000, ey = e[2] * b.h / 1000, bside = edgeOf(b, ex, ey), aside = OPP[bside];
      const [jx, jy] = joinPt(a, b, aside);
      // Mirror: b goes on a's aside, with b's exit facing a's way in.
      fit(b, a, aside, a.x + jx, a.y + jy, ex, ey);
    }
    const order = [];
    seqs.forEach((s) => s.forEach((l) => { if (T[l] && order.indexOf(l) < 0) order.push(l); }));
    Object.keys(T).forEach((k) => { if (order.indexOf(+k) < 0) order.push(+k); });
    let grp = 0, guard = 0;
    T[order[0]].placed = true;
    while (order.some((l) => !T[l].placed) && guard++ < 1000) {
      let did = false;
      for (const l of order) {
        const b = T[l]; if (b.placed) continue;
        const lk = links.filter((k) => k.b === l && T[k.a].placed).sort((p, q) => q.real - p.real)[0];
        if (lk) { fromDoor(T[lk.a], b, lk); b.grp = T[lk.a].grp; did = true; break; }
        const back = links.find((k) => k.a === l && k.real && T[k.b].placed);
        if (back) { intoDoor(b, T[back.b], back.e); b.grp = T[back.b].grp; did = true; break; }
      }
      if (!did) { const b = T[order.find((q) => !T[q].placed)]; b.placed = true; b.grp = ++grp; b.x = 0; b.y = 0; }
    }
    // Groups with no door to the story (the bonus maps) go in a row under the world.
    const box = (ts) => ({ x0: Math.min(...ts.map((t) => t.x)), y0: Math.min(...ts.map((t) => t.y)), x1: Math.max(...ts.map((t) => t.x + t.w)), y1: Math.max(...ts.map((t) => t.y + t.h)) });
    const main = box(all.filter((t) => !t.grp));
    let cx = main.x0;
    for (let g = 1; g <= grp; g++) {
      const ts = all.filter((t) => t.grp === g), bb = box(ts), dx = cx - bb.x0, dy = main.y1 + 2600 - bb.y0;
      ts.forEach((t) => { t.x += dx; t.y += dy; }); cx += bb.x1 - bb.x0 + 1400;
    }
    // Where each road leaves and arrives (picture pixels, world-absolute).
    const near = (t, px, py) => [Math.max(t.x, Math.min(t.x + t.w, px)), Math.max(t.y, Math.min(t.y + t.h, py))];
    links.forEach((k) => {
      const a = T[k.a], b = T[k.b];
      const pa = k.e ? [a.x + k.e[1] * a.w / 1000, a.y + k.e[2] * a.h / 1000] : near(a, b.x + b.w / 2, b.y + b.h / 2);
      const back = exits(b.l).find((e) => e[3] === a.l);
      let pb;
      if (back) pb = [b.x + back[1] * b.w / 1000, b.y + back[2] * b.h / 1000];
      else { const es = ents(b.l).map((e) => [b.x + e[1] * b.w / 1000, b.y + e[2] * b.h / 1000]); pb = es.length ? es.sort((p, q) => Math.hypot(p[0] - pa[0], p[1] - pa[1]) - Math.hypot(q[0] - pa[0], q[1] - pa[1]))[0] : near(b, pa[0], pa[1]); }
      k.pa = pa; k.pb = pb;
    });
    const B = box(all);
    return { T, links, seqs, B };
  }

  // ---------- look ----------
  const CSS = `
  #w3d{position:relative;flex:1;min-height:0;overflow:hidden;border-radius:10px;border:2px solid #b8893a;box-shadow:0 0 0 1px #2a1d10,inset 0 0 40px rgba(0,0,0,.6);
    background:radial-gradient(120% 70% at 50% 110%,rgba(240,130,50,.35),transparent 60%),linear-gradient(#141a2e,#2b2235 45%,#3a2a28 70%,#17120e);touch-action:none;user-select:none;-webkit-user-select:none}
  #w3d canvas{position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none}
  #w3d .w-lab{position:absolute;left:0;top:0;pointer-events:none;white-space:nowrap;will-change:transform}
  #w3d .w-lv{transform-origin:50% 100%;padding:3px 8px 3px;border-radius:3px;color:#2b1d10;font:600 12px/1.15 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;text-align:center;
    background:radial-gradient(ellipse at 40% 40%,#fbf1d4,#ecd9a8 60%,#cfae72);border:1.5px solid #a87a32;box-shadow:0 2px 6px rgba(0,0,0,.6)}
  #w3d .w-lv i{display:block;font:700 9px/1.2 var(--display,Georgia,serif);letter-spacing:.06em;text-transform:uppercase;color:#7a4c18;font-style:normal}
  #w3d .w-lv i.b{color:#9a1f1f}
  #w3d .w-lv.sel{border-color:#ffe08a;box-shadow:0 0 0 2px #f6c45a,0 0 12px rgba(255,190,80,.9)}
  #w3d .w-lv::after{content:"";position:absolute;left:50%;bottom:-6px;width:8px;height:8px;margin-left:-4px;background:#d8b25a;transform:rotate(45deg);border-right:1.5px solid #a87a32;border-bottom:1.5px solid #a87a32;z-index:-1}
  #w3d .w-rg{padding:4px 14px 5px;color:#f6dc94;font:700 15px/1.1 var(--display,Georgia,serif);letter-spacing:.08em;text-transform:uppercase;text-shadow:0 1px 3px #000;
    background:linear-gradient(90deg,rgba(16,26,51,.0),rgba(16,26,51,.92) 14%,rgba(29,44,82,.95) 50%,rgba(16,26,51,.92) 86%,rgba(16,26,51,0));border-top:1.5px solid rgba(199,154,62,.9);border-bottom:1.5px solid rgba(199,154,62,.9)}
  #w3d .w-ms{padding:2px 7px;border-radius:999px;font:800 10px/1.2 var(--ui,system-ui,sans-serif);color:#1a1208;letter-spacing:.04em}
  #w3d .w-hud{position:absolute;left:8px;top:8px;right:8px;display:flex;flex-wrap:wrap;gap:6px;pointer-events:none}
  #w3d .w-hud > *{pointer-events:auto}
  #w3d .w-chip{height:32px;padding:0 12px;border-radius:16px;border:1.5px solid #8a6a30;background:linear-gradient(#1c1a1f,#0d0c10);color:#efe4cc;font:700 13px/1 var(--display,Georgia,serif);letter-spacing:.03em;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
  #w3d .w-chip b{width:10px;height:10px;border-radius:50%;display:inline-block}
  #w3d .w-chip.on{border-color:#ffe08a;color:#ffe9a8;background:linear-gradient(#3b2c14,#1a1209);box-shadow:0 0 10px rgba(255,190,80,.6)}
  #w3d .w-ctl{position:absolute;right:8px;bottom:8px;display:grid;grid-template-columns:repeat(2,auto);gap:6px}
  @media (min-height:501px) and (max-aspect-ratio:1/1){#w3d .w-ctl{grid-template-columns:auto}}
  #w3d .w-ctl button{width:42px;height:42px;border-radius:50%;border:2px solid #d8b25a;background:radial-gradient(circle at 50% 30%,#2f2922,#16120f 60%,#0a0807);color:#f3ead6;font:700 18px/1 var(--display,Georgia,serif);cursor:pointer;
    box-shadow:0 0 0 2px #0d0b09,0 0 10px rgba(240,170,80,.3);display:grid;place-items:center;padding:0}
  #w3d .w-ctl button.wide{font-size:11px;letter-spacing:.02em}
  #w3d .w-card{position:absolute;left:8px;bottom:8px;width:min(330px,calc(100% - 70px));max-height:calc(100% - 64px);overflow:auto;padding:10px 12px;box-sizing:border-box;color:#2b1d10;
    font:500 13px/1.3 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;background:radial-gradient(ellipse at 30% 40%,#fbf1d4,#ecd9a8 60%,#d2b57a);border:2px solid #b8893a;border-radius:4px;
    box-shadow:0 0 0 1px #4a3415,inset 0 0 22px rgba(120,80,30,.45),0 4px 12px rgba(0,0,0,.6)}
  #w3d .w-card h3{margin:0 0 2px;font:700 18px/1.1 var(--display,Georgia,serif);color:#3b2410}
  #w3d .w-card .rg{font:700 10px/1.2 var(--display,Georgia,serif);letter-spacing:.08em;text-transform:uppercase;color:#7a4c18}
  #w3d .w-card p{margin:5px 0 0}
  #w3d .w-card .acts{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
  #w3d .w-card .acts button{height:30px;padding:0 12px;border-radius:15px;border:1.5px solid #c99a46;background:linear-gradient(#1c1a1f,#0d0c10);color:#f3d27a;font:700 12px/1 var(--display,Georgia,serif);cursor:pointer}
  #w3d .w-card .x{position:absolute;right:6px;top:4px;border:0;background:none;color:#6b4518;font:700 18px/1 sans-serif;cursor:pointer;padding:4px}
  #w3d .w-msg{position:absolute;inset:0;display:grid;place-items:center;color:#f3d98e;font:700 15px var(--display,Georgia,serif);text-align:center;padding:20px}
  #w3d .w-help{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);max-width:min(80%,420px);text-align:center;padding:6px 14px;border-radius:14px;background:rgba(10,8,6,.78);border:1px solid rgba(216,178,90,.6);color:#efe4cc;font:600 12px var(--ui,system-ui,sans-serif);pointer-events:none;transition:opacity .6s}
  #storyMap .sm-scroll.w3d-sc{overflow:hidden;display:flex;flex-direction:column}
  #storyMap .sm-tabs button{white-space:nowrap}
  @media (max-width:440px){#storyMap .sm-tabs{gap:4px}#storyMap .sm-tabs button{padding:0 9px;font-size:12.5px}}
  @media (max-height:500px){
    #w3d .w-chip{height:28px;padding:0 9px;font-size:11.5px}
    #w3d .w-ctl button{width:36px;height:36px;font-size:15px}
    #w3d .w-card{width:min(300px,calc(100% - 60px));padding:7px 10px;font-size:12px}
    #w3d .w-card h3{font-size:15px}
    #w3d .w-lv{font-size:10.5px;padding:2px 6px}
    #w3d .w-rg{font-size:12px}
  }`;

  let cur = null;   // the mounted view

  function mount(sc, D) {
    unmount();
    if (!document.getElementById("w3dCss")) { const st = document.createElement("style"); st.id = "w3dCss"; st.textContent = CSS; document.head.appendChild(st); }
    sc.classList.add("w3d-sc");
    const leg = sc.parentNode && sc.parentNode.querySelector(".sm-leg");
    if (leg) leg.innerHTML = '<span><b style="background:linear-gradient(90deg,#6f8a3a,#b9a063,#6f8a3a)"></b>Joined ground: walk straight on</span><span><b style="background:#e8b84a;height:5px;vertical-align:2px"></b>Door inside a screen</span><span><b style="background:repeating-linear-gradient(90deg,#cfc6b0 0 4px,transparent 4px 7px);height:3px;vertical-align:3px"></b>Story jump</span>';
    const root = document.createElement("div"); root.id = "w3d"; sc.appendChild(root);
    const msg = document.createElement("div"); msg.className = "w-msg"; msg.textContent = "Raising the world…"; root.appendChild(msg);
    const view = { root, dead: false };
    cur = view;
    loadThree().then(() => { if (view.dead) return; msg.remove(); build(view, D); }).catch(() => { msg.textContent = "The 3D world could not load. Check the connection and open the map again."; });
    return view;
  }
  function unmount() {
    if (!cur) return;
    const v = cur; cur = null; v.dead = true;
    if (v.stop) v.stop();
  }

  function build(view, D) {
    const { root } = view;
    const L = layout(D), { T, links, B } = L;
    const NAMES = D.NAMES, region = D.region;
    // Which heroes walk each screen, and where their missions start.
    const who = {}, mstart = {};
    D.HEROES.forEach((h, hi) => h.m.forEach((ms, mi) => ms.forEach((l, k) => { (who[l] = who[l] || []).push(hi); if (!k) (mstart[l] = mstart[l] || []).push([hi, mi + 1]); })));
    const bonusOf = {}; D.BONUS.forEach((b) => b.s.forEach((v) => { bonusOf[v[0]] = b.name; }));

    const W = () => root.clientWidth || 1, H = () => root.clientHeight || 1;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(W(), H(), false);
    root.insertBefore(renderer.domElement, root.firstChild);
    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x241d26, 260, 900);
    const camera = new THREE.PerspectiveCamera(45, W() / H(), 0.5, 4000);
    scene.add(new THREE.HemisphereLight(0xfff1d6, 0x2a2030, 0.95));
    const sun = new THREE.DirectionalLight(0xffd9a0, 0.65); sun.position.set(-1, 2, 1.2); scene.add(sun);
    const maxAniso = renderer.capabilities.getMaxAnisotropy();

    const cxW = (B.x0 + B.x1) / 2 / U, czW = (B.y0 + B.y1) / 2 / U, spanW = Math.max(B.x1 - B.x0, B.y1 - B.y0) / U;
    // Ground: dark stone with a faint gold grid.
    {
      const g = document.createElement("canvas"); g.width = g.height = 256; const c = g.getContext("2d");
      c.fillStyle = "#1b1714"; c.fillRect(0, 0, 256, 256);
      for (let i = 0; i < 900; i++) { c.fillStyle = "rgba(" + (Math.random() < 0.5 ? "255,230,190" : "0,0,0") + "," + (Math.random() * 0.05) + ")"; c.fillRect(Math.random() * 256, Math.random() * 256, 2 + Math.random() * 6, 2 + Math.random() * 6); }
      c.strokeStyle = "rgba(216,178,90,0.10)"; c.lineWidth = 2; c.strokeRect(0, 0, 256, 256);
      const tx = new THREE.CanvasTexture(g); tx.wrapS = tx.wrapT = THREE.RepeatWrapping; const S = spanW * 8; tx.repeat.set(S / 24, S / 24); tx.anisotropy = maxAniso;
      const gm = new THREE.Mesh(new THREE.PlaneGeometry(S, S), new THREE.MeshLambertMaterial({ map: tx, color: 0x8a7a68 }));
      gm.rotation.x = -Math.PI / 2; gm.position.set(cxW, -0.6, czW); scene.add(gm);
    }

    // Slabs.
    const side = new THREE.MeshLambertMaterial({ color: 0x4a4038 }), bottom = new THREE.MeshLambertMaterial({ color: 0x1a1512 });
    const loader = new THREE.TextureLoader();
    const W3X = { 76: 1 };   // v238: hand-built screens (game art re-laid), 3D World only
    const tiles = {}, pickables = [];
    const top = (l) => (RISE[region(l)] || 0) * 1 + 0.6;
    Object.values(T).forEach((t) => {
      const w = t.w / U, d = t.h / U, hgt = top(t.l) + 0.6;
      const mat = new THREE.MeshBasicMaterial({ color: 0x555555 });
      const geo = new THREE.BoxGeometry(w, hgt, d);
      const m = new THREE.Mesh(geo, [side, side, mat, bottom, side, side]);
      m.position.set(t.x / U + w / 2, hgt / 2 - 0.6, t.y / U + d / 2);
      m.userData.l = t.l; scene.add(m); pickables.push(m);
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0xc79a3e, transparent: true, opacity: 0.85 }));
      edges.position.copy(m.position); scene.add(edges);
      tiles[t.l] = { t, m, mat, edges, cx: t.x / U + w / 2, cz: t.y / U + d / 2, y: hgt - 0.6, w, d, full: false };
    });
    let loaded = 0;
    const thumbQ = Object.keys(tiles).map(Number);
    function loadThumb(l) {
      loader.load((W3X[l] ? "maps/x/t/L" : "maps/t/L") + l + ".webp", (tx) => { if (view.dead) { tx.dispose(); return; } tx.anisotropy = maxAniso;
        const k = tiles[l]; if (!k.full) { k.mat.map = tx; if (!k.dim) k.mat.color.set(0xffffff); k.mat.needsUpdate = true; } k.thumb = tx; loaded++; tryBridges(l); dirty(); }, undefined, () => {});
    }
    // Full pictures for the screens you are close to (at most 6 at once).
    const fullSet = [];
    function wantFull(l) {
      const k = tiles[l]; if (!k || k.full || k.fullLoading) return;
      k.fullLoading = true;
      loader.load((W3X[l] ? "maps/x/L" : "maps/L") + l + ".webp", (tx) => { k.fullLoading = false; if (view.dead) { tx.dispose(); return; }
        tx.anisotropy = maxAniso; tx.magFilter = THREE.NearestFilter;
        k.full = tx; k.mat.map = tx; k.mat.color.set(0xffffff); k.mat.needsUpdate = true; fullSet.push(l);
        while (fullSet.length > 6) { const o = tiles[fullSet.shift()]; if (o.full) { o.full.dispose(); o.full = false; o.mat.map = o.thumb || null; o.mat.needsUpdate = true; } }
        dirty(); }, undefined, () => { k.fullLoading = false; });
    }

    // Ground between joined screens (v237, as the game's seamless doors since v234): a door within 120 px of its
    // screen's edge leads straight across a gap to the next screen, and the gap is land made from both screens' own
    // edges, each 40 px edge strip mirrored outwards and the two blended across (more of each near its own side), as a
    // ramp from one screen's height to the other's. Doors inside a screen keep their gold arc.
    const EDGE_NEAR = 120, STRIP = 40, BK = 0.2;   // door-to-edge reach, strip width (map px), bridge texels per map px
    const bridges = [], bridged = {};
    const pairKey = (a, b) => Math.min(a, b) + "-" + Math.max(a, b);
    links.forEach((k) => {
      if (!k.real) return; const key = pairKey(k.a, k.b); if (bridged[key]) return;
      const A = T[k.a], Bt = T[k.b]; if (!A || !Bt) return;
      let side = null, g = 0;
      const ovY = Math.min(A.y + A.h, Bt.y + Bt.h) - Math.max(A.y, Bt.y), ovX = Math.min(A.x + A.w, Bt.x + Bt.w) - Math.max(A.x, Bt.x);
      if (Bt.x >= A.x + A.w && ovY > 0) { side = "R"; g = Bt.x - (A.x + A.w); } else if (Bt.x + Bt.w <= A.x && ovY > 0) { side = "L"; g = A.x - (Bt.x + Bt.w); }
      else if (Bt.y >= A.y + A.h && ovX > 0) { side = "B"; g = Bt.y - (A.y + A.h); } else if (Bt.y + Bt.h <= A.y && ovX > 0) { side = "T"; g = A.y - (Bt.y + Bt.h); }
      if (!side || g < 8 || g > 420) return;
      const ax = side === "L" || side === "R" ? 0 : 1, ov = ax ? ovX : ovY; if (ov < 80) return;
      const edge = side === "R" ? A.x + A.w : side === "L" ? A.x : side === "B" ? A.y + A.h : A.y;
      if (Math.abs(k.pa[ax] - edge) > EDGE_NEAR) return;
      bridged[key] = 1;
      bridges.push({ a: k.a, b: k.b, side, ax, gap: g, p0: Math.max(ax ? A.x : A.y, ax ? Bt.x : Bt.y), p1: Math.min(ax ? A.x + A.w : A.y + A.h, ax ? Bt.x + Bt.w : Bt.y + Bt.h), built: false });
    });
    const pixCache = {};
    function pix(l) {   // the screen's thumbnail as pixels, at BK texels per map pixel
      if (pixCache[l]) return pixCache[l];
      const k = tiles[l], im = k && k.thumb && k.thumb.image; if (!im || !im.width) return null;
      const w = Math.max(2, Math.round(k.t.w * BK)), h = Math.max(2, Math.round(k.t.h * BK)), c = document.createElement("canvas"); c.width = w; c.height = h;
      const cx = c.getContext("2d"); cx.drawImage(im, 0, 0, w, h);
      return (pixCache[l] = { d: cx.getImageData(0, 0, w, h).data, w, h });
    }
    const bridgeMats = [];
    function buildBridge(br) {
      const PA = pix(br.a), PB = pix(br.b); if (!PA || !PB) return;
      br.built = true;
      const A = T[br.a], Bt = T[br.b], ax = br.ax, sg = br.side === "R" || br.side === "B" ? 1 : -1;
      const G = Math.max(2, Math.round(br.gap * BK)), N = Math.max(2, Math.round((br.p1 - br.p0) * BK)), K = Math.max(1, Math.round(STRIP * BK));
      const mir = (v, n) => { v = ((v % (2 * n)) + 2 * n) % (2 * n); return v < n ? v : 2 * n - 1 - v; };
      // canvas: columns run with world x, rows with world z
      const W = ax ? N : G, H = ax ? G : N, c = document.createElement("canvas"); c.width = W; c.height = H;
      const cx = c.getContext("2d"), out = cx.createImageData(W, H), o = out.data;
      const at = (P, x, y) => { x = Math.max(0, Math.min(P.w - 1, x)); y = Math.max(0, Math.min(P.h - 1, y)); return (y * P.w + x) * 4; };
      const aOff = Math.round(((ax ? A.x : A.y)) * BK), bOff = Math.round(((ax ? Bt.x : Bt.y)) * BK), q0 = Math.round(br.p0 * BK);
      const aLen = ax ? PA.h : PA.w, bLen = ax ? PB.h : PB.w;
      for (let d = 0; d < G; d++) {
        const t = (d + 0.5) / G, w = t * t * (3 - 2 * t);
        const ia = mir(d, K), ib = mir(G - 1 - d, K);
        const aA = sg > 0 ? aLen - 1 - ia : ia, aB = sg > 0 ? ib : bLen - 1 - ib;
        for (let i = 0; i < N; i++) {
          const pa = q0 + i - aOff, pb = q0 + i - bOff;
          const sa = ax ? at(PA, pa, aA) : at(PA, aA, pa), sb = ax ? at(PB, pb, aB) : at(PB, aB, pb);
          const dd = sg > 0 ? d : G - 1 - d, row = ax ? dd : i, col = ax ? i : dd, q = (row * W + col) * 4;
          o[q] = PA.d[sa] + (PB.d[sb] - PA.d[sa]) * w; o[q + 1] = PA.d[sa + 1] + (PB.d[sb + 1] - PA.d[sa + 1]) * w; o[q + 2] = PA.d[sa + 2] + (PB.d[sb + 2] - PA.d[sa + 2]) * w; o[q + 3] = 255;
        }
      }
      cx.putImageData(out, 0, 0);
      const tx = new THREE.CanvasTexture(c); tx.anisotropy = maxAniso;
      // A ramp from A's top to B's top, with stone sides down to the ground.
      const yA = tiles[br.a].y, yB = tiles[br.b].y;
      const e0 = (sg > 0 ? (ax ? A.y + A.h : A.x + A.w) : (ax ? A.y : A.x)) / U, e1 = e0 + sg * br.gap / U, s0 = br.p0 / U, s1 = br.p1 / U;
      const P = (e, s, y) => ax ? [s, y, e] : [e, y, s];
      const lo = Math.min(e0, e1), hi = Math.max(e0, e1), yLo = e0 < e1 ? yA : yB, yHi = e0 < e1 ? yB : yA;
      // corners: (lo,s0) (hi,s0) (lo,s1) (hi,s1); uv: world x -> u, world z -> 1 - v
      const pos = [], uv = [], idx = [];
      const corner = (e, s, y) => { pos.push(...P(e, s, y)); const wx = ax ? s : e, wz = ax ? e : s; const x0 = ax ? s0 : lo, x1 = ax ? s1 : hi, z0 = ax ? lo : s0, z1 = ax ? hi : s1; uv.push((wx - x0) / (x1 - x0), 1 - (wz - z0) / (z1 - z0)); };
      corner(lo, s0, yLo); corner(hi, s0, yHi); corner(lo, s1, yLo); corner(hi, s1, yHi);
      idx.push(0, 2, 1, 1, 2, 3);
      const geo = new THREE.BufferGeometry(); geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2)); geo.setIndex(idx); geo.computeVertexNormals();
      const mat = new THREE.MeshBasicMaterial({ map: tx, side: THREE.DoubleSide });
      const m = new THREE.Mesh(geo, mat); scene.add(m);
      // stone sides at both ends of the span
      const sp = [], si = [];
      [s0, s1].forEach((s) => { const b = sp.length / 3; sp.push(...P(lo, s, yLo), ...P(hi, s, yHi), ...P(lo, s, -0.6), ...P(hi, s, -0.6)); si.push(b, b + 1, b + 2, b + 1, b + 3, b + 2); });
      const sg2 = new THREE.BufferGeometry(); sg2.setAttribute("position", new THREE.Float32BufferAttribute(sp, 3)); sg2.setIndex(si); sg2.computeVertexNormals();
      const sm = new THREE.Mesh(sg2, new THREE.MeshLambertMaterial({ color: 0x4a4038, side: THREE.DoubleSide })); scene.add(sm);
      br.mesh = m; br.mat = mat; br.tx = tx; bridgeMats.push(mat);
      if (br.dimmed) mat.color.set(0x3a3a3a);
      dirty();
    }
    const tryBridges = (l) => bridges.forEach((br) => { if (!br.built && (br.a === l || br.b === l)) buildBridge(br); });
    thumbQ.forEach(loadThumb);

    // Roads: gold arcs for doors, dashed pale arcs for story jumps.
    const roadMat = new THREE.MeshBasicMaterial({ color: 0xe8b84a }), jumpMat = new THREE.LineDashedMaterial({ color: 0xcfc6b0, dashSize: 1.2, gapSize: 0.9, transparent: true, opacity: 0.8 });
    const roads = [];
    function arc(pa, pb, ya, yb, lift) {
      const a = new THREE.Vector3(pa[0] / U, ya + 0.15, pa[1] / U), b = new THREE.Vector3(pb[0] / U, yb + 0.15, pb[1] / U);
      const m = a.clone().lerp(b, 0.5); m.y = Math.max(ya, yb) + lift + a.distanceTo(b) * 0.12;
      return new THREE.QuadraticBezierCurve3(a, m, b);
    }
    const doneRoad = {};
    links.forEach((k) => {
      const key = Math.min(k.a, k.b) + "-" + Math.max(k.a, k.b) + (k.real ? "r" : "j"); if (doneRoad[key]) return; doneRoad[key] = 1;
      const c = arc(k.pa, k.pb, tiles[k.a].y, tiles[k.b].y, 0.6);
      let o;
      if (k.real && bridged[pairKey(k.a, k.b)]) o = null;
      else if (k.real) o = new THREE.Mesh(new THREE.TubeGeometry(c, 24, 0.22, 6, false), roadMat);
      else { o = new THREE.Line(new THREE.BufferGeometry().setFromPoints(c.getPoints(40)), jumpMat); o.computeLineDistances(); }
      if (o) { scene.add(o); roads.push(o); }
      // A glowing gem where a door is.
      if (k.real) [k.pa, k.pb].forEach((p, i) => { const g = new THREE.Mesh(new THREE.OctahedronGeometry(0.45), new THREE.MeshBasicMaterial({ color: 0xffe08a })); g.position.set(p[0] / U, tiles[i ? k.b : k.a].y + 0.5, p[1] / U); scene.add(g); roads.push(g); });
    });

    // Hero paths (built when a hero is picked).
    let pathObjs = [];
    function clearPath() { pathObjs.forEach((o) => { scene.remove(o); o.geometry && o.geometry.dispose(); }); pathObjs = []; }
    function linkOf(a, b) { return links.find((k) => k.a === a && k.b === b) || links.find((k) => k.a === b && k.b === a && k.real); }
    function drawPath(seq, col) {
      const mat = new THREE.MeshBasicMaterial({ color: col });
      for (let i = 1; i < seq.length; i++) {
        const a = seq[i - 1], b = seq[i], k = linkOf(a, b); if (!k) continue;
        const fwd = k.a === a, pa = fwd ? k.pa : k.pb, pb = fwd ? k.pb : k.pa;
        // From the middle of a to its exit, over to b's way in, then to b's middle.
        const ta = tiles[a], tb = tiles[b];
        const pts = [];
        const seg = (c) => c.getPoints(16).forEach((p) => pts.push(p));
        seg(new THREE.LineCurve3(new THREE.Vector3(ta.cx, ta.y + 0.9, ta.cz), new THREE.Vector3(pa[0] / U, ta.y + 0.9, pa[1] / U)));
        if (bridged[pairKey(a, b)]) seg(new THREE.LineCurve3(new THREE.Vector3(pa[0] / U, ta.y + 0.9, pa[1] / U), new THREE.Vector3(pb[0] / U, tb.y + 0.9, pb[1] / U)));
        else seg(arc(pa, pb, ta.y + 0.75, tb.y + 0.75, 1.2));
        seg(new THREE.LineCurve3(new THREE.Vector3(pb[0] / U, tb.y + 0.9, pb[1] / U), new THREE.Vector3(tb.cx, tb.y + 0.9, tb.cz)));
        const tube = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 60, 0.32, 6, false), mat);
        scene.add(tube); pathObjs.push(tube);
      }
    }

    // ---------- labels ----------
    const labLayer = document.createElement("div"); labLayer.style.cssText = "position:absolute;inset:0;pointer-events:none;overflow:hidden"; root.appendChild(labLayer);
    const labs = [];
    Object.values(tiles).forEach((k) => {
      const l = k.t.l, e = document.createElement("div"); e.className = "w-lab w-lv";
      const boss = D.BOSS[l];
      e.innerHTML = (boss ? '<i class="b">' + boss + "</i>" : "") + NAMES[l];
      labLayer.appendChild(e);
      labs.push({ e, l, k, kind: "lv", w: 0, h: 0 });
    });
    // Region banners at the middle of each land's screens.
    const regs = {};
    Object.values(tiles).forEach((k) => { const r = bonusOf[k.t.l] && region(k.t.l) === "" ? bonusOf[k.t.l] : region(k.t.l); (regs[r] = regs[r] || []).push(k); });
    // Lands split in two places (Minas Tirith upper and lower city) get one banner per cluster.
    Object.keys(regs).forEach((r) => {
      const ks = regs[r], groups = [];
      ks.forEach((k) => { const g = groups.find((g) => g.some((o) => Math.hypot(o.cx - k.cx, o.cz - k.cz) < 90)); if (g) g.push(k); else groups.push([k]); });
      groups.forEach((g) => {
        const e = document.createElement("div"); e.className = "w-lab w-rg"; e.textContent = r; labLayer.appendChild(e);
        const x = g.reduce((s, k) => s + k.cx, 0) / g.length, z = g.reduce((s, k) => s + k.cz, 0) / g.length, y = Math.max(...g.map((k) => k.y)) + 4;
        const rad = Math.max(...g.map((k) => Math.hypot(k.cx - x, k.cz - z) + Math.max(k.w, k.d) / 2));
        labs.push({ e, kind: "rg", p: new THREE.Vector3(x, y, z), rad, ls: g.map((k) => k.t.l) });
      });
    });
    let msLabs = [];
    function setMissionLabs(hi) {
      msLabs.forEach((m) => m.e.remove()); msLabs = [];
      const list = [];
      if (hi >= 0 && hi < 4) D.HEROES[hi].m.forEach((ms, mi) => list.push([ms[0], "Mission " + (mi + 1), HERO_COL[hi]]));
      if (hi === 4) D.BONUS.forEach((b) => list.push([b.s[0][0], b.name, HERO_COL[4]]));
      list.forEach(([l, txt, col]) => { const k = tiles[l]; if (!k) return; const e = document.createElement("div"); e.className = "w-lab w-ms"; e.textContent = txt; e.style.background = col; e.style.boxShadow = "0 0 0 1.5px #1a1208, 0 0 10px " + col; labLayer.appendChild(e); msLabs.push({ e, kind: "ms", p: new THREE.Vector3(k.cx, k.y + 0.4, k.cz + k.d / 2), l }); });
    }

    // ---------- camera ----------
    const cam = { x: cxW, z: czW, dist: spanW * 1.15, az: 0, pol: 0.5 };
    const goal = Object.assign({}, cam);
    const DMIN = 6, DMAX = spanW * 3;
    let touched = false;
    let flying = false;
    // Look at the top of the screen under the middle of the view, so close up you look at the land, not into it.
    let ty = 0;
    const tileUnder = (x, z) => { for (const k of Object.values(tiles)) if (Math.abs(x - k.cx) <= k.w / 2 && Math.abs(z - k.cz) <= k.d / 2) return k; return null; };
    function applyCam() {
      const sp = Math.sin(cam.pol), cp = Math.cos(cam.pol);
      const k = cam.dist < 120 ? tileUnder(cam.x, cam.z) : null, want = k ? k.y * Math.min(1, (120 - cam.dist) / 60) : 0;
      ty += (want - ty) * 0.35; if (Math.abs(want - ty) > 0.01) flying = true;
      camera.position.set(cam.x + cam.dist * sp * Math.sin(cam.az), ty + cam.dist * cp, cam.z + cam.dist * sp * Math.cos(cam.az));
      camera.lookAt(cam.x, ty, cam.z);
      scene.fog.near = cam.dist * 1.6 + 40; scene.fog.far = cam.dist * 4.5 + 200;
    }
    function fitTo(ls, instant) {
      const ks = ls.map((l) => tiles[l]).filter(Boolean); if (!ks.length) return;
      const x0 = Math.min(...ks.map((k) => k.cx - k.w / 2)), x1 = Math.max(...ks.map((k) => k.cx + k.w / 2)), z0 = Math.min(...ks.map((k) => k.cz - k.d / 2)), z1 = Math.max(...ks.map((k) => k.cz + k.d / 2));
      const asp = W() / H(), span = Math.max((x1 - x0) / Math.max(asp, 0.3), z1 - z0);
      goal.x = (x0 + x1) / 2; goal.z = (z0 + z1) / 2; goal.dist = Math.min(DMAX, Math.max(DMIN * 2, span * 1.05 / (2 * Math.tan(22.5 * Math.PI / 180)) * 1.0));
      if (instant) Object.assign(cam, goal); flying = !instant; dirty();
    }

    // ---------- HUD ----------
    const hud = document.createElement("div"); hud.className = "w-hud"; root.appendChild(hud);
    let hero = -1;
    HERO_TAB.forEach((h, i) => {
      const b = document.createElement("button"); b.type = "button"; b.className = "w-chip" + (i === 0 ? " on" : ""); b.dataset.h = i - 1;
      b.innerHTML = (i ? '<b style="background:' + HERO_COL[i - 1] + '"></b>' : "") + h[0]; if (h[1]) b.title = h[0] + " (" + h[1] + " walk the same path)";
      hud.appendChild(b);
    });
    hud.addEventListener("click", (e) => { const b = e.target.closest("[data-h]"); if (!b) return; e.preventDefault(); pickHero(+b.dataset.h); });
    const ctl = document.createElement("div"); ctl.className = "w-ctl"; root.appendChild(ctl);
    ctl.innerHTML = '<button type="button" data-c="in" aria-label="Zoom in">+</button><button type="button" data-c="out" aria-label="Zoom out">−</button><button type="button" data-c="rl" aria-label="Turn left">⟲</button><button type="button" data-c="rr" aria-label="Turn right">⟳</button><button type="button" data-c="tilt" class="wide" aria-label="Tilt">3D</button><button type="button" data-c="all" class="wide" aria-label="Whole campaign">ALL</button>';
    ctl.addEventListener("click", (e) => {
      const b = e.target.closest("[data-c]"); if (!b) return; e.preventDefault(); touched = true; const c = b.dataset.c;
      if (c === "in") goal.dist = Math.max(DMIN, goal.dist / 1.6); else if (c === "out") goal.dist = Math.min(DMAX, goal.dist * 1.6);
      else if (c === "rl") goal.az += Math.PI / 4; else if (c === "rr") goal.az -= Math.PI / 4;
      else if (c === "tilt") { goal.pol = goal.pol > 0.3 ? 0.02 : 0.95; b.textContent = goal.pol > 0.3 ? "TOP" : "3D"; }
      else if (c === "all") { goal.az = 0; goal.pol = 0.5; fitTo(sel(hero)); }
      flying = true; dirty();
    });
    const help = document.createElement("div"); help.className = "w-help"; help.textContent = "Drag to move · pinch to zoom · twist to turn · two fingers up/down to tilt · tap a screen"; root.appendChild(help);
    setTimeout(() => { help.style.opacity = "0"; }, 5000);
    if (!("ontouchstart" in window)) help.textContent = "Drag to move · wheel to zoom · right-drag to turn and tilt · click a screen";

    const sel = (h) => h < 0 ? Object.keys(tiles).map(Number) : h < 4 ? [].concat(...D.HEROES[h].m) : [].concat(...D.BONUS.map((b) => b.s.map((v) => v[0])));
    function pickHero(h) {
      hero = h;
      hud.querySelectorAll("[data-h]").forEach((b) => b.classList.toggle("on", +b.dataset.h === h));
      const on = new Set(sel(h));
      Object.values(tiles).forEach((k) => { const lit = h < 0 || on.has(k.t.l); k.mat.color.set(lit ? 0xffffff : 0x3a3a3a); k.edges.material.opacity = lit ? 0.85 : 0.2; k.dim = !lit; });
      roads.forEach((o) => { o.visible = h < 0; });
      bridges.forEach((br) => { br.dimmed = !!(tiles[br.a].dim || tiles[br.b].dim); if (br.mat) br.mat.color.set(br.dimmed ? 0x3a3a3a : 0xffffff); });
      clearPath();
      if (h >= 0 && h < 4) D.HEROES[h].m.forEach((ms) => drawPath(ms, HERO_COL[h]));
      if (h === 4) D.BONUS.forEach((b) => drawPath(b.s.map((v) => v[0]), HERO_COL[4]));
      if (h >= 0 && h < 4) for (let i = 1; i < D.HEROES[h].m.length; i++) { const a = D.HEROES[h].m[i - 1], b = D.HEROES[h].m[i]; drawPath([a[a.length - 1], b[0]], HERO_COL[h]); }
      setMissionLabs(h);
      goal.az = 0; goal.pol = 0.5; fitTo([...on]);
    }

    // ---------- card ----------
    let card = null, selL = -1, selMark = null;
    function showCard(l) {
      if (card) card.remove(); if (selMark) { scene.remove(selMark); selMark = null; }
      labs.forEach((o) => o.kind === "lv" && o.e.classList.toggle("sel", o.l === l));
      selL = l; if (l < 0) { card = null; dirty(); return; }
      const k = tiles[l];
      selMark = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(k.w + 0.5, 0.3, k.d + 0.5)), new THREE.LineBasicMaterial({ color: 0xffe08a }));
      selMark.position.set(k.cx, k.y + 0.2, k.cz); scene.add(selMark);
      wantFull(l);
      card = document.createElement("div"); card.className = "w-card";
      const hs = (who[l] || []).filter((v, i, a) => a.indexOf(v) === i).map((h) => D.HEROES[h].name + (D.HEROES[h].sub ? " " + D.HEROES[h].sub : ""));
      const ms = (mstart[l] || []).map(([h, m]) => D.HEROES[h].name + " mission " + m);
      const c = D.COUNTS[l], tot = c ? c[0] + c[1] + c[2] + c[3] : 0;
      const out = links.filter((q) => q.a === l && q.real).map((q) => NAMES[q.b]), inn = links.filter((q) => q.b === l && q.real).map((q) => NAMES[q.a]);
      card.innerHTML = '<button type="button" class="x" aria-label="Close">×</button><div class="rg">' + (region(l) || bonusOf[l] || "") + " · level " + l + "</div><h3>" + NAMES[l] + "</h3>" +
        (D.BOSS[l] ? "<p><b>Big fight:</b> " + D.BOSS[l] + "</p>" : "") +
        (ms.length ? "<p><b>Starts:</b> " + ms.join(", ") + "</p>" : "") +
        (hs.length ? "<p><b>Walked by:</b> " + hs.join(", ") + "</p>" : bonusOf[l] ? "<p><b>Bonus map:</b> " + bonusOf[l] + "</p>" : "") +
        (out.length ? "<p><b>Doors to:</b> " + [...new Set(out)].join(", ") + "</p>" : "") +
        (inn.length ? "<p><b>Reached from:</b> " + [...new Set(inn)].join(", ") + "</p>" : "") +
        (tot ? "<p><b>Enemies:</b> " + tot + (c[4] ? " + " + c[4] + " spawners" : "") + "</p>" : "") +
        '<div class="acts"><button type="button" data-a="fly">Fly here</button><button type="button" data-a="pic">Full picture</button></div>';
      card.addEventListener("click", (e) => {
        const a = e.target.closest("[data-a]"), x = e.target.closest(".x");
        if (x) { e.preventDefault(); showCard(-1); return; }
        if (!a) return; e.preventDefault();
        if (a.dataset.a === "pic" && D.pic) D.pic(l);
        if (a.dataset.a === "fly") { goal.x = k.cx; goal.z = k.cz; goal.dist = Math.max(DMIN, Math.max(k.w, k.d) * 1.6); goal.pol = 0.7; flying = true; dirty(); }
      });
      root.appendChild(card); dirty();
    }

    // ---------- input ----------
    const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    function groundAt(px, py) {
      const r = renderer.domElement.getBoundingClientRect();
      ndc.set(((px - r.left) / r.width) * 2 - 1, -((py - r.top) / r.height) * 2 + 1); ray.setFromCamera(ndc, camera);
      const p = new THREE.Vector3(); return ray.ray.intersectPlane(plane, p) ? p : null;
    }
    function pickAt(px, py) {
      const r = renderer.domElement.getBoundingClientRect();
      ndc.set(((px - r.left) / r.width) * 2 - 1, -((py - r.top) / r.height) * 2 + 1); ray.setFromCamera(ndc, camera);
      const h = ray.intersectObjects(pickables, false)[0]; return h ? h.object.userData.l : -1;
    }
    const ptrs = new Map(); let g0 = null, tap = null;
    const cvs = renderer.domElement;
    function gestureStart() {
      const ps = [...ptrs.values()];
      if (ps.length === 1) g0 = { mode: ps[0].btn === 2 || ps[0].shift ? "orbit" : "pan", x: ps[0].x, y: ps[0].y, cam: Object.assign({}, cam), hit: groundAt(ps[0].x, ps[0].y) };
      else if (ps.length >= 2) { const [a, b] = ps; g0 = { mode: "two", d: Math.hypot(a.x - b.x, a.y - b.y), ang: Math.atan2(b.y - a.y, b.x - a.x), my: (a.y + b.y) / 2, mx: (a.x + b.x) / 2, cam: Object.assign({}, cam) }; }
    }
    cvs.addEventListener("pointerdown", (e) => {
      e.preventDefault(); touched = true; cvs.setPointerCapture && cvs.setPointerCapture(e.pointerId);
      ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY, btn: e.button, shift: e.shiftKey });
      tap = ptrs.size === 1 ? { x: e.clientX, y: e.clientY, t: performance.now() } : null;
      flying = false; Object.assign(goal, cam); gestureStart();
    });
    cvs.addEventListener("pointermove", (e) => {
      const p = ptrs.get(e.pointerId); if (!p) return; p.x = e.clientX; p.y = e.clientY;
      if (tap && Math.hypot(e.clientX - tap.x, e.clientY - tap.y) > 8) tap = null;
      const ps = [...ptrs.values()];
      if (!g0) return;
      if (g0.mode === "pan" && ps.length === 1) {
        // Keep the grabbed ground point under the finger.
        Object.assign(cam, g0.cam); applyCam(); const now = groundAt(p.x, p.y);
        if (now && g0.hit) { cam.x = g0.cam.x + (g0.hit.x - now.x); cam.z = g0.cam.z + (g0.hit.z - now.z); }
      } else if (g0.mode === "orbit" && ps.length === 1) {
        cam.az = g0.cam.az - (p.x - g0.x) * 0.008; cam.pol = Math.max(0.02, Math.min(1.25, g0.cam.pol - (p.y - g0.y) * 0.006));
      } else if (g0.mode === "two" && ps.length >= 2) {
        const [a, b] = ps, d = Math.hypot(a.x - b.x, a.y - b.y), ang = Math.atan2(b.y - a.y, b.x - a.x), my = (a.y + b.y) / 2, mx = (a.x + b.x) / 2;
        cam.dist = Math.max(DMIN, Math.min(DMAX, g0.cam.dist * g0.d / Math.max(d, 1)));
        cam.az = g0.cam.az + (ang - g0.ang);
        cam.pol = Math.max(0.02, Math.min(1.25, g0.cam.pol + (my - g0.my) * 0.005));
        // Move with the fingers' middle too.
        const k = cam.dist / H() * 1.0, dx = (mx - g0.mx) * k, dz = (my - g0.my) * k * 0;
        cam.x = g0.cam.x - (dx * Math.cos(cam.az) + dz * Math.sin(cam.az)); cam.z = g0.cam.z - (-dx * Math.sin(cam.az) + dz * Math.cos(cam.az));
      }
      Object.assign(goal, cam); dirty();
    });
    const up = (e) => {
      if (!ptrs.has(e.pointerId)) return; ptrs.delete(e.pointerId);
      if (tap && ptrs.size === 0 && performance.now() - tap.t < 450) { const l = pickAt(e.clientX, e.clientY); showCard(l === selL ? -1 : l); }
      tap = null; gestureStart(); if (!ptrs.size) g0 = null;
    };
    cvs.addEventListener("pointerup", up); cvs.addEventListener("pointercancel", up);
    cvs.addEventListener("contextmenu", (e) => e.preventDefault());
    cvs.addEventListener("wheel", (e) => {
      e.preventDefault(); touched = true;
      const before = groundAt(e.clientX, e.clientY);
      cam.dist = Math.max(DMIN, Math.min(DMAX, cam.dist * Math.exp(e.deltaY / (e.ctrlKey ? 120 : 400)))); applyCam();
      const after = groundAt(e.clientX, e.clientY); if (before && after) { cam.x += before.x - after.x; cam.z += before.z - after.z; }
      Object.assign(goal, cam); flying = false; dirty();
    }, { passive: false });
    ["gesturestart", "gesturechange"].forEach((n) => root.addEventListener(n, (e) => e.preventDefault()));
    const onKey = (e) => {
      const k = e.key, s = cam.dist * 0.08; let used = true;
      if (k === "ArrowLeft") { goal.x -= s * Math.cos(cam.az); goal.z += s * Math.sin(cam.az); } else if (k === "ArrowRight") { goal.x += s * Math.cos(cam.az); goal.z -= s * Math.sin(cam.az); }
      else if (k === "ArrowUp") { goal.x -= s * Math.sin(cam.az); goal.z -= s * Math.cos(cam.az); } else if (k === "ArrowDown") { goal.x += s * Math.sin(cam.az); goal.z += s * Math.cos(cam.az); }
      else if (k === "+" || k === "=") goal.dist = Math.max(DMIN, goal.dist / 1.3); else if (k === "-") goal.dist = Math.min(DMAX, goal.dist * 1.3);
      else if (k === "q") goal.az += 0.2; else if (k === "e") goal.az -= 0.2; else used = false;
      if (used) { e.preventDefault(); flying = true; dirty(); }
    };
    window.addEventListener("keydown", onKey);

    // ---------- frame ----------
    let need = true, raf = 0;
    function dirty() { need = true; if (!raf && !view.dead) raf = requestAnimationFrame(frame); }
    const v3 = new THREE.Vector3();
    function placeLabels() {
      const w = W(), h = H(), f = h / (2 * Math.tan(22.5 * Math.PI / 180));
      const shown = [];
      const proj = (p) => { v3.copy(p).project(camera); return v3.z < 1 && v3.z > -1 ? [(v3.x + 1) / 2 * w, (1 - v3.y) / 2 * h] : null; };
      const fits = (x, y, ww, hh) => { const r = [x - ww / 2 - 2, y - hh - 2, x + ww / 2 + 2, y + 2]; if (shown.some((o) => r[0] < o[2] && r[2] > o[0] && r[1] < o[3] && r[3] > o[1])) return false; shown.push(r); return true; };
      const hide = (o) => { if (o.vis !== false) { o.e.style.display = "none"; o.vis = false; } };
      const show = (o, x, y) => { if (o.vis !== true) { o.e.style.display = ""; o.vis = true; } o.e.style.transform = "translate(" + Math.round(x - o.w / 2) + "px," + Math.round(y - o.h) + "px)"; };
      const measure = (o) => { if (!o.w) { o.e.style.display = ""; o.w = o.e.offsetWidth; o.h = o.e.offsetHeight; o.vis = true; } };
      // Mission markers first, then region banners while zoomed out, then screen names by size on screen.
      msLabs.forEach((o) => { measure(o); const s = proj(o.p); if (!s || !fits(s[0], s[1] - 4, o.w, o.h)) hide(o); else show(o, s[0], s[1] - 4); });
      const items = labs.map((o) => {
        if (o.kind === "rg") { const dd = camera.position.distanceTo(o.p), px = o.rad * 2 / dd * f; return { o, p: o.p, pri: px > w * 0.9 ? -1 : 1e6 - px, rg: true, px }; }
        const k = o.k; v3.set(k.cx, k.y + 0.4, k.cz); const dd = camera.position.distanceTo(v3), px = Math.max(k.w, k.d) / dd * f;
        if (k.dim || px < 34) return { o, pri: -1 };
        return { o, p: new THREE.Vector3(k.cx, k.y + 0.4, k.cz), pri: px + (o.l === selL ? 1e7 : 0) };
      });
      // Zoomed out: lands first. Zoomed in (a land fills the view): its screens first.
      items.sort((a, b) => b.pri - a.pri);
      items.forEach((it) => {
        const o = it.o; if (it.pri < 0) { hide(o); return; }
        if (it.rg && hero >= 0) { const on = new Set(sel(hero)); if (!o.ls.some((l) => on.has(l))) { hide(o); return; } }
        measure(o); const s = proj(it.p); if (!s || s[0] < -50 || s[0] > w + 50 || s[1] < -20 || s[1] > h + 60) { hide(o); return; }
        if (it.rg && it.px < 26) { hide(o); return; }
        if (!fits(s[0], s[1], o.w, o.h)) { hide(o); return; }
        show(o, s[0], s[1]);
      });
    }
    function frame() {
      raf = 0; if (view.dead) return;
      if (flying) {
        let moving = false; const ease = 0.16;
        ["x", "z", "dist", "az", "pol"].forEach((q) => { const d = goal[q] - cam[q]; if (Math.abs(d) > (q === "dist" ? 0.01 : 0.0005)) { cam[q] += d * ease; moving = true; } else cam[q] = goal[q]; });
        if (!moving) flying = false;
        need = true;
      }
      if (need) {
        need = false; applyCam(); renderer.render(scene, camera); placeLabels();
        // Close up: swap in the full pictures of the screens in the middle of the view.
        if (cam.dist < 40) { const l = pickAt(root.getBoundingClientRect().left + W() / 2, root.getBoundingClientRect().top + H() / 2); if (l >= 0) wantFull(l); }
      }
      if (flying) raf = requestAnimationFrame(frame);
    }
    const ro = new ResizeObserver(() => { renderer.setSize(W(), H(), false); camera.aspect = W() / H(); camera.updateProjectionMatrix(); if (!touched) fitTo(sel(hero), true); dirty(); });
    ro.observe(root);
    view.stop = () => {
      cancelAnimationFrame(raf); ro.disconnect(); window.removeEventListener("keydown", onKey);
      scene.traverse((o) => { if (o.geometry) o.geometry.dispose(); });
      Object.values(tiles).forEach((k) => { k.thumb && k.thumb.dispose(); k.full && k.full.dispose(); k.mat.dispose(); });
      bridges.forEach((br) => { br.tx && br.tx.dispose(); br.mat && br.mat.dispose(); });
      renderer.dispose(); if (renderer.forceContextLoss) renderer.forceContextLoss(); root.remove();
    };
    view.api = { pickHero, showCard, fitTo, cam, goal, tiles, layout: L, dirty, bridges };
    fitTo(sel(-1), true); applyCam(); dirty();
  }

  window.World3D = { mount, unmount, layout, get view() { return cur; } };
})();
