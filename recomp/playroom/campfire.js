// Campfire travel (plan Phase 2: "Campsites unlock when you enter their area after its quest, then act as fast-travel
// points"; "Changing regions and campfire travel are the only black screens, with the region's name banner as it loads").
//
// Every campsite has the game's own campfire (spawn record 0x11 of kind 1). The story only brings a hero to an area's
// campsite once that area's quest is behind them, so reaching a campfire lights it for that hero: a gold banner says
// so, and it is kept for that saved hero (this device and the account). Standing by any lit campfire shows a Travel
// button; it opens the list of the hero's lit campfires, and picking one dims the screen under that place's name while
// the game's own level change takes the hero (and P2) there, to the fireside (in a region, the region's campfire entry:
// tools/region/pack.py entry 2). Page only. v275: online too (both games change level on the same frame, as through a
// door); the 2-player online test is tools/test/online-pair.js.
(() => {
  // [id, level the fire is in, fire x, fire y, level to travel to, its entry]  (fires from the levels' 0x11 records)
  const CAMPS = [
    ["anduin", 1, 149, 377, 1, 0],
    ["cirith", 7, 236, 507, 7, 0],
    ["dimholt", 19, 431, 445, 19, 0],          // no fire record: the arrival spot stands in
    ["doom", 26, 228, 411, 26, 0],
    ["dunharrow", 31, 370, 429, 31, 0],
    ["entwood", 36, 60, 378, 36, 0],
    ["gorgoroth", 40, 66, 230, 40, 0],
    ["isengard", 51, 4357, 4685, 51, 2],       // the Isengard region's Campsite (region px)
    ["isengard", 50, 325, 205, 51, 2],         // the old Campsite map, if a door still leads there
    ["morgul", 75, 47, 298, 75, 0],
    ["dead", 86, 172, 519, 86, 0],
    ["pelennor", 100, 201, 125, 100, 0],
    ["rohan", 108, 333, 449, 108, 0],
    ["whitemts", 123, 227, 149, 123, 0],
  ];
  const NEAR = 64, FOUND = 420;   // px from the fire: the Travel button shows / in a region, the campfire is lit (a campsite's own map lights it on entering)
  const KEY = "rotk-campfires";
  const REGIONS = new Set(window.__regionLevels || [51]);
  const regionName = (l) => { try { const D = window.__smData; return (D && D.region && D.region(l)) || ""; } catch (e) { return ""; } };
  const placeName = (l) => { try { const D = window.__smData; return (D && D.NAMES && D.NAMES[l]) || "Campsite"; } catch (e) { return "Campsite"; } };
  const campOf = (id) => CAMPS.find((c) => c[0] === id);
  const title = (c) => regionName(c[1]) || placeName(c[1]);

  // ---- memory -----------------------------------------------------------------------------------------------------
  const mem = () => {
    const mp = window.__mp, M = mp && mp.M; if (!M || !M.HEAPU8) return null;
    let iw = -1, ew = -1;
    try { iw = mp.iwram(); ew = mp.ewram ? mp.ewram() : M._rotk_ewram ? M._rotk_ewram() : -1; } catch (e) { return null; }
    if (!(iw > 0)) return null;
    const H8 = M.HEAPU8;
    const at = (a) => a >= 0x03000000 ? iw + (a & 0x7fff) : ew > 0 ? ew + (a & 0x3ffff) : -1;
    const r8 = (a) => { const o = at(a); return o >= 0 ? H8[o] : 0; };
    const r16 = (a) => r8(a) | r8(a + 1) << 8, r32 = (a) => (r8(a) | r8(a + 1) << 8 | r8(a + 2) << 16 | r8(a + 3) << 24) >>> 0;
    const linkOn = !!(M._rotk_link_on && M._rotk_link_on());
    return { M, H8, iw, r8, r16, r32, online: !!mp.online, linkOn, me: mp.online ? (mp.me & 1) : 0 };
  };
  const heroAt = (m) => {
    const h = m.r32(0x03003C00 + 0x1AC * (m.r8(0x03003F59) & 1));
    return h >>> 24 === 2 ? [m.r16(h + 0xAE), m.r16(h + 0xB2)] : null;
  };
  // The saved hero being played: page 2 when its flag is on, and the slot
  const heroKey = (m) => { const pg = m.r8(0x0203F009) ? m.r8(0x0203F007) & 1 : 0, sl = m.r8(0x03005834); return sl < 4 ? "p" + pg + "s" + sl : null; };
  const p2Key = () => { try { const j = JSON.parse(sessionStorage.getItem("rotk-p2") || "null"); return j && j.p2 >= 0 && j.p2 < 4 ? "p" + (j.p2pg | 0) + "s" + j.p2 : null; } catch (e) { return null; } };

  // ---- lit campfires, per saved hero (this device + the account; lighting only adds, so copies merge) ---------------
  // last[hero] = the campfire that hero last came to: where they wake after falling (plan Phase 2 QoL)
  let lit = {}, last = {}, at = 0, cloud = null;
  const merge = (o) => { if (!o) return false; let ch = false; for (const k in o) for (const id of o[k] || []) { const a = lit[k] || (lit[k] = []); if (!a.includes(id)) { a.push(id); ch = true; } } return ch; };
  try { const j = JSON.parse(localStorage.getItem(KEY) || "null"); if (j && j.lit) { merge(j.lit); at = j.at || 0; if (j.last) last = j.last; } } catch (e) {}
  const keep = () => {
    at = Date.now();
    try { localStorage.setItem(KEY, JSON.stringify({ lit, last, at })); } catch (e) {}
    try { if (cloud) cloud.set({ lit: JSON.stringify(lit), last: JSON.stringify(last), at }).catch(() => {}); } catch (e) {}
  };
  (async () => {
    try {
      const [db, user] = await Promise.all([window.claude?.use?.("db"), window.claude?.use?.("user")]);
      const id = db && user ? await user.id() : null; if (!id) return;
      const doc = db.doc("data/users/" + id + "/campfires");
      for (let t = 0; t < 20; t++) {
        try {
          const snap = await Promise.race([doc.get(), new Promise((_, r) => setTimeout(() => r(new Error("timeout")), 10000))]);
          const d = snap && snap.exists ? snap.data() : null;
          cloud = doc;
          let ch = merge(d && d.lit ? JSON.parse(d.lit) : null) || !d;
          if (d && d.last && (d.at || 0) > at) { try { last = Object.assign({}, last, JSON.parse(d.last)); ch = true; } catch (e) {} }   // the newer copy's
          if (ch) keep();
          return;
        } catch (e) { await new Promise((r) => setTimeout(r, 3000)); }
      }
    } catch (e) {}
  })();
  const light = (k, id) => { if (!k) return false; const a = lit[k] || (lit[k] = []); if (a.includes(id)) return false; a.push(id); return true; };

  // ---- look ---------------------------------------------------------------------------------------------------------
  const CSS =
    "#cfBtn{position:fixed;left:50%;top:69%;transform:translateX(-50%);z-index:23;display:flex;align-items:center;gap:8px;padding:7px 16px 7px 10px;border:1.5px solid #ffe08a;border-radius:999px;" +
      "background:linear-gradient(#3b2c14,#1a1209);color:#ffe08a;font:700 15px/1 Cinzel,'Trajan Pro',Georgia,serif;letter-spacing:.08em;box-shadow:0 0 0 1px #2a1d10,0 0 12px rgba(255,190,80,.55),0 3px 8px rgba(0,0,0,.6);" +
      "cursor:pointer;touch-action:none;-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}" +
    "#cfBtn[hidden],#cfMenu[hidden]{display:none}#cfBtn svg{width:20px;height:20px}#cfBtn:active{transform:translateX(-50%) scale(.96)}" +
    "#cfMenu{position:fixed;inset:0;z-index:24;display:flex;align-items:center;justify-content:center;background:rgba(6,5,8,.72);touch-action:none}" +
    "#cfMenu .bx{width:min(92%,440px);max-height:86%;display:flex;flex-direction:column;gap:10px;padding:14px 16px 16px;box-sizing:border-box;border:2px solid #b8893a;border-radius:6px;" +
      "background:linear-gradient(#2a2420,#14110f);box-shadow:0 0 0 1px #2a1d10,0 8px 24px rgba(0,0,0,.75),inset 0 0 30px rgba(0,0,0,.6)}" +
    "#cfMenu .hd{text-align:center;color:#ffe08a;font:700 clamp(18px,5vw,24px)/1.1 Cinzel,'Trajan Pro',Georgia,serif;letter-spacing:.12em;text-shadow:0 2px 4px #000}" +
    "#cfMenu .rl{height:2px;margin:-2px auto 2px;width:60%;background:linear-gradient(90deg,transparent,#c99a46,transparent)}" +
    "#cfMenu .ls{display:flex;flex-direction:column;gap:7px;overflow:auto;min-height:0;padding:2px}" +
    "#cfMenu .pl{display:flex;align-items:center;gap:10px;padding:8px 12px;border:2px solid #a87a32;border-radius:4px;cursor:pointer;color:#2b1d10;text-align:left;" +
      "background:radial-gradient(ellipse at 40% 40%,#fbf1d4,#ecd9a8 60%,#cfae72);box-shadow:inset 0 0 18px rgba(120,80,30,.5),0 2px 6px rgba(0,0,0,.6);font:italic 500 14px/1.2 'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif}" +
    "#cfMenu .pl b{display:block;font:700 16px/1.15 Cinzel,'Trajan Pro',Georgia,serif;font-style:normal;letter-spacing:.04em}" +
    "#cfMenu .pl svg{flex:0 0 auto;width:24px;height:24px}#cfMenu .pl.sel{border-color:#ffe08a;box-shadow:inset 0 0 18px rgba(120,80,30,.4),0 0 0 2px #f6c45a,0 0 14px rgba(255,190,80,.85)}" +
    "#cfMenu .pl.here{opacity:.6;cursor:default}#cfMenu .nt{color:#d9c9a8;font:italic 13px/1.3 'Iowan Old Style',Palatino,Georgia,serif;text-align:center}" +
    "@media (max-height:520px) and (min-width:560px){#cfMenu .bx{width:min(92%,620px)}#cfMenu .ls{display:grid;grid-template-columns:1fr 1fr}}" +
    "#cfMenu .x{align-self:center;padding:6px 22px;border:1.5px solid #c99a46;border-radius:999px;background:linear-gradient(#1c1a1f,#0d0c10);color:#f3d27a;font:700 14px/1 Cinzel,Georgia,serif;cursor:pointer}" +
    "#cfLit{position:fixed;left:0;right:0;top:24%;z-index:23;text-align:center;pointer-events:none;opacity:0;transition:opacity .6s;font-family:Cinzel,'Trajan Pro',Georgia,serif;color:#ffe08a;text-shadow:0 2px 6px #000,0 0 18px rgba(216,162,64,.35)}" +
    "#cfLit .a{font:700 clamp(18px,5vw,30px)/1.1 Cinzel,Georgia,serif;letter-spacing:.14em}#cfLit .b{margin-top:6px;font:600 clamp(11px,3vw,15px)/1.2 Cinzel,Georgia,serif;letter-spacing:.2em;color:#e6c27a}" +
    "#cfLit .r{margin:8px auto 0;width:min(46%,240px);height:2px;background:linear-gradient(90deg,transparent,#c99a46,transparent)}";
  const FLAME = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#ffb347" d="M12 2c1 4 5 5.5 5 11a5 5 0 0 1-10 0c0-3 1.5-4.5 2.5-6 .3 2 1.2 3 2.2 3.4C11 8 11 5 12 2z"/><path fill="#ffe8a0" d="M12 11c.8 2 2.6 2.6 2.6 5a2.6 2.6 0 0 1-5.2 0c0-1.5.8-2.3 1.4-3 .2.8.6 1.2 1 1.4-.2-1.4-.1-2.4.2-3.4z"/><path stroke="#8a5a1a" stroke-width="1.6" stroke-linecap="round" d="M5 21l14-3M19 21L5 18"/></svg>';
  let host = null, btn = null, menu = null, toast = null;
  const ensure = () => {
    const H = window.GbrHost, par = H && H.canvas && H.canvas.parentElement; if (!par) return false;
    if (host === par && btn && btn.isConnected) { place(); return true; }
    host = par;
    if (!document.getElementById("cfCss")) { const st = document.createElement("style"); st.id = "cfCss"; st.textContent = CSS; document.head.appendChild(st); }
    btn = document.createElement("button"); btn.type = "button"; btn.id = "cfBtn"; btn.hidden = true; btn.innerHTML = FLAME + "<span>Travel</span>";
    btn.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); open(); });
    btn.addEventListener("click", (e) => e.preventDefault());
    menu = document.createElement("div"); menu.id = "cfMenu"; menu.hidden = true;
    menu.addEventListener("pointerdown", (e) => { e.stopPropagation(); if (e.target === menu) close(); });
    toast = document.createElement("div"); toast.id = "cfLit";
    document.body.appendChild(btn); document.body.appendChild(menu); document.body.appendChild(toast);   // over the HUD (#hdHud, fixed, z 21)
    return true;
  };
  // over the game's picture: the button a little below the hero, the lit banner above (the picture's box on the page)
  const place = () => {
    const r = host.getBoundingClientRect(); if (!(r.width > 0)) return;
    const cx = (r.left + r.width / 2).toFixed(0) + "px";
    btn.style.left = cx; btn.style.top = (r.top + r.height * 0.69).toFixed(0) + "px";
    toast.style.left = r.left.toFixed(0) + "px"; toast.style.right = "auto"; toast.style.width = r.width.toFixed(0) + "px"; toast.style.top = (r.top + r.height * 0.22).toFixed(0) + "px";
  };
  const showLit = (c) => {
    if (!toast) return;
    toast.innerHTML = '<div class="a">' + esc(title(c)) + '</div><div class="r"></div><div class="b">CAMPFIRE LIT</div>';
    toast.style.opacity = "1"; clearTimeout(showLit.t); showLit.t = setTimeout(() => { toast.style.opacity = "0"; }, 2600);
  };
  const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  // ---- the travel list ----------------------------------------------------------------------------------------------
  let here = null, sel = 0, paused = false;
  const pause = (on) => {
    const m = mem(); if (!m || m.online) return;   // online the game runs on (the other player is still playing)
    try { m.M._rotk_pause(on ? 1 : 0); paused = on; } catch (e) {}
  };
  function open() {
    const m = mem(); if (!m || !here) return;
    const k = heroKey(m), ids = (lit[k] || []).slice();
    const seen = new Set(), list = [];
    CAMPS.forEach((c) => { if (ids.includes(c[0]) && !seen.has(c[0])) { seen.add(c[0]); list.push(c); } });
    list.sort((a, b) => (b[0] === here[0]) - (a[0] === here[0]));   // where you are first
    menu.innerHTML = '<div class="bx"><div class="hd">Campfires</div><div class="rl"></div><div class="ls"></div><div class="nt"></div><button type="button" class="x">Stay</button></div>';
    const ls = menu.querySelector(".ls"), nt = menu.querySelector(".nt");
    const others = list.filter((c) => c[0] !== here[0]);
    nt.textContent = !others.length ? "Light more campfires on your journey to travel between them." : m.linkOn ? "Travel to a campfire you have lit. Your companion comes with you." : "Travel to a campfire you have lit.";
    sel = 0;
    list.forEach((c) => {
      const b = document.createElement("div"); const isHere = c[0] === here[0];
      b.className = "pl" + (isHere ? " here" : ""); b.innerHTML = FLAME + "<span><b>" + esc(title(c)) + "</b>" + (c[0] === here[0] ? "You are here" : esc(placeName(c[1]))) + "</span>";
      if (!isHere) b.addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); go(c); });
      ls.appendChild(b);
    });
    const mark = () => ls.querySelectorAll(".pl:not(.here)").forEach((el, i) => el.classList.toggle("sel", i === sel));
    menu.__keys = (e) => {
      const n = ls.querySelectorAll(".pl:not(.here)").length;
      if (e.key === "Escape" || e.key === "Backspace") close();
      else if (e.key === "ArrowDown" && n) sel = (sel + 1) % n; else if (e.key === "ArrowUp" && n) sel = (sel + n - 1) % n;
      else if ((e.key === "Enter" || e.key === " ") && n) { go(others[sel]); }
      else return;
      e.preventDefault(); e.stopPropagation(); mark();
    };
    mark();
    menu.querySelector(".x").addEventListener("pointerdown", (e) => { e.preventDefault(); e.stopPropagation(); close(); });
    menu.hidden = false; btn.hidden = true; pause(true);
  }
  function close() { if (!menu || menu.hidden) return; menu.hidden = true; menu.innerHTML = ""; if (paused) pause(false); }
  window.addEventListener("keydown", (e) => { if (menu && !menu.hidden && menu.__keys) menu.__keys(e); }, true);
  // The game's own level change to the campfire, as a door makes it (0x08014D40 -> 0x08033170(1, 0, level)): each player's
  // arrival entry at IWRAM 0x03003F68 + player (0x0803C634), then state 1 pending (0x81), mode 0, the level (mode 5, a save's load, stops a link game)
  // Online both games go, on the same frame: the engine takes the page's writes back out and sends them with the
  // buttons, and both pages write them before that frame (v180 ops)
  const warp = (m, c) => {
    const bases = m.online && m.M._rotk_link_iwram ? [0, 1].map((g) => m.M._rotk_link_iwram(g)) : [m.iw];
    for (const iw of bases) {
      const w32 = (o, v) => { for (let i = 0; i < 4; i++) m.H8[iw + o + i] = (v >>> (8 * i)) & 255; };
      m.H8[iw + 0x3F68] = c[5]; m.H8[iw + 0x3F69] = c[5];
      w32(0x41F8, c[4]); w32(0x41F4, 0); w32(0x41FC, 0); w32(0x4200, 0); w32(0x4204, 0); w32(0x41F0, 0x81);
    }
  };
  // With P2 (one game: P2 is player 1 in it) the level change places only the hero being played at the campfire; P2 is
  // left where its old map had it, so once the new place is in P2 is put by your side (the AI then steps it off you)
  let arrive = null;
  const putBeside = (m) => {
    const o0 = m.r32(0x03003C00), o1 = m.r32(0x03003C00 + 0x1AC); if (o0 >>> 24 !== 2 || o1 >>> 24 !== 2) return true;
    const x = m.r16(o0 + 0xAE), y = m.r16(o0 + 0xB2);
    if (Math.hypot(m.r16(o1 + 0xAE) - x, m.r16(o1 + 0xB2) - y) < 120) return true;
    const ew = m.M._rotk_ewram ? m.M._rotk_ewram() : -1; if (!(ew > 0)) return true;
    const w8 = (a, v) => { m.H8[ew + (a & 0x3ffff)] = v; };
    for (const b of [0xAC, 0xB4, 0xCC]) { w8(o1 + b + 2, x & 255); w8(o1 + b + 3, x >> 8); w8(o1 + b + 6, y & 255); w8(o1 + b + 7, y >> 8); }
    return true;
  };
  function go(c) {
    close();
    const m = mem(); if (!m) return;
    const tv = { to: c[4], name: title(c), sub: placeName(c[1]).toUpperCase(), go: () => { const m2 = mem(); if (m2) warp(m2, c); } };
    try { (window.__wideLog || (window.__wideLog = [])).push("campfire: travel to " + c[0] + " (level " + c[4] + ")"); } catch (e) {}
    if (window.__seam && window.__seam.travel) window.__seam.travel(tv); else tv.go();
    arrive = m.linkOn && !m.online ? { lv: c[4], t: performance.now() } : null;   // online each game places its own player
  }

  // ---- falling: wake at the last campfire ---------------------------------------------------------------------------
  // When the hero falls the game reloads the level they fell in (0x08033170(1, 0, level): 0x030041F0 = 0x81 pending,
  // mode 0, the same level, arrival 0x03003F68 = 0, the level's start). While that is pending (the fade out, about half
  // a second) its level and arrival are changed to the hero's last campfire, so they wake by its fire instead of at
  // the start of the level or region. Online only the host's page does it (its hero's campfire), into both games.
  let wakeSeen = 0;
  const wakeWatch = () => {
    requestAnimationFrame(wakeWatch);
    const m = mem(); if (!m) return;
    try {
      const r32 = (o) => m.r32(0x03000000 + o);
      if (r32(0x41F0) !== 0x81 || r32(0x41F4) !== 0) { wakeSeen = 0; return; }
      const cur = m.r8(0x03004174), to = r32(0x41F8);
      if (to !== cur || wakeSeen) return;
      wakeSeen = 1;
      if (m.online && m.me !== 0) return;
      const P = 0x03003C00 + 0x1AC * (m.r8(0x03003F59) & 1);
      if (((m.r16(P + 0x17C) << 16) >> 16) > 0) return;   // not a fall (a level that restarts itself); a fallen hero's hit points can be below 0
      const k = heroKey(m), c = k && last[k] && CAMPS.find((x) => x[0] === last[k]);
      if (!c) return;
      const bases = m.online && m.M._rotk_link_iwram ? [0, 1].map((g) => m.M._rotk_link_iwram(g)) : [m.iw];
      for (const iw of bases) { m.H8[iw + 0x3F68] = c[5]; m.H8[iw + 0x3F69] = c[5]; m.H8[iw + 0x41F8] = c[4]; }
      if (m.linkOn && !m.online) arrive = { lv: c[4], t: performance.now() };
      try { (window.__wideLog || (window.__wideLog = [])).push("campfire: fell, waking at " + c[0] + " (level " + c[4] + ")"); } catch (e) {}
    } catch (e) {}
  };
  requestAnimationFrame(wakeWatch);
  // With two heroes (P2, online) a fallen hero comes back alone at the level's start while the other plays on, so there
  // is no reload to change: once they are back on their feet, if their last campfire is in this same level (a region's
  // campsite) they are moved to its fireside. Online each page moves its own hero, in both games (the writes travel as
  // ops, so both pages stay alike).
  let downAt = 0;
  const wakeTwo = (m, lv) => {
    const me = m.r8(0x03003F59) & 1, P = 0x03003C00 + 0x1AC * me, hp = (m.r16(P + 0x17C) << 16) >> 16;
    if (hp <= 0) { downAt = performance.now(); return; }
    if (!downAt) return;
    if (performance.now() - downAt > 15000) { downAt = 0; return; }
    const k = heroKey(m), c = k && last[k] && CAMPS.find((x) => x[0] === last[k]);
    if (!c || c[4] !== lv || !REGIONS.has(lv)) { downAt = 0; return; }
    const h = heroAt(m); if (!h) return;
    downAt = 0;
    if (Math.hypot(h[0] - c[2], h[1] - c[3]) < 300) return;
    const x = c[2] + (me ? 20 : -20), y = c[3] + (me ? 58 : 55);
    const games = m.online && m.M._rotk_link_ewram ? [0, 1].map((g) => [m.M._rotk_link_iwram(g), m.M._rotk_link_ewram(g)]) : [[m.iw, m.M._rotk_link_on ? m.M._rotk_link_ewram(0) : m.M._rotk_ewram()]];
    for (const [iw, ew] of games) {
      const o = (m.H8[iw + 0x3C00 + 0x1AC * me] | m.H8[iw + 0x3C01 + 0x1AC * me] << 8 | m.H8[iw + 0x3C02 + 0x1AC * me] << 16 | m.H8[iw + 0x3C03 + 0x1AC * me] << 24) >>> 0;
      if (o >>> 24 !== 2) continue;
      const e = ew + (o & 0x3ffff);
      for (const b of [0xAC, 0xB4, 0xCC]) { m.H8[e + b + 2] = x & 255; m.H8[e + b + 3] = x >> 8; m.H8[e + b + 6] = y & 255; m.H8[e + b + 7] = y >> 8; }
    }
    try { (window.__wideLog || (window.__wideLog = [])).push("campfire: back up, moved to " + c[0]); } catch (e) {}
  };

  // ---- watch: which campfire is near, light new ones ----------------------------------------------------------------
  setInterval(() => {
    if (!ensure()) return;
    const m = mem(); let near = null;
    if (arrive && m) {
      try {
        if (performance.now() - arrive.t > 20000) arrive = null;
        else if (m.r8(0x030041B0) === 1 && m.r8(0x03004174) === arrive.lv && m.r8(0x030041F8) === arrive.lv && !m.r8(0x0203FFF1) && heroAt(m) && putBeside(m)) arrive = null;
      } catch (e) { arrive = null; }
    }
    try {
      const st = m ? m.r8(0x030041B0) : 0, lv = m ? m.r8(0x03004174) : 0, hero = m && st === 1 && lv === m.r8(0x030041F8) ? heroAt(m) : null;
      const covering = !!(window.__seam && window.__seam.on);
      if (m && m.linkOn && st === 1) wakeTwo(m, lv);
      if (hero && !covering) {
        for (const c of CAMPS) {
          if (c[1] !== lv) continue;
          const d = Math.hypot(hero[0] - c[2], hero[1] - c[3]);
          if (d <= FOUND || !REGIONS.has(lv)) {
            const ks = [heroKey(m)]; if (m.linkOn && !m.online) ks.push(p2Key());
            let nw = false; for (const k of ks) nw = light(k, c[0]) || nw;
            let mv = false; for (const k of ks) if (k && last[k] !== c[0]) { last[k] = c[0]; mv = true; }
            if (nw) showLit(c);
            if (nw || mv) keep();
          }
          if (d <= NEAR) near = c;
        }
      }
    } catch (e) {}
    here = near;
    if (menu && !menu.hidden) return;
    if (btn.hidden !== !near) btn.hidden = !near;
  }, 250);
  window.__campfire = { lit: () => JSON.parse(JSON.stringify(lit)), camps: CAMPS, open: () => open(), go: (id) => { const c = campOf(id); if (c) go(c); },
    light: (id) => { const m = mem(), k = m && heroKey(m); if (k && light(k, id)) keep(); }, last: () => Object.assign({}, last) };   // tests: light a campfire for the hero being played
})();
