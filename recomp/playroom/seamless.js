// Seamless journey, one big level (Jordan, 2026-11-20: "Interconnect each level in a 3Dimensional way so it feels like
// traveling from each character's start to finish is seamless with no black screens in between"; 2026-11-21: "I want
// them to feel like one big level, no line or cut scene, just cohesive movement between maps").
//
// When the hero walks through a door the game turns the screen black for about a second (fade out, the new screen is
// built, fade in). Now the page joins the two screens into one map at the door instead: the next screen's map picture
// is laid right past the door the hero walks through (its own door a step further on), and the view scrolls on, at
// the game's own zoom, from where the hero leaves to where they come in, like the camera following them across one
// big level. No black frame, no lift, no line.
//
// How: the game writes the next level to IWRAM 0x030041F8 a few frames before its fade starts (0x03004174 still holds
// the old one); that frame is copied off the game canvas and stays on top of the old screen's map picture. The way
// the hero was walking (or the nearest map edge) says which side the next screen goes on; its entry point is the
// door's far end in the 3D World (World3D.layout), else its door back. While the scroll runs the live picture is held
// under it and the engine runs fast (the load turbo, not online). The new screen is ready once 0x03004174 =
// 0x030041F8, the load flag (EWRAM 0x0203FFF1) is clear and the fade in has settled (picture brightness steady); that
// picture fades in where it belongs and the view settles on it while the game waits (paused, not online). A load with
// no level change (a respawn) holds the last bright picture. Page only: 1-player, P2 and online alike.
(() => {
  const SPEED = 330;         // map pixels a second the view scrolls (the hero's run is about a quarter of that)
  const D_MIN = 0.42, D_MAX = 1.0;   // seconds a scroll takes at least and at most
  const T_WAIT = 0.88;       // how far (share of the scroll) the view goes before it waits for the new screen
  const STEP = 30;           // map pixels from the door the hero leaves by to the one they come in at
  const FEATHER = 26;        // map pixels over which the next screen's picture blends into this one at the join
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
  let pin = null, trail = [], lay = null, layTried = false, S = null, good = null, pre = {}, lastSt = -1, lastLv = -1, hookT = 0;

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
  const pic = (l, t) => "maps/" + (t ? "t/" : "") + "L" + l + ".webp";
  const preload = (l) => {
    const D = window.__smData; if (!D || !D.SZ) return;
    const want = [l].concat((D.EE[l] || []).filter((e) => e[0] === 1).map((e) => e[3]));
    want.forEach((k) => { if (D.SZ[k] && !pre[k]) pre[k] = [true, false].map((t) => { const im = new Image(); im.decoding = "async"; im.src = pic(k, t); return im; }); });
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

  const CSS = "#seam{position:absolute;inset:0;z-index:20;overflow:hidden;pointer-events:none;background:#000}" +
    "#seam .w{position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform}" +
    "#seam .w>*{position:absolute;display:block;box-sizing:border-box;max-width:none;max-height:none}" +
    "#seam .s{transition:opacity .18s linear}";

  // Which way the hero was going: their last steps, else the map edge they are nearest. [axis, sign]
  const heading = (hero, lv) => {
    const old = trail.length > 6 ? trail[trail.length - 7] : trail[0];
    if (old && old[2] === lv) { const dx = hero[0] - old[0], dy = hero[1] - old[1];
      if (Math.max(Math.abs(dx), Math.abs(dy)) >= 3) return Math.abs(dx) >= Math.abs(dy) ? [0, Math.sign(dx)] : [1, Math.sign(dy)]; }
    const D = window.__smData, sz = (D && D.SZ && D.SZ[lv]) || [hero[0] * 2, hero[1] * 2];
    const d = [hero[0], sz[0] - hero[0], hero[1], sz[1] - hero[1]], k = d.indexOf(Math.min(...d));
    return [[0, -1], [0, 1], [1, -1], [1, 1]][k];
  };
  // Where the hero comes in on the next screen (its own map pixels).
  const entryOf = (from, to) => {
    const D = window.__smData || {}, sz = D.SZ && D.SZ[to]; if (!sz) return null;
    const L = layout(), TB = L && L.T && L.T[to];
    const lk = L && TB && (L.links.find((k) => k.a === from && k.b === to) || L.links.find((k) => k.a === to && k.b === from));
    if (lk) { const there = lk.a === to ? lk.pa : lk.pb; return [there[0] - TB.x, there[1] - TB.y]; }
    const e = (D.EE && D.EE[to] || []).find((e) => e[0] === 1 && e[3] === from);
    if (e) return [e[1] * sz[0] / 1000, e[2] * sz[1] / 1000];
    return [sz[0] / 2, sz[1] / 2];
  };
  // A soft edge along the join: keep the part of a picture past the join line (seam, along axis ax) on side sg.
  const maskAt = (node, ax, start, seam, sg) => {
    const t = seam - start, a = (t - FEATHER / 2).toFixed(1) + "px", b = (t + FEATHER / 2).toFixed(1) + "px";
    const g = "linear-gradient(to " + (ax ? "bottom" : "right") + "," + (sg > 0 ? "transparent " + a + ",#000 " + b : "#000 " + a + ",transparent " + b) + ")";
    node.style.webkitMaskImage = g; node.style.maskImage = g;
  };

  function start(m, from, to, hero, snap, view) {
    const D = window.__smData || {};
    const camA = view.cam, same = to === from;
    if (window.__seamDebug) window.__seamDbg = { from, to, hero, cam: camA, v: view.v, pic: snap.toDataURL() };
    // One map: the old screen at 0,0; the next one placed so its entry point is a step on from the door.
    const dir = heading(hero, from), entry = same ? null : entryOf(from, to);
    let B = { x: 0, y: 0 }, seam = 0;
    if (entry) {
      const go = [dir[0] === 0 ? dir[1] : 0, dir[0] === 1 ? dir[1] : 0];
      B = { x: hero[0] + go[0] * STEP - entry[0], y: hero[1] + go[1] * STEP - entry[1] };
      seam = hero[dir[0]] + dir[1] * STEP / 2;
    }
    const ob = entry && origin(entry, to, view.v.w, view.v.h);
    if (window.__seamDebug) Object.assign(window.__seamDbg, { dir, entry, B, seam });
    const camBest = entry ? [ob[0] + view.v.sx, ob[1] + view.v.sy, camA[2], camA[3]] : camA.slice();

    let el = document.getElementById("seam");
    if (!document.getElementById("seamCss")) { const st = document.createElement("style"); st.id = "seamCss"; st.textContent = CSS; document.head.appendChild(st); }
    if (el) el.remove();
    el = document.createElement("div"); el.id = "seam";
    const host = window.GbrHost.canvas.parentElement; host.appendChild(el);
    const wd = document.createElement("div"); wd.className = "w"; el.appendChild(wd);
    const put = (node, x, y, w, h) => { node.style.left = x + "px"; node.style.top = y + "px"; if (w !== undefined) { node.style.width = w + "px"; node.style.height = h + "px"; } wd.appendChild(node); return node; };
    // The map picture (full size when it has arrived, else the small one) under the game's own picture.
    const mapImg = (l, x, y) => {
      const sz = D.SZ && D.SZ[l]; if (!sz) return null;
      const p = pre[l] || [], ok = (im) => im && im.complete && im.naturalWidth;
      const im = ok(p[0]) ? p[0].cloneNode() : ok(p[1]) ? p[1].cloneNode() : new Image();
      if (!im.src) im.src = pic(l, false);
      im.onerror = () => { im.style.visibility = "hidden"; };
      if (p[0] && !ok(p[0])) p[0].addEventListener("load", () => { if (im.isConnected) im.src = p[0].src; }, { once: true });   // sharp one when it comes
      return put(im, x, y, sz[0], sz[1]);
    };
    mapImg(from, 0, 0);
    const twin = (c, cam, lv, cut, x, y) => {   // the picture twice: trimmed to its map (under), and whole (on top)
      const w = document.createElement("canvas"); w.width = c.width; w.height = c.height; w.getContext("2d").drawImage(c, 0, 0);
      const o = outside(cam, lv), pc = (x) => (100 * x).toFixed(2) + "%";
      c.className = "s"; c.style.clipPath = "inset(" + pc(o[0]) + " " + pc(o[1]) + " " + pc(Math.max(o[2], cut)) + " " + pc(o[3]) + ")";
      put(c, x, y, cam[2], cam[3]); put(w, x, y, cam[2], cam[3]); return w;
    };
    // The next screen over the old one past the door, blending in at the join (it comes up as the view moves).
    const imB = entry ? mapImg(to, B.x, B.y) : null;
    if (imB) { maskAt(imB, dir[0], dir[0] ? B.y : B.x, seam, dir[1]); imB.style.opacity = "0"; }
    // The game's picture on top: whole at first (exactly what was on screen), then its HUD rows and the black past the
    // map's edge give way to the map pictures as the view moves.
    const wholeA = twin(snap, camA, from, view.cut, camA[0], camA[1]);
    S = { el, wd, put, twin, snapA: snap, wholeA, wholeB: null, viewA: view, B, imB, from, to, camA, camB: camBest, camBact: null, view, t: 0, uR: 0, last: performance.now(), haveB: false, wantB: false,
      loaded: false, sawLoad: false, pl: -1, steady: 0, online: m.online, born: performance.now(), paused: false };
    const cA = [camA[0] + camA[2] / 2, camA[1] + camA[3] / 2], cB = [B.x + camBest[0] + camBest[2] / 2, B.y + camBest[1] + camBest[3] / 2];
    S.dur = Math.max(D_MIN, Math.min(D_MAX, Math.hypot(cB[0] - cA[0], cB[1] - cA[1]) / SPEED));
    if (!m.online) window.__seamTurbo = 1;
    move(0);
    requestAnimationFrame(tick);
  }

  const smooth = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  function move(u) {
    const s = S, vA = s.viewA, v = s.view;
    let kx = vA.css[2] / s.camA[2], ky = vA.css[3] / s.camA[3];
    const cA = [s.camA[0] + s.camA[2] / 2, s.camA[1] + s.camA[3] / 2];
    const est = [s.B.x + s.camB[0] + s.camB[2] / 2, s.B.y + s.camB[1] + s.camB[3] / 2];
    let cB = est, w = 0;
    if (s.camBact) {   // the new screen is in: settle on where its picture really is (and at its zoom)
      const act = [s.B.x + s.camBact[0] + s.camBact[2] / 2, s.B.y + s.camBact[1] + s.camBact[3] / 2];
      w = smooth((u - s.uR) / Math.max(0.05, 1 - s.uR)); cB = [est[0] + (act[0] - est[0]) * w, est[1] + (act[1] - est[1]) * w];
      const bx = v.css[2] / s.camBact[2], by = v.css[3] / s.camBact[3];
      kx = Math.exp(Math.log(kx) + (Math.log(bx) - Math.log(kx)) * w); ky = Math.exp(Math.log(ky) + (Math.log(by) - Math.log(ky)) * w);
    }
    const sm = ease(u);
    const cx = cA[0] + (cB[0] - cA[0]) * sm, cy = cA[1] + (cB[1] - cA[1]) * sm;
    const ox = v.css[0] + v.css[2] / 2, oy = v.css[1] + v.css[3] / 2;
    const g = smooth(u / 0.22);
    if (s.imB) s.imB.style.opacity = g.toFixed(3);
    s.wholeA.style.opacity = (1 - g).toFixed(3);
    if (s.wholeB) s.wholeB.style.opacity = w.toFixed(3);   // the black past the new map's edge comes back as the view settles
    s.snapA.style.opacity = (1 - w).toFixed(3);              // and the hero is only where they came in
    s.wd.style.transform = "translate(" + ox.toFixed(2) + "px," + oy.toFixed(2) + "px) scale(" + kx.toFixed(5) + "," + ky.toFixed(5) + ") translate(" + (-cx).toFixed(2) + "px," + (-cy).toFixed(2) + "px)";
  }
  // Ease in a little (the hero was already moving), ease out into the new view.
  const ease = (u) => { u = Math.max(0, Math.min(1, u)); const a = 0.35; return u < a ? u * u / a : a + 2 * (u - a) - (u - a) * (u - a) / (1 - a); };
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
    let rate = 1 / s.dur;
    if (!s.haveB) { const room = T_WAIT - s.t; rate *= room > 0.12 ? 1 : Math.max(0.04, room / 0.12); }
    else rate = Math.min(rate, (1 - s.uR) / 0.3);   // settle on the new picture over at least 0.3 s
    if (pin !== null) { s.t = pin; s.born = now; } else s.t = Math.min(s.haveB ? 1 : T_WAIT, s.t + dt * rate);
    move(s.t);
    if (s.haveB && s.t >= 1 && now - s.gotB > 200) { finish(true); return; }
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
      if (hero) { trail.push([hero[0], hero[1], cur]); if (trail.length > 12) trail.shift(); }
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
      s.camBact = view.cam; s.uR = s.t; s.view = view; s.gotB = performance.now();
      s.wholeB = s.twin(snap, view.cam, s.to, 0, s.B.x + view.cam[0], s.B.y + view.cam[1]); s.wholeB.style.opacity = "0";
      snap.style.opacity = "0"; requestAnimationFrame(() => { snap.style.opacity = "1"; });
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
