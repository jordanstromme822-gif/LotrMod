// Seamless journey (Jordan, 2026-11-20: "Interconnect each level in a 3Dimensional way so it feels like traveling from
// each character's start to finish is seamless with no black screens in between").
//
// When the hero walks through a door the game turns the screen black for about a second (fade out, the new screen is
// built, fade in). Now the page covers that with a short flight over the same joined world as the Story map's 3D World
// (World3D.layout): the camera lifts off the screen the hero is leaving, tilts back over the overhead pictures of both
// screens with the door's gold road between them, and comes down where the hero walks in. No black frame is shown.
//
// How: the game writes the next level to IWRAM 0x030041F8 a few frames before its fade starts (0x03004174 still holds
// the old one); that frame is copied off the game canvas as the take-off picture. While the flight runs, the live
// picture is held under it and the engine runs fast (the same turbo the load already uses, not online). The new
// screen is ready once 0x03004174 = 0x030041F8, the load flag (EWRAM 0x0203FFF1) is clear and the fade in has
// settled (picture brightness steady); that picture is the landing picture. The game waits (paused, not online)
// while the camera lands, so nothing happens to the hero unseen. A load with no level change (the same screen, a
// respawn) flies from the last bright picture. Page only: 1-player, P2 and online alike.
(() => {
  const D_ALL = 1.15;        // seconds for a whole flight when the new screen is ready in time
  const T_WAIT = 0.52;       // how far (share of the flight) the camera goes before it waits for the new screen
  const TILT = 34;           // degrees the world tips back at the top of the flight (grows with the height, so
                             // the big pictures never reach past the eye while the camera is still low)
  const GAP = 140;           // picture pixels between two screens when the 3D World has no place for one
  const ROW_Y = 0.575;       // the hero stands this far down the game's view (measured: 138 of 240 rows)
  // Top left of the game's whole view on the map (measured against the map pictures): the hero in the middle (18 rows
  // low), held inside the map with the wide view's extra margin ((w - 240) / 2 at the sides, (h - 160) / 2 at the
  // top; the bottom stops 14 rows sooner, under the HUD).
  const origin = (hero, lv, w, h) => {
    const D = window.__smData, sz = D && D.SZ && D.SZ[lv], mx = (w - 240) / 2, my = (h - 160) / 2;
    let x = hero[0] - w / 2, y = hero[1] - h * ROW_Y;
    if (sz) { x = Math.max(-mx, Math.min(sz[0] - 240 - mx, x)); y = Math.max(-my, Math.min(sz[1] - 174 - my, y)); }
    return [x, y];
  };
  let pin = null, lay = null, layTried = false, S = null, good = null, pre = {}, lastSt = -1, lastLv = -1, hookT = 0;

  const layout = () => {
    if (lay || layTried) return lay;
    const D = window.__smData; if (!D || !window.World3D || !World3D.layout) return null;
    layTried = true; try { lay = World3D.layout(D); } catch (e) { lay = null; }
    return lay;
  };
  const mem = () => {
    const mp = window.__mp, M = mp && mp.M; if (!M || !M.HEAPU8) return null;
    let iw = -1, ew = -1;
    try { iw = mp.iwram(); ew = mp.ewram ? mp.ewram() : M._rotk_ewram ? M._rotk_ewram() : -1; } catch (e) { return null; }
    if (!(iw > 0)) return null;
    const H8 = M.HEAPU8;
    const r8 = (a) => a >= 0x03000000 ? H8[iw + a - 0x03000000] : ew > 0 ? H8[ew + (a & 0x3ffff)] : 0;
    const r16 = (a) => r8(a) | r8(a + 1) << 8, r32 = (a) => (r8(a) | r8(a + 1) << 8 | r8(a + 2) << 16 | r8(a + 3) << 24) >>> 0;
    return { M, r8, r16, r32, online: !!mp.online };
  };
  const heroAt = (m) => {
    const P = 0x03003C00 + 0x1AC * (m.r8(0x03003F59) & 1), h = m.r32(P);
    if (h >>> 24 !== 2) return null;
    return [m.r16(h + 0xAE), m.r16(h + 0xB2)];
  };
  const luma = () => {
    const f = window.__gbaFrame && window.__gbaFrame(); if (!f || !f.w || !f.h) return -1;
    let s = 0, n = 0; const u = f.u8, N = f.w * f.h;
    for (let i = 0; i < N; i += 61) { const o = f.off + i * 3; s += u[o] + u[o + 1] + u[o + 2]; n++; }
    return s / n / 3;
  };
  // Share of a picture (top, right, bottom, left) that lies past the edge of its map (black in the game's picture).
  const outside = (cam, lv) => {
    const D = window.__smData, sz = D && D.SZ && D.SZ[lv]; if (!sz) return [0, 0, 0, 0];
    const f = (a, b) => Math.max(0, Math.min(0.5, a / b));
    return [f(-cam[1], cam[3]), f(cam[0] + cam[2] - sz[0], cam[2]), f(cam[1] + cam[3] - sz[1], cam[3]), f(-cam[0], cam[2])];
  };
  const busy = () => !!(window.__hdShopOn || window.__hdBpOn || window.__hdPgOn);
  const pic = (l) => "maps/t/L" + l + ".webp";
  const preload = (l) => {
    const D = window.__smData; if (!D || !D.SZ) return;
    const want = [l].concat((D.EE[l] || []).filter((e) => e[0] === 1).map((e) => e[3]));
    want.forEach((k) => { if (D.SZ[k] && !pre[k]) { const im = new Image(); im.decoding = "async"; im.src = pic(k); pre[k] = im; } });
  };

  // Where the game's picture sits on screen (CSS pixels inside #game) and which part of the map it shows.
  const viewNow = (hero, lv, v0) => {
    const v = v0 || window.__gbaView, H = window.GbrHost; if (!v || !H || !H.canvas) return null;
    const el = H.canvas, r = el.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return null;
    const fx = r.width / v.CW, fy = r.height / v.CH;
    const css = [v.dest[0] * fx, v.dest[1] * fy, v.dest[2] * fx, v.dest[3] * fy];
    const o = origin(hero, lv, v.w, v.h), cam = [o[0] + v.sx, o[1] + v.sy, v.sw, v.sh];
    // The game's own HUD (bars and icons, 34 rows, raised by __hudB in the small-screen view) is cut off the pictures in the air.
    const hudTop = v.h - (window.__hudB || 0) - 34, cut = Math.max(0, Math.min(0.4, (v.sy + v.sh - hudTop) / v.sh));
    return { v, css, cam, cut, W: r.width, H: r.height };
  };
  // Copy what the game canvas shows now (it must have been drawn in this same task).
  const grab = (view) => {
    const H = window.GbrHost, src = H.canvas, d = view.v.dest;
    const c = document.createElement("canvas"); c.width = Math.max(1, d[2]); c.height = Math.max(1, d[3]);
    try { c.getContext("2d").drawImage(src, d[0], d[1], d[2], d[3], 0, 0, d[2], d[3]); } catch (e) { return null; }
    return c;
  };
  // The last bright picture again (when the load came without a level change, the screen is black already).
  const grabGood = (view) => {
    const H = window.GbrHost; if (!good || !H) return null;
    const v = view.v, w = v.w, h = v.h;
    try {
      const d = v.dest, dz = [d[0] - v.sx * d[2] / v.sw, d[1] - v.sy * d[3] / v.sh, w * d[2] / v.sw, h * d[3] / v.sh];   // as GbrHost.draw zooms
      if (H.sharp) { H.sharp(good.raw, 0, w, 0, 0, w, h, dz, H.plain); return grab(view); }
      const b = document.createElement("canvas"); b.width = w; b.height = h; const bx = b.getContext("2d"), im = bx.createImageData(w, h);
      for (let i = 0, s = 0, t = 0; i < w * h; i++, s += 3, t += 4) { im.data[t] = good.raw[s]; im.data[t + 1] = good.raw[s + 1]; im.data[t + 2] = good.raw[s + 2]; im.data[t + 3] = 255; }
      bx.putImageData(im, 0, 0);
      const c = document.createElement("canvas"); c.width = v.dest[2]; c.height = v.dest[3];
      c.getContext("2d").drawImage(b, v.sx, v.sy, v.sw, v.sh, 0, 0, c.width, c.height); return c;
    } catch (e) { return null; }
  };

  const CSS = "#seam{position:absolute;inset:0;z-index:20;overflow:hidden;pointer-events:none;perspective:2000px;" +
    "background:radial-gradient(120% 70% at 50% 110%,rgba(240,130,50,.35),transparent 60%),linear-gradient(#141a2e,#2b2235 45%,#3a2a28 70%,#17120e)}" +
    "#seam .w{position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform}" +
    "#seam .w>*{position:absolute;display:block;box-sizing:border-box;max-width:none;max-height:none}" +
    "#seam .m{filter:brightness(.82) saturate(.9);box-shadow:0 0 0 6px #b8893a,0 0 0 9px #2a1d10,0 30px 60px rgba(0,0,0,.6);image-rendering:auto}" +
    "#seam .s{transition:opacity .16s linear}" +
    "#seam .road{height:14px;margin-top:-7px;transform-origin:0 50%;border-radius:7px;background:linear-gradient(#f6dc93,#c99a46);box-shadow:0 0 18px rgba(255,200,90,.7)}" +
    "#seam .nm{left:0;top:0;font:700 34px/1 var(--display,Georgia,serif);color:#f6dc93;text-shadow:0 2px 8px #000,0 0 18px rgba(0,0,0,.8);white-space:nowrap;transform:translate(-50%,-140%)}";

  function start(m, from, to, hero, snap, view) {
    const L = layout(), D = window.__smData || {};
    const T = L && L.T;
    let TA = T && T[from], TB = T && T[to];
    const camA = view.cam;
    if (window.__seamDebug) window.__seamDbg = { from, to, hero, cam: camA, v: view.v, pic: snap.toDataURL() };
    let A = TA ? { x: TA.x, y: TA.y, w: TA.w, h: TA.h } : { x: 0, y: 0, w: 0, h: 0 };
    // Where the hero will walk in on the new screen: the door's far end in the 3D World, else the screen's middle.
    let B = null, entry = null, road = null;
    if (TB && to !== from) {
      B = { x: TB.x, y: TB.y, w: TB.w, h: TB.h };
      const lk = L.links.find((k) => k.a === from && k.b === to) || L.links.find((k) => k.a === to && k.b === from);
      if (lk) { const there = lk.a === to ? lk.pa : lk.pb, here = lk.a === to ? lk.pb : lk.pa; entry = [there[0] - B.x, there[1] - B.y]; road = [here, there]; }
      else entry = [B.w / 2, B.h / 2];
    }
    if (!B) {   // no place in the 3D World: the next screen goes just past the side the hero left by
      const w = TA ? TA.w : camA[2] * 3, h = TA ? TA.h : camA[3] * 3;
      const d = [hero[0], w - hero[0], hero[1], h - hero[1]], side = d.indexOf(Math.min(...d));
      const dir = to === from ? [0, 0] : [[-1, 0], [1, 0], [0, -1], [0, 1]][side];
      B = { x: A.x + camA[0] + dir[0] * (camA[2] + GAP), y: A.y + camA[1] + dir[1] * (camA[3] + GAP), w: 0, h: 0 };
      entry = [camA[2] / 2, camA[3] * ROW_Y];
      if (to === from) { B = A; entry = null; }
    }
    if (to === from) B = A;
    const ob = entry && origin(entry, to, view.v.w, view.v.h);
    const camBest = entry ? [ob[0] + view.v.sx, ob[1] + view.v.sy, camA[2], camA[3]] : camA.slice();

    let el = document.getElementById("seam");
    if (!document.getElementById("seamCss")) { const st = document.createElement("style"); st.id = "seamCss"; st.textContent = CSS; document.head.appendChild(st); }
    if (el) el.remove();
    el = document.createElement("div"); el.id = "seam";
    const host = window.GbrHost.canvas.parentElement; host.appendChild(el);
    const wd = document.createElement("div"); wd.className = "w"; el.appendChild(wd);
    const put = (node, x, y, w, h) => { node.style.left = x + "px"; node.style.top = y + "px"; if (w !== undefined) { node.style.width = w + "px"; node.style.height = h + "px"; } wd.appendChild(node); return node; };
    const mapImg = (l, R) => { if (!R.w || !D.SZ || !D.SZ[l]) return; const im = pre[l] && pre[l].complete && pre[l].naturalWidth ? pre[l].cloneNode() : new Image(); if (!im.src) im.src = pic(l); im.className = "m"; im.onerror = () => { im.style.visibility = "hidden"; }; put(im, R.x, R.y, R.w, R.h); };
    mapImg(from, A); if (B !== A) mapImg(to, B);
    // Other screens under the flight path are ground too (the same joined world as the 3D World).
    if (T && B !== A) {
      const ax = A.x + camA[0], ay = A.y + camA[1], bx = B.x + camBest[0], by = B.y + camBest[1], pad = Math.max(camA[2], camA[3]) * 1.5;
      const x0 = Math.min(ax, bx) - pad, y0 = Math.min(ay, by) - pad, x1 = Math.max(ax, bx) + camA[2] + pad, y1 = Math.max(ay, by) + camA[3] + pad;
      Object.values(T).forEach((t) => { if (t.l === from || t.l === to || t.x > x1 || t.x + t.w < x0 || t.y > y1 || t.y + t.h < y0) return; mapImg(t.l, t); });
    }
    if (road) { const r = document.createElement("div"); r.className = "road"; const dx = road[1][0] - road[0][0], dy = road[1][1] - road[0][1];
      r.style.width = Math.hypot(dx, dy) + "px"; r.style.transform = "rotate(" + Math.atan2(dy, dx) + "rad)"; put(r, road[0][0], road[0][1]); }
    if (B !== A && D.NAMES && D.NAMES[to]) { const n = document.createElement("div"); n.className = "nm"; n.textContent = D.NAMES[to]; put(n, B.x + B.w / 2, B.y + Math.max(0, camBest[1])); n.style.fontSize = Math.max(34, camA[2] / 9) + "px"; }
    snap.className = "s"; snap.__out = outside(camA, from); snap.__cut = view.cut; put(snap, A.x + camA[0], A.y + camA[1], camA[2], camA[3]);
    S = { el, wd, put, A, B, from, to, camA, camB: camBest, camBact: null, view, t: 0, uR: 0, last: performance.now(), haveB: false, wantB: false,
      loaded: false, sawLoad: false, pl: -1, steady: 0, online: m.online, born: performance.now(), paused: false };
    if (!m.online) window.__seamTurbo = 1;
    move(0);
    requestAnimationFrame(tick);
  }

  const smooth = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  function move(u) {
    const s = S, v = s.view, kAx = v.css[2] / s.camA[2], kAy = v.css[3] / s.camA[3];
    const cA = [s.A.x + s.camA[0] + s.camA[2] / 2, s.A.y + s.camA[1] + s.camA[3] / 2];
    const est = [s.B.x + s.camB[0] + s.camB[2] / 2, s.B.y + s.camB[1] + s.camB[3] / 2];
    let cB = est;
    if (s.camBact) { const act = [s.B.x + s.camBact[0] + s.camBact[2] / 2, s.B.y + s.camBact[1] + s.camBact[3] / 2], w = smooth((u - s.uR) / Math.max(0.05, 1 - s.uR)); cB = [est[0] + (act[0] - est[0]) * w, est[1] + (act[1] - est[1]) * w]; }
    const sm = smooth(u), bump = Math.sin(Math.PI * Math.max(0, Math.min(1, u)));
    const cx = cA[0] + (cB[0] - cA[0]) * sm, cy = cA[1] + (cB[1] - cA[1]) * sm;
    // Lift high enough to see both screens at the top of the flight (between 30% and 70% of the game's own zoom).
    const dx = Math.abs(est[0] - cA[0]), dy = Math.abs(est[1] - cA[1]);
    const kMid = Math.max(0.3 * kAx, Math.min(0.7 * kAx, v.W / (dx + s.camA[2] * 1.7), v.H / (dy + s.camA[3] * 1.7) * kAx / kAy));
    const lift = Math.log(Math.max(1e-4, kMid / kAx)) * bump;
    const kx = kAx * Math.exp(lift), ky = kAy * Math.exp(lift);
    const ox = v.css[0] + v.css[2] / 2, oy = v.css[1] + v.css[3] / 2;
    // In the air the game's own HUD rows and the black past the map's edge are cut off the pictures.
    const g = Math.min(1, bump * 4);
    for (const c of s.wd.querySelectorAll("canvas.s")) { const o = c.__out || [0, 0, 0, 0], pc = (x) => (100 * x * g).toFixed(2) + "%";
      c.style.clipPath = "inset(" + pc(o[0]) + " " + pc(o[1]) + " " + pc(Math.max(o[2], c.__cut || 0)) + " " + pc(o[3]) + ")"; }
    s.wd.style.transform = "translate(" + ox.toFixed(2) + "px," + oy.toFixed(2) + "px) rotateX(" + (TILT * bump * bump).toFixed(2) + "deg) scale(" + kx.toFixed(5) + "," + ky.toFixed(5) + ") translate(" + (-cx).toFixed(2) + "px," + (-cy).toFixed(2) + "px)";
  }
  function finish(ok, why) {
    const s = S; if (!s) return;
    S = null; window.__seamTurbo = 0;
    const H = window.GbrHost; if (H) H.holdT = 0;
    if (s.paused) { try { s.m.M._rotk_pause(0); } catch (e) {} }
    if (s.el) s.el.remove();
    if (!ok) (window.__wideLog || (window.__wideLog = [])).push("seam: gave up after " + Math.round(performance.now() - s.born) + " ms (" + (why || "error") + ", " + s.from + " > " + s.to + ")");
  }
  function tick() {
    const s = S; if (!s) return;
    const now = performance.now(), dt = Math.min(0.05, (now - s.last) / 1000); s.last = now;
    if (now - s.born > 5000) { finish(false, "time"); return; }
    let rate = 1 / D_ALL;
    if (!s.haveB) { const room = T_WAIT - s.t; rate *= room > 0.12 ? 1 : Math.max(0.04, room / 0.12); }
    if (pin !== null) { s.t = pin; s.born = now; } else s.t = Math.min(s.haveB ? 1 : T_WAIT, s.t + dt * rate);
    move(s.t);
    if (s.haveB && s.t >= 1) { finish(true); return; }
    requestAnimationFrame(tick);
  }

  // Runs after each game picture is handed to the screen.
  function after(fresh, drew) {
    if (!fresh) return;
    const m = mem(); if (!m) return;
    const st = m.r8(0x030041B0), to = m.r8(0x030041F8), cur = m.r8(0x03004174), ld = m.r8(0x0203FFF1);
    const H = window.GbrHost;
    if (!S) {
      const hero = st === 1 ? heroAt(m) : null, lum = drew ? luma() : -1;
      const inPlay = st === 1 && lastSt === 1 && hero && !busy();
      if (inPlay && to !== cur && cur && to && drew) {   // level 0 = leaving play for the story screens
        const view = viewNow(hero, cur), snap = view && grab(view);
        if (view && snap) { start(m, cur, to, hero, snap, view); S.m = m; H.holdT = performance.now() + 1000; }
      } else if (inPlay && ld && good && performance.now() - good.at < 1500) {
        const view = viewNow(good.hero, good.lv, good.v), snap = view && grabGood(view);
        if (snap) { start(m, cur, cur, good.hero, snap, view); S.m = m; H.holdT = performance.now() + 1000; }
      } else if (st === 1 && drew && hero && !ld && to === cur && lum > 4) {
        // remember the last steady picture (not while it fades)
        const prev = good && good.lum;
        if (!(prev > 0) || lum >= prev * 0.93 || performance.now() - good.at > 300) {
          const f = window.__gbaFrame(), n = f.w * f.h * 3, v = window.__gbaView;
          if (v && v.w === f.w && v.h === f.h) { if (!good || good.raw.length !== n) good = { raw: new Uint8Array(n) }; good.raw.set(f.u8.subarray(f.off, f.off + n)); good.lum = lum; good.at = performance.now(); good.hero = hero; good.lv = cur; good.v = Object.assign({}, v); }
        }
      }
      if (st === 1 && cur !== lastLv) { lastLv = cur; preload(cur); setTimeout(layout, 50); }
      lastSt = st;
      return;
    }
    // A flight is on: the live picture stays still under it until the new screen has settled.
    const s = S;
    if (s.wantB) {
      if (!drew) return;
      const hero = heroAt(m), view = hero && viewNow(hero, s.to), snap = view && grab(view);
      if (!snap) { finish(false, "picture"); return; }
      s.camBact = view.cam; s.uR = s.t; s.view = view; snap.__out = outside(view.cam, s.to); snap.__cut = view.cut;
      snap.className = "s"; snap.style.opacity = "0";
      s.put(snap, s.B.x + view.cam[0], s.B.y + view.cam[1], view.cam[2], view.cam[3]);
      requestAnimationFrame(() => { snap.style.opacity = "1"; });
      s.wantB = false; s.haveB = true; window.__seamTurbo = 0;
      H.holdT = performance.now() + 2000;
      if (!s.online) { try { m.M._rotk_pause(1); s.paused = true; } catch (e) {} }
      return;
    }
    if (s.haveB) return;
    H.holdT = performance.now() + 1000;
    if (st !== 1) { if (performance.now() - s.born > 400) finish(false, "state " + st); return; }
    if (ld) s.sawLoad = true;
    if (!s.loaded) { if (cur === s.to && !ld && to === cur && heroAt(m)) s.loaded = true; else return; }
    const lum = luma();
    if (lum > 6 && s.pl > 0 && Math.abs(lum - s.pl) <= Math.max(1, 0.02 * lum)) s.steady++; else s.steady = 0;
    s.pl = lum;
    if (s.steady >= 2) { s.wantB = true; H.holdT = 0; }
  }

  // Hook the picture hand-off once the game is running (the Wide engine sets window.GbrHost).
  const hook = () => {
    const H = window.GbrHost;
    if (!H || !H.draw || H.__seam) return false;
    const d0 = H.draw;
    H.draw = function () {
      const f0 = this.frames, held = !!(this.holdT && performance.now() < this.holdT);
      d0.apply(this, arguments);
      const fresh = this.frames !== f0;
      try { after(fresh, fresh && !held && !busy()); } catch (e) { (window.__wideLog || (window.__wideLog = [])).push("seam: " + (e && e.message)); finish(false); }
    };
    H.__seam = true;
    return true;
  };
  if (!hook()) hookT = setInterval(() => { if (hook()) clearInterval(hookT); }, 250);
  // pin(u) holds the camera at u (0..1) for screenshots and tests; pin(null) lets it go on.
  window.__seam = { get on() { return !!S; }, get ready() { return !!(S && S.haveB); }, pin: (u) => { pin = u === null || u === undefined ? null : +u; }, finish, layout };
})();
