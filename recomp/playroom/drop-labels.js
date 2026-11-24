  // v263 Item names on the ground, Diablo 2 style (Jordan, 2026-11-24: "items dont even display properly anymore they
  // should atleast have rarity and name above them when they drop like diablo 2").
  // Why names went missing: the game writes the name of the item under the hero into its own bottom bar, and the HD HUD
  // (v224) covers that bar. Now every item lying in view gets its name above it on a dark plate, coloured by tier:
  //   white  = plain gear, gems, food and herbs      blue   = magic (a prefix or a suffix)
  //   yellow = rare (a prefix and a suffix)          gold   = unique (the game's named uniques, cat 14)
  //   green  = set (kept for the Three Dwarf Rings, Phase 7)
  // A small gold arrow in front of the name marks gear that beats what the hero wears (window.__goldGear, the same test
  // as the gold border in the Backpack). The plate of the item at the hero's feet (what the game's bar used to name)
  // gets a gold edge. Labels that would overlap stack upward like Diablo 2's.
  // Names: gear from the game file's item tables (prefix + base + suffix, like the Forge); gems, food and herbs from the
  // game's own pickup texts (581-587: "A Gem", "A Pile of @1 Gems", "Some Fruit", "Some Mushrooms", "Dried Kingsfoil
  // Herbs", "Fresh Kingsfoil Herbs", "Lembas Bread"). Ground items: update fn 0x0802F131, +0x63 == 3 lying, +0x60 type
  // (14 gems, 15 fruit, 16 mushrooms, 17 dried / 18 fresh Kingsfoil, 19 lembas, 25+ gear), +0x88 the item word
  // (gear) or the gem count in bits 8-15, x/y +0xAE/+0xB2. Drawn on its own canvas over the game picture (same place
  // as the hit effects, window.__fxView), so it works in 1-player, P2 and online alike. window.__dropLabelsOff = 1 hides.
  (() => {
    const R = () => window.__romFull;
    const U8 = (o) => R()[o], U16 = (o) => R()[o] | R()[o + 1] << 8;
    const U32 = (o) => (R()[o] | R()[o + 1] << 8 | R()[o + 2] << 16 | R()[o + 3] << 24) >>> 0;
    const TXT = {};
    const text = (id) => {   // tools/text.py
      if (id in TXT) return TXT[id];
      const r = R(), bank = U32(0x289A10) - 0x08000000, tree = bank + 4, table = tree + U32(bank);
      let p = bank + U32(table + 4 * id), node = 0x100, bit = 0, byte = r[p++], s = "";
      for (let n = 0; n < 300; n++) {
        while (node > 0xFF) { const e = tree + (node - 0x100) * 4; node = U16((byte >> bit) & 1 ? e + 2 : e); if (++bit === 8) { bit = 0; byte = r[p++]; } }
        if (!node) break;
        s += String.fromCharCode(node); node = 0x100;
      }
      return (TXT[id] = s);
    };
    const CNT = [18, 11, 9, 11, 10, 4, 13, 10, 24, 8, 12, 9, 8, 7, 53];
    const catw = (c, k) => U32(0x68F50 + c * 0x28 + 4 * k) - 0x08000000;
    const NAMES = new Map();
    const gearName = (w) => {
      if (NAMES.has(w)) return NAMES.get(w);
      let s = "";
      try {
        const c = w & 15, i = (w >>> 8) & 255, pre = (w >>> 16) & 255, suf = w >>> 24, nm = (e) => text(U16(e) - 1);
        if (c <= 14 && i < CNT[c]) s = [pre !== 255 && c !== 7 && c !== 14 ? nm(catw(c, 2) + 12 * pre) : "", nm(catw(c, 0) + 12 * i), suf !== 255 && c !== 14 ? nm(catw(c, 5) + 12 * suf) : ""].filter(Boolean).join(" ");
      } catch (e) { s = ""; }
      NAMES.set(w, s); return s;
    };
    // Tiers, Diablo 2's colours brightened a little for a small screen.
    const TIER = { n: "#ece6d8", m: "#7f93ff", r: "#f3e45a", u: "#d9b25e", s: "#4fd16a" };
    const tierOf = window.__itemTier = (w) => {
      if (w === 0xFFFFFFFF || !w || (w & 15) === 15) return "n";
      if ((w & 0xFFFF) === 0x17FE) return (w >>> 16) === 0xFFFF ? "n" : ["n", "m", "r"][w >>> 30] || "n";   // Orc Heads: their own 3 tiers
      const c = w & 15;
      if (c === 14) return "u";
      if (c === 7) return "n";
      const pre = ((w >>> 16) & 255) !== 255, suf = (w >>> 24) !== 255;
      return pre && suf ? "r" : pre || suf ? "m" : "n";
    };
    window.__itemTierColor = (w) => TIER[tierOf(w)];
    window.__itemNameOf = gearName;
    const labelOf = (t, w) => {
      if (t >= 25) { const s = gearName(w); return s ? { s, c: TIER[tierOf(w)], w } : null; }
      if (t === 14) { const n = (w >>> 8) & 255; return { s: n > 1 ? text(582).replace("@1", n) : text(581), c: TIER.n }; }
      if (t >= 15 && t <= 19) return { s: text(583 + t - 15), c: TIER.n };
      return null;
    };
    const st = { view: null, cv: null, ctx: null, raf: 0 };
    const prevFx = window.__fxView;
    window.__fxView = function (w, h, sx, sy, sw, sh, dest, CW, CH, host) {
      st.view = { w, h, sx, sy, sw, sh, k: dest[2] / sw, ky: dest[3] / sh, ox: dest[0], oy: dest[1], CW, CH, host };
      if (prevFx) return prevFx.apply(this, arguments);
    };
    const ensure = (host) => {
      if (st.cv && st.cv.isConnected && st.cv.previousElementSibling && (st.cv.previousElementSibling === host || st.cv.previousElementSibling.id === "fxCanvas")) return true;
      if (!host || !host.parentElement) return false;
      if (st.cv) st.cv.remove();
      const c = document.createElement("canvas"); c.id = "dropLabels";
      c.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:4";
      const fx = document.getElementById("fxCanvas");
      (fx && fx.previousElementSibling === host ? fx : host).after(c); st.cv = c; st.ctx = c.getContext("2d"); return true;
    };
    const read = (w, h) => {
      const M = window.__wideM; if (!M || !M._rotk_iwram || !R()) return null;
      // online: this player's own game (the same choice as the Backpack page); 1-player and a local P2 game: the shown game
      const onl = !!(window.__mp && window.__mp.online && M._rotk_link_iwram), me = onl ? window.__mp.me & 1 : 0;
      const H8 = M.HEAPU8, ib = onl ? M._rotk_link_iwram(me) : M._rotk_iwram(), eb = onl ? M._rotk_link_ewram(me) : M._rotk_ewram(), dv = new DataView(H8.buffer);
      if (!ib || H8[ib + 0x41B0] !== 1) return null;
      const at = (q) => q >= 0x2000000 && q < 0x2040000 ? eb + (q - 0x2000000) : q >= 0x3000000 && q < 0x3008000 ? ib + (q - 0x3000000) : 0;
      const r32 = (q) => { const o = at(q); return o ? dv.getUint32(o, true) : 0; };
      let p = dv.getUint32(ib + 0x3C00, true), n = 0; if (!at(p)) return null;
      while (n++ < 400) { const nx = r32(p); if (!at(nx)) break; p = nx; }
      const cx = dv.getInt32(ib + 0x20F8, true) - (w - 240) / 2, cy = dv.getInt32(ib + 0x20FC, true) - (h - 160) / 2, out = [];
      const pi = H8[ib + 0x3F59] & 1, P = ib + 0x3C00 + 0x1AC * pi, hero = at(dv.getUint32(P, true));
      const hx = hero ? dv.getInt16(hero + 0xAE, true) : -1e5, hy = hero ? dv.getInt16(hero + 0xB2, true) : -1e5;
      const hid = H8[P + 0x19F], worn = []; for (let k = 0; k < 8; k++) worn.push(dv.getUint32(P + 0x3C + 4 * k, true));
      n = 0; while (at(p) && n++ < 400 && out.length < 24) {
        const o = at(p);
        if (dv.getUint32(o + 0x14, true) === 0x0802f131 && H8[o + 0x63] === 3) {
          const x = dv.getInt16(o + 0xAE, true), y = dv.getInt16(o + 0xB2, true);
          if (x - cx > -40 && x - cx < w + 40 && y - cy > -20 && y - cy < h + 30)
            out.push({ x, y, t: H8[o + 0x60], w: dv.getUint32(o + 0x88, true), feet: Math.abs(x - hx) <= 10 && Math.abs(y - hy) <= 10 });
        }
        p = r32(p + 4);
      }
      return { cx, cy, out, hid, worn, lv: H8[P + 0x19C] + 1 };
    };
    const rr = (x, X, Y, W, H, r) => { x.beginPath(); x.moveTo(X + r, Y); x.arcTo(X + W, Y, X + W, Y + H, r); x.arcTo(X + W, Y + H, X, Y + H, r); x.arcTo(X, Y + H, X, Y, r); x.arcTo(X, Y, X + W, Y, r); x.closePath(); };
    const frame = () => {
      st.raf = requestAnimationFrame(frame);
      const v = st.view; if (!v || !v.host) return;
      if (!ensure(v.host)) return;
      const c = st.cv, x = st.ctx;
      if (c.width !== v.CW || c.height !== v.CH) { c.width = v.CW; c.height = v.CH; }
      x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, c.width, c.height);
      if (window.__dropLabelsOff || window.__hdBpOn || window.__hdShopOn || window.__hdPgOn) return;
      let r = null; try { r = read(v.w, v.h); } catch (e) { r = null; }
      if (!r || !r.out.length) return;
      const tr = v.host.style.translate; if (c.style.translate !== tr) c.style.translate = tr;
      const css = c.clientWidth ? c.width / c.clientWidth : 1;   // canvas pixels per CSS pixel
      const fs = Math.round(Math.max(10.5, Math.min(13, v.k / css * 5.2)) * css), pad = Math.round(fs * 0.38), lh = Math.round(fs * 1.42);
      x.font = "600 " + fs + "px Manrope, 'Segoe UI', system-ui, sans-serif"; x.textBaseline = "middle"; x.textAlign = "left";
      const X = (gx) => v.ox + (gx - r.cx - v.sx) * v.k, Y = (gy) => v.oy + (gy - r.cy - v.sy) * v.ky;
      const L = [];
      for (const it of r.out) {
        const lb = labelOf(it.t, it.w); if (!lb) continue;
        const up = lb.w !== undefined && window.__goldGear && (() => { try { return window.__goldGear(lb.w, r.worn, r.hid) && !(window.__goldGear.cant && window.__goldGear.cant(lb.w, r.hid, r.lv)); } catch (e) { return false; } })();
        const tw = x.measureText(lb.s).width, aw = up ? fs * 0.9 : 0, W = Math.ceil(tw + aw + 2 * pad), H = lh;
        // over the item; the one at the hero's feet goes just under it, so it doesn't cover the hero
        L.push({ ...lb, up, feet: it.feet, W, H, ax: X(it.x), y0: it.feet ? Y(it.y + 5) + H : Y(it.y - 13), gy: it.feet ? 1e6 : it.y });
      }
      // nearer the bottom of the screen first, so stacks grow upward like Diablo 2's
      L.sort((a, b) => b.gy - a.gy || a.ax - b.ax);
      const placed = [], clipT = v.oy, clipB = v.oy + v.sh * v.ky, clipL = v.ox, clipR = v.ox + v.sw * v.k;
      for (const l of L) {
        let lx = Math.round(Math.min(Math.max(l.ax - l.W / 2, clipL + 2), clipR - l.W - 2)), ly = Math.round(l.y0 - l.H);
        for (let g = 0; g < 12; g++) {
          const hit = placed.find((q) => lx < q.x + q.W + 2 && lx + l.W + 2 > q.x && ly < q.y + q.H + 2 && ly + l.H + 2 > q.y);
          if (!hit) break; ly = hit.y - l.H - 2;
        }
        if (ly < clipT || ly + l.H > clipB) continue;
        placed.push({ x: lx, y: ly, W: l.W, H: l.H });
        x.globalAlpha = 1;
        rr(x, lx, ly, l.W, l.H, Math.round(fs * 0.22)); x.fillStyle = "rgba(8,7,6,0.72)"; x.fill();
        if (l.feet) { x.lineWidth = Math.max(1, Math.round(css)); x.strokeStyle = "rgba(246,214,140,0.9)"; x.stroke(); }
        let tx = lx + pad;
        if (l.up) { x.fillStyle = "#ffd23a"; x.beginPath(); const s = fs * 0.62, cx0 = tx + s / 2, cy0 = ly + l.H / 2; x.moveTo(cx0, cy0 - s * 0.55); x.lineTo(cx0 + s / 2, cy0 + s * 0.4); x.lineTo(cx0 - s / 2, cy0 + s * 0.4); x.closePath(); x.fill(); tx += fs * 0.9; }
        x.fillStyle = "rgba(0,0,0,0.9)"; x.fillText(l.s, tx + Math.max(1, css * 0.8), ly + l.H / 2 + Math.max(1, css * 0.8));
        x.fillStyle = l.c; x.fillText(l.s, tx, ly + l.H / 2);
      }
    };
    st.raf = requestAnimationFrame(frame);
    window.__dropLabels = { st, read: () => st.view && read(st.view.w, st.view.h), labelOf };
  })();
