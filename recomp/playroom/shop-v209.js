  // v203 HD Forge / Shrine (Jordan, 2026-11-20: "There are no items for sale, you could randomly generate items there"
  // / "the leave button serves no purpose and isn't accessible" / "notice how I can't access certain things at the
  // forge"). The page draws the shop over the game's own (v181) and now:
  // - keeps its own cursor over everything on the screen: the shop's goods, the gear for sale, all 12 backpack boxes
  //   and Leave. The joystick / d-pad / arrow keys move that cursor (the game's own cursor only knew 8 boxes and the
  //   goods); the page then walks the game's cursor to the same box (closed loop, so it also works where the Forge's
  //   map differs from the Shrine's), so A buys or sells through the game exactly as before.
  // - Forges sell random gear (rolled from the game's own item tables for the hero who is shopping, up to their level):
  //   names, stats and Min. Level are read from the game file, the price is 5x what the game pays when
  //   you sell it. A on one asks "Buy ... ?" (Yes / No); buying puts the item in the first free backpack box and
  //   takes the gems, then closes and reopens the shop behind the picture so the game sees it. A forge keeps its
  //   stock until you leave the level.
  // - v209 (Jordan, 2026-11-20: "change the leave button in the forge menu to sell all, have it sell all inventory at the
  //   same time, make sure it prompts you to ask if you are sure first when you select it and show the amount you will
  //   receive"): the button under the backpack is Sell All (B still leaves). A on it first asks the game what each
  //   item in the 12 boxes is worth (the game's own "That is worth N gems", A then No on each box, behind the
  //   picture; values are remembered per item), then asks "Sell all N items for T gems?" with the list. Yes empties
  //   the boxes and adds the gems in one go, then closes and reopens the shop behind the picture like a purchase.
  // Works in 1-player, P2 and online (page writes go through __mirrorIw / travel with the buttons since v180).
  // See recomp/playroom/shop-v203.py, shop-v209.py.
  (function hdShop() {
    const CNT = [18, 11, 9, 11, 10, 4, 13, 10, 24, 8, 12, 9, 8, 7, 53], START = [];
    { let s = 0; for (const c of CNT) { START.push(s); s += c; } }
    // the game's shop cursor moves (measured at the Shrine: 0-7 backpack, 8-10 goods); the Forge has goods 8-9 only
    const NAV3 = { 7: [1, 2, 3, 8, 5, 6, 7, 8, 9, 10, 0], 6: [10, 0, 1, 2, 10, 4, 5, 6, 3, 8, 9], 4: [4, 5, 6, 7, 0, 1, 2, 3, 8, 9, 10], 5: [4, 5, 6, 7, 0, 1, 2, 3, 8, 9, 10] };
    const NAV2 = { 7: [1, 2, 3, 8, 5, 6, 7, 8, 9, 0], 6: [9, 0, 1, 2, 9, 4, 5, 6, 3, 8], 4: [4, 5, 6, 7, 0, 1, 2, 3, 8, 9], 5: [4, 5, 6, 7, 0, 1, 2, 3, 8, 9] };
    const INV = [8, 9, 10, 11, 12, 13, 14, 30, 31, 32, 33, 34];
    const SHOP_UPD = 0x080200c9;
    const GOODS = { 0: ["Whetstone", "Mystery item"], 2: ["Attribute Point", "Skill Point", "Kingsfoil Herb"] };
    const NSTOCK = 6;
    const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
    const str = (H8, o, n) => { let s = ""; for (let i = 0; i < n; i++) { const c = H8[o + i]; if (!c) break; s += String.fromCharCode(c); } return s; };
    const on = () => true;   // v186: always (Jordan: no old item menu)
    let own = 0;
    const gi = (id, v) => { own++; try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} own--; };
    const sync = () => !!(window.__mp && window.__mp.sync);
    const press = (id, ms = 70) => { const go = () => { gi(id, 1); setTimeout(() => gi(id, 0), ms); }; if (sync()) setTimeout(go, 50); else go(); };
    const pic = (w) => {
      if (w === 0xFFFFFFFF || w === 0 || (w & 15) === 15) return "";
      const cat = w & 15, idx = (w >>> 8) & 255;
      if (cat > 14 || idx >= CNT[cat]) return "";
      const n = START[cat] + idx;
      return '<i class="hp" style="background-position:' + ((n % 16) / 15 * 100).toFixed(3) + "% " + (Math.floor(n / 16) / 12 * 100).toFixed(3) + '%"></i>';
    };
    const empty = (w) => w === 0 || w === 0xFFFFFFFF || (w & 15) === 15;

    // ---- the game file's item tables (same layout as recomp/auto/auto.js) and texts (tools/text.py) ----
    const ROM = () => window.__romFull;
    const U8 = (o) => ROM()[o];
    const U16 = (o) => { const R = ROM(); return R[o] | R[o + 1] << 8; };
    const U32 = (o) => { const R = ROM(); return (R[o] | R[o + 1] << 8 | R[o + 2] << 16 | R[o + 3] << 24) >>> 0; };
    const S8 = (v) => (v > 127 ? v - 256 : v);
    const TXT = {};
    const text = (id) => {
      if (id in TXT) return TXT[id];
      const R = ROM(), bank = U32(0x289A10) - 0x08000000, tree = bank + 4, table = tree + U32(bank);
      let p = bank + U32(table + 4 * id), node = 0x100, bit = 0, byte = R[p++], s = "";
      for (let n = 0; n < 300; n++) {
        while (node > 0xFF) { const e = tree + (node - 0x100) * 4; node = U16((byte >> bit) & 1 ? e + 2 : e); if (++bit === 8) { bit = 0; byte = R[p++]; } }
        if (!node) break;
        s += String.fromCharCode(node); node = 0x100;
      }
      return (TXT[id] = s);
    };
    const catw = (c, k) => U32(0x68F50 + c * 0x28 + 4 * k) - 0x08000000;
    const iflags = (c, i) => U32(catw(c, 8) + 8 * i);
    const split = (it) => ({ c: it & 15, i: (it >>> 8) & 255, pre: (it >>> 16) & 255, suf: it >>> 24 });
    const ents = (it) => {   // base, prefix, suffix records (12 bytes: u16 name text + 1, level, 4 stat pairs)
      const { c, i, pre, suf } = split(it), o = [catw(c, 0) + 12 * i];
      if (pre !== 255 && c !== 7) o.push(catw(c, 2) + 12 * pre);
      if (suf !== 255) o.push(catw(c, 5) + 12 * suf);
      return o;
    };
    const reqLevel = (it) => {   // the game's own sum (0x0802D2F8)
      const { c, i, pre, suf } = split(it), f = iflags(c, i);
      let r = U8(catw(c, 0) + 12 * i + 2);
      if (f & 0x80) r += 5; if (f & 0x100) r += 5;
      if (pre !== 255 && c !== 7) { r += U8(catw(c, 2) + 12 * pre + 2) >> 1; const pf = U32(catw(c, 3) + 4 * pre); r += 5 * !!(pf & 1) + 5 * !!(pf & 2); }
      if (suf !== 255) { r += U8(catw(c, 5) + 12 * suf + 2); const sf = U32(catw(c, 6) + 4 * suf); r += 5 * !!(sf & 1) + 5 * !!(sf & 2); }
      if (f & 0x10000) r = 1;
      return r & 255;
    };
    const itemName = (it) => {   // "Sharpened Flint Knife of the Moon"
      const { c, i, pre, suf } = split(it), nm = (e) => text(U16(e) - 1);
      return [pre !== 255 && c !== 7 ? nm(catw(c, 2) + 12 * pre) : "", nm(catw(c, 0) + 12 * i), suf !== 255 ? nm(catw(c, 5) + 12 * suf) : ""].filter(Boolean).join(" ");
    };
    const statNames = (e) => { const o = []; for (let k = 3; k < 11; k += 2) { const s = U8(e + k); if (s !== 0x5a) o.push(text(329 + s)); } return o; };
    const cursed = (e) => statNames(e).includes("Cursed");
    const itemStats = (it) => {
      const sum = new Map();
      for (const e of ents(it)) for (let k = 3; k < 11; k += 2) { const s = U8(e + k); if (s !== 0x5a) sum.set(s, (sum.get(s) || 0) + S8(U8(e + k + 1))); }
      const out = [];
      for (const [s, v] of sum) {
        if (!v) continue;
        const nm = text(329 + s);
        if (!nm) continue;
        if (nm === "Cheap" || nm === "Cursed") { out.push(nm); continue; }
        if (s <= 3 && v > 0) out.push(Math.max(1, v >> 1) + "-" + v + " " + nm);
        else out.push((v > 0 ? "+" : "") + v + (nm[0] === "%" ? "" : " ") + nm);
      }
      return out;
    };
    // what the game pays when you sell (measured: 3 x Min. Level + a little per kind of item); the Forge asks 5x that
    const SELLB = { 0: 5, 1: 8, 2: 7, 3: 6, 4: 6, 5: 8, 6: 9, 8: 15, 9: 7, 10: 26, 11: 4, 12: 2, 13: 1 };
    const price = (it) => Math.max(30, Math.round((3 * reqLevel(it) + (SELLB[it & 15] || 6))) * 5);
    const roll = (heroId, HL, n) => {
      const cats = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13], out = [];
      for (let t = 0; out.length < n && t < 600; t++) {
        const c = cats[Math.floor(Math.random() * cats.length)], i = Math.floor(Math.random() * CNT[c]), f = iflags(c, i);
        if (f & 0x10000) continue;                                       // backpack-only items
        if (heroId < 6 && !(f & (1 << (26 + heroId)))) continue;         // only gear this hero can wear
        let pre = 255, suf = 255;
        const mk = () => ((suf << 24) | (pre << 16) | (i << 8) | c) >>> 0;
        if (reqLevel(mk()) > HL) continue;
        if (Math.random() < 0.6) {                                       // a prefix (the general ones, not the hero ones)
          const lim = U8(catw(c, 1)) || 0, p = Math.floor(Math.random() * lim);
          if (lim && U32(catw(c, 3) + 4 * p) === 0 && !cursed(catw(c, 2) + 12 * p)) { pre = p; if (reqLevel(mk()) > HL) pre = 255; }
        }
        if (Math.random() < 0.45) {                                      // a suffix
          const lim = Math.floor((catw(c, 6) - catw(c, 5)) / 12), s = Math.floor(Math.random() * lim);
          if (lim > 0 && lim < 256 && U32(catw(c, 6) + 4 * s) === 0 && !cursed(catw(c, 5) + 12 * s)) { suf = s; if (reqLevel(mk()) > HL) suf = 255; }
        }
        const it = mk();
        if (reqLevel(it) < HL - 2 && Math.random() < 0.75) continue;    // mostly gear near the hero's level
        if (out.includes(it) || !itemName(it)) continue;
        out.push(it);
      }
      out.sort((a, b) => price(a) - price(b));
      return out;
    };
    const stocks = new Map();
    let stockLevel = -1;

    // names / prices the shop showed for its goods (shown when the game's cursor is on them), by shop kind
    let goodsName = {}; try { goodsName = JSON.parse(localStorage.getItem("rotk-goods2") || "{}"); } catch (e) {}
    let sa = null; const worth = new Map();   // v209 Sell All: its state; what the game pays for each item word
    let el = null, last = "", ctx = null, hc = null, open = false, hold = 0, ask = null, note = "", noteT = 0, goTok = 0, kindNow = 2, vendorAt = "";
    const rep = { id: -1, t: 0, n: 0 };

    // ---- the page's cursor: rows of boxes ----
    const rows = () => {
      const R = [];
      const ng = kindNow === 0 ? 2 : 3;
      R.push([8, 9, 10].slice(0, ng).map((g) => "g" + g));
      const st = ctx && ctx.stock;
      if (st && st.length) { const s = st.map((_, k) => "s" + k); for (let k = 0; k < s.length; k += 3) R.push(s.slice(k, k + 3)); }
      R.push(INV.slice(0, 4).map((c) => "c" + c), INV.slice(4, 8).map((c) => "c" + c), INV.slice(8, 12).map((c) => "c" + c));
      R.push(["all"]);
      return R;
    };
    const findRC = (id) => { const R = rows(); for (let r = 0; r < R.length; r++) { const c = R[r].indexOf(id); if (c >= 0) return [r, c, R]; } return [-1, -1, R]; };
    const gameTarget = (id) => {   // the game's cursor for a page box, or -1
      if (!id) return -1;
      if (id[0] === "g") return +id.slice(1);
      if (id[0] === "c") { const c = +id.slice(1); return c >= 30 ? 7 : c - 8; }
      return -1;
    };
    const fromGame = (s) => (s >= 8 ? "g" + s : s === 7 ? "c" + (30 + (ctx ? ctx.win : 0)) : "c" + (s + 8));
    const curNow = () => {
      if (!ctx) return 255;
      const H8 = ctx.M.HEAPU8, iw = ctx.iw, ew = ctx.ew, ui = (H8[iw + 0x1C90] | H8[iw + 0x1C91] << 8 | H8[iw + 0x1C92] << 16 | H8[iw + 0x1C93] << 24) >>> 0;
      return ui >>> 24 === 2 ? H8[ew + (ui & 0x3ffff) + 0x62] : ui >>> 24 === 3 ? H8[iw + (ui & 0x7fff) + 0x62] : 255;
    };
    const route = (a, b) => {   // shortest d-pad presses from the game's cursor a to b
      const NAV = kindNow === 0 ? NAV2 : NAV3;
      const prev = { [a]: null }, q = [a];
      while (q.length) { const c = q.shift(); if (c === b) break; for (const k of [7, 6, 4, 5]) { const n = NAV[k][c]; if (n !== undefined && !(n in prev)) { prev[n] = [c, k]; q.push(n); } } }
      const s = []; let c = b; while (prev[c]) { s.unshift(prev[c][1]); c = prev[c][0]; } return s;
    };
    // walk the game's cursor to t, one press at a time, re-reading where it really went
    const goTo = (t, then) => {
      const tok = ++goTok; let n = 0;
      const step = () => {
        if (tok !== goTok || !ctx || !open) return;
        const s = curNow();
        if (s === t) { if (then) then(); return; }
        if (n++ > 12 || s > 10) return;
        const r = route(s, t); if (!r.length) return;
        press(r[0]);
        setTimeout(step, sync() ? 260 : 160);
      };
      step();
    };
    // put the game's cursor under the page's box (a stash box first goes into cell 15, like a tap)
    const follow = (then) => {
      if (!ctx || !hc) return;
      if (hc[0] === "c") {
        const c = +hc.slice(1);
        if (c >= 30 && c - 30 !== ctx.win) {
          ctx.M.HEAPU8[ctx.ew + 0x3F605] = c - 30 + 1;   // SWIN (tools/orcslots shop_keys)
          const tok = ++goTok;
          const s = curNow();
          const seq = s === 7 ? [6, 7] : route(s, 7);
          let k = 0; const go = () => { if (tok !== goTok) return; if (k < seq.length) { press(seq[k++]); setTimeout(go, sync() ? 260 : 160); } else goTo(7, then); }; go();
          return;
        }
      }
      const t = gameTarget(hc);
      if (t >= 0) goTo(t, then); else { ++goTok; if (then) then(); }
    };
    const setNote = (s) => { note = s; noteT = performance.now() + 2600; last = ""; };
    const move = (dir) => {
      const [r, c, R] = findRC(hc);
      if (r < 0) { hc = R[R.length - 2][0]; follow(); last = ""; return; }
      if (sa) return;
      let nr = r, nc = c;
      if (dir === 6) nc = Math.max(0, c - 1);
      else if (dir === 7) nc = Math.min(R[r].length - 1, c + 1);
      else {
        nr = Math.max(0, Math.min(R.length - 1, r + (dir === 4 ? -1 : 1)));
        if (nr !== r) nc = R[r].length === 1 ? Math.floor((R[nr].length - 1) / 2) : Math.round(c / Math.max(1, R[r].length - 1) * (R[nr].length - 1));
      }
      const id = R[nr][nc];
      if (id === hc) return;
      hc = id; ask = null; last = "";
      follow();
    };
    // A on the page's box
    const act = () => {
      if (!ctx || !hc) return;
      if (hc === "all") { sellAll(); return; }
      if (hc[0] === "s") {
        const k = +hc.slice(1), it = ctx.stock[k];
        if (!it) return;
        if (ctx.gems < price(it)) { setNote("Not enough gems"); return; }
        ask = { k, sel: 0 }; last = "";
        return;
      }
      if (ctx.sub !== 0) return;
      follow(() => press(8));
    };
    const buy = (k) => {
      ask = null; last = "";
      if (!ctx) return;
      const it = ctx.stock[k]; if (!it) return;
      const pr = price(it), H8 = ctx.M.HEAPU8, hero = ctx.hero;
      const gems = H8[hero + 0x184] | H8[hero + 0x185] << 8;
      if (gems < pr) { setNote("Not enough gems"); return; }
      let slot = -1;
      for (let i = 8; i < 16; i++) { const o = hero + 0x3C + 4 * i, w = (H8[o] | H8[o + 1] << 8 | H8[o + 2] << 16 | H8[o + 3] << 24) >>> 0; if (empty(w)) { slot = i; break; } }
      if (slot < 0) { setNote("No room in your backpack"); return; }
      const o = hero + 0x3C + 4 * slot;
      H8[o] = it & 255; H8[o + 1] = (it >>> 8) & 255; H8[o + 2] = (it >>> 16) & 255; H8[o + 3] = it >>> 24;
      const g = gems - pr; H8[hero + 0x184] = g & 255; H8[hero + 0x185] = g >> 8;
      try { if (window.__mirrorIw) { for (let j = 0; j < 4; j++) window.__mirrorIw(o - ctx.iw + j); window.__mirrorIw(hero + 0x184 - ctx.iw); window.__mirrorIw(hero + 0x185 - ctx.iw); } } catch (e) {}
      ctx.stock[k] = 0;
      setNote("Bought " + itemName(it));
      reopen();
    };
    // the shop only reads the backpack when it opens: close and open it again behind the picture
    const reopen = () => {
      hold = performance.now() + 5000;
      const keep = hc; let phase = 0, nextR = 0, tries = 0;
      press(0);
      const tick = () => {
        if (!hold) return;
        const s = ctx.M.HEAPU8[ctx.iw + 0x41B0], now = performance.now();
        if (phase === 0 && s !== 20) { phase = 1; nextR = now + 250; }
        if (phase === 1 && s !== 20 && now >= nextR && tries < 4) { tries++; press(11, 110); nextR = now + 700; }   // Grab opens it again
        if (phase === 1 && s === 20 && curNow() <= 10) { hold = 0; hc = keep; last = ""; return; }
        if (performance.now() > hold) { hold = 0; last = ""; return; }
        setTimeout(tick, 60);
      };
      setTimeout(tick, 60);
    };
    // ---- v209 Sell All ----
    const wSet = (o, w) => { const H8 = ctx.M.HEAPU8; H8[o] = w & 255; H8[o + 1] = (w >>> 8) & 255; H8[o + 2] = (w >>> 16) & 255; H8[o + 3] = w >>> 24; };
    const wGet = (o) => { const H8 = ctx.M.HEAPU8; return (H8[o] | H8[o + 1] << 8 | H8[o + 2] << 16 | H8[o + 3] << 24) >>> 0; };
    const boxAt = (c) => {   // where a box's item word lives (the stash window shows in hero word 15)
      const p = ctx.M.HEAPU8[ctx.iw + 0x3F59] & 1;
      if (c < 30) return { o: ctx.hero + 0x3C + 4 * c, iw: true };
      if (c - 30 === ctx.win) return { o: ctx.hero + 0x3C + 4 * 15, iw: true, also: ctx.ew + 0x3F840 + 20 * p + 4 * (c - 30) };
      return { o: ctx.ew + 0x3F840 + 20 * p + 4 * (c - 30), iw: false };
    };
    const gameWorth = () => {   // the game's "That is worth N gems", while it asks about a box
      const m = window.__gameText(ctx.M.HEAPU8, ctx.ew).filter((q) => q.x >= 112 && q.y >= 64).map((q) => q.s).join(" ").match(/worth (\d+) gems/i);
      return m ? +m[1] : -1;
    };
    const asking = () => { const H8 = ctx.M.HEAPU8; return H8[ctx.iw + 0x41C0] === 2 || window.__gameText(H8, ctx.ew).some((q) => q.x >= 112 && q.y >= 64 && /\?$/.test(q.s)); };
    const sellAll = () => {
      if (!ctx || sa || ctx.sub !== 0) return;
      const list = [];
      for (const c of INV) { const w = wGet(boxAt(c).o); if (!empty(w) && pic(w)) list.push({ c, w, v: worth.has(w) ? worth.get(w) : -1 }); }
      if (!list.length) { setNote("Your backpack is empty"); return; }
      sa = { phase: "count", list, i: 0, sel: 0, tok: ++goTok }; last = "";
      probe();
    };
    // ask the game what one box is worth: walk there, A, read the worth, B (= No)
    const probe = () => {
      if (!sa || sa.phase !== "count" || !ctx || !open) return;
      while (sa.i < sa.list.length && sa.list[sa.i].v >= 0) sa.i++;
      if (sa.i >= sa.list.length) { sa.list = sa.list.filter((x) => x.v >= 0); hc = "all"; ++goTok; last = ""; if (!sa.list.length) { sa = null; setNote("The " + (kindNow === 0 ? "Forge" : "Shrine") + " won't buy these"); return; } sa.phase = "ask"; sa.sel = 0; return; }
      const it = sa.list[sa.i], me = sa; last = "";
      hc = "c" + it.c;
      const t0 = performance.now(); let pressed = 0, said = 0;
      let fin = 0; const next = () => { if (fin++ || sa !== me) return; sa.i++; setTimeout(probe, sync() ? 200 : 120); };
      const wait = () => {
        if (sa !== me || !ctx || !open) return;
        const now = performance.now();
        if (said) { if (!asking() && ctx.M.HEAPU8[ctx.iw + 0x41C0] === 0) return next(); if (now - said > 2500) { said = now; press(0); } return setTimeout(wait, 60); }
        const v = gameWorth();
        if (v >= 0 && asking()) { it.v = v; worth.set(it.w, v); said = now; press(0); return setTimeout(wait, 60); }
        if (pressed && now - pressed > 1800) { if (asking()) { said = now; press(0); return setTimeout(wait, 60); } return next(); }   // no price: not for sale
        if (now - t0 > 6000) return next();
        setTimeout(wait, 60);
      };
      follow(() => { if (sa !== me || fin) return; pressed = performance.now(); press(8); });   // the one wait loop below sees it
      setTimeout(wait, 60);
    };
    const saTotal = () => sa ? sa.list.reduce((a, x) => a + Math.max(0, x.v), 0) : 0;
    const saCancel = () => { if (!sa) return; const was = sa.phase; sa = null; ++goTok; last = ""; if (was === "count" && ctx && asking()) press(0); hc = "all"; };
    const sellAllYes = () => {
      const me = sa; sa = null; last = "";
      if (!ctx || !me) return;
      const H8 = ctx.M.HEAPU8, hero = ctx.hero, iw = ctx.iw;
      let got = 0, n = 0;
      const ewDirty = [];
      for (const it of me.list) {
        const b = boxAt(it.c);
        if (wGet(b.o) !== it.w) continue;   // moved since the count
        wSet(b.o, 0xFFFFFFFF);
        if (b.also !== undefined) { wSet(b.also, 0xFFFFFFFF); ewDirty.push(b.also); }
        if (b.iw) { try { if (window.__mirrorIw) for (let j = 0; j < 4; j++) window.__mirrorIw(b.o - iw + j); } catch (e) {} }
        else ewDirty.push(b.o);
        got += it.v; n++;
      }
      if (!n) { setNote("Nothing sold"); return; }
      const gems = Math.min(65535, (H8[hero + 0x184] | H8[hero + 0x185] << 8) + got);
      H8[hero + 0x184] = gems & 255; H8[hero + 0x185] = gems >> 8;
      try { if (window.__mirrorIw) { window.__mirrorIw(hero + 0x184 - iw); window.__mirrorIw(hero + 0x185 - iw); } } catch (e) {}
      try {   // the other game of a 2-player pair gets the stash boxes too (online, the engine sends them on)
        const M = ctx.M;
        if (window.__mirrorIw && M._rotk_link_ewram) {
          const onl = !!(window.__mp && window.__mp.online), me2 = onl ? window.__mp.me & 1 : 0, a = M._rotk_link_ewram(me2), b2 = M._rotk_link_ewram(me2 ^ 1);
          if (a && b2 && a !== b2 && a === ctx.ew) for (const o of ewDirty) for (let j = 0; j < 4; j++) H8[b2 + (o - a) + j] = H8[o + j];
        }
      } catch (e) {}
      setNote("Sold " + n + " item" + (n === 1 ? "" : "s") + " for " + got + " gems");
      reopen();
    };
    // the d-pad / joystick / keys go to the page's cursor while the HD shop is up (the game's own Yes / No still
    // gets them); A works through the page's box; B leaves, or says No to the page's question
    const handle = (id, v) => {
      if (!open || !ctx) return false;
      if (hold) return id === 0 || id === 8 || (id >= 4 && id <= 7) || id === 11;
      if (sa) {
        if (sa.phase === "count") { if (id === 0 && v) saCancel(); return id === 0 || id === 8 || (id >= 4 && id <= 7) || id === 11; }
        if (id >= 4 && id <= 7) { if (v) { sa.sel = sa.sel ? 0 : 1; last = ""; } return true; }
        if (id === 8) { if (v) { if (sa.sel === 0) sellAllYes(); else saCancel(); } return true; }
        if (id === 0) { if (v) saCancel(); return true; }
        return false;
      }
      if (ask) {
        if (id >= 4 && id <= 7) { if (v) { ask.sel = ask.sel ? 0 : 1; last = ""; } return true; }
        if (id === 8) { if (v) { if (ask.sel === 0) buy(ask.k); else { ask = null; last = ""; } } return true; }
        if (id === 0) { if (v) { ask = null; last = ""; } return true; }
        return false;
      }
      if (ctx.gameAsk) return false;
      if (id >= 4 && id <= 7) {
        if (v) { move(id); rep.id = id; rep.n = 0; rep.t = performance.now() + 380; }
        else if (rep.id === id) rep.id = -1;
        return true;
      }
      if (id === 8) {
        if (v) {
          const t = gameTarget(hc);
          if (t >= 0 && t === curNow() && ctx.sub === 0 && !(hc[0] === "c" && +hc.slice(1) >= 30 && +hc.slice(1) - 30 !== ctx.win)) { handle.aPass = true; return false; }
          handle.aPass = false; act(); return true;
        }
        if (handle.aPass) { handle.aPass = false; return false; }
        return true;
      }
      return false;
    };
    setInterval(() => {   // held joystick repeats
      if (rep.id < 0 || !open || ask || hold || sa) return;
      const now = performance.now();
      if (now >= rep.t) { move(rep.id); rep.t = now + 150; }
    }, 40);
    const wrap = () => {
      const E = window.EJS_emulator, g = E && E.gameManager;
      if (!g || g.__shopWrap || typeof g.simulateInput !== "function") return;
      const orig = g.simulateInput;
      g.simulateInput = function (p, id, v) { if (!own && !p) { let h = false; try { h = handle(id, v); } catch (e) {} if (h) return; } return orig.apply(this, arguments); };
      g.__shopWrap = true;
    };

    function build() {
      el = document.createElement("div"); el.id = "hdSh"; el.hidden = true;
      el.innerHTML = '<style>' +
/*CSS*/
        '#hdSh .gd{display:flex;gap:calc(var(--c)*0.12);justify-content:center}' +
        '#hdSh .cell.gs{width:calc(var(--c)*1.25);height:calc(var(--c)*0.62);background:linear-gradient(180deg,#2c3a26,#182214);border-color:#4f6e3a}' +
        '#hdSh .cell .gl{position:absolute;inset:6% 5%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-size:calc(var(--c)*0.15);line-height:1.1;color:#e8dcb8}' +
        '#hdSh .cell .gl small{font-size:calc(var(--c)*0.13);color:#9fe0ff}' +
        '#hdSh .st{grid-template-columns:repeat(3,calc(var(--c)*1.1))}' +
        '#hdSh .cell.sk{background:linear-gradient(180deg,#30291c,#1c170f);border-color:#7a6230}' +
        '#hdSh .cell.sk .hp{bottom:24%}' +
        '#hdSh .cell .pr{position:absolute;left:0;right:0;bottom:3%;text-align:center;font-size:calc(var(--c)*0.15);line-height:1;color:#9fe0ff;pointer-events:none}' +
        '#hdSh .cell .pr.no{color:#ff8a78}' +
        '#hdSh .cell.sold{opacity:.45}' +
        '#hdSh .gem{font:700 calc(var(--fs)*1.05)/1 var(--display,Georgia,serif);color:#9fe0ff}' +
        '#hdSh .nm{font:700 calc(var(--fs)*1.25)/1.15 var(--display,Georgia,serif)}' +
        '#hdSh .tx{white-space:pre-wrap}' +
        '#hdSh .note{color:#ffb070}' +
        '#hdSh .bar{justify-content:center}' +
        '#hdSh .bar b.cur{background:#d8b25a;color:#1a1208;border-color:#f6dc94;box-shadow:0 0 calc(var(--c)*0.3) rgba(255,200,100,0.8)}' +
        '#hdSh .rp{justify-content:space-between;overflow:hidden}' +
        '#hdSh .sal{max-height:45%;overflow:hidden;font-size:calc(var(--fs)*0.85);line-height:1.25}' +
        '#hdSh .sal div{display:flex;justify-content:space-between;gap:1em}' +
        '#hdSh .sal div span:last-child{color:#9fe0ff}' +
        '</style><div class="pg lp"></div><div class="pg rp"></div>';
      document.body.appendChild(el);
      el.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        if (!ctx || hold) return;
        const t = e.target.closest("[data-id],[data-y],[data-ay],[data-sa]");
        if (!t) return;
        if (sa) { if (t.dataset.sa !== undefined && sa.phase === "ask") { if (+t.dataset.sa === 0) sellAllYes(); else saCancel(); } else if (t.dataset.sa !== undefined) saCancel(); return; }
        if (t.dataset.ay !== undefined) { const y = +t.dataset.ay; if (ask) { if (y === 0) buy(ask.k); else { ask = null; last = ""; } } return; }
        if (t.dataset.y !== undefined) { const y = +t.dataset.y, s = ctx.H8[ctx.iw + 0x41BC]; const seq = y === s ? [8] : [y < s ? 4 : 5, 8]; let k = 0; const go = () => { if (k < seq.length) { press(seq[k++]); setTimeout(go, sync() ? 220 : 150); } }; go(); return; }
        const id = t.dataset.id;
        if (ctx.gameAsk) return;
        if (id === hc) { act(); return; }
        hc = id; ask = null; last = "";
        if (id === "all") { sellAll(); return; }
        follow();
      });
    }
    setInterval(() => {
      try {
        wrap();
        const M = window.__wideM;
        const hide = () => { window.__hdShopOn = false; open = false; ask = null; sa = null; if (el && !el.hidden) { el.hidden = true; last = ""; } };
        if (!M || !M.HEAPU8 || !M._rotk_iwram || (M._rotk_link_iwram && (!M._rotk_link_on() || (window.__mp && window.__mp.online && !window.__mp.sync)))) return hide();
        const onl = !!(window.__mp && window.__mp.online), me = onl ? window.__mp.me & 1 : 0;
        const iw = onl ? M._rotk_link_iwram(me) : M._rotk_iwram(), ew = onl ? M._rotk_link_ewram(me) : M._rotk_ewram();
        if (!iw || !ew) return hide();
        const H8 = M.HEAPU8, r32 = (o) => (H8[o] | H8[o + 1] << 8 | H8[o + 2] << 16 | H8[o + 3] << 24) >>> 0;
        if (hold && el && !el.hidden) { window.__hdShopOn = true; return; }   // closing + reopening after a purchase
        if (!on() || H8[iw + 0x41B0] !== 20 || !window.__gameText) return hide();
        const ui = r32(iw + 0x1C90), scur = ui >>> 24 === 2 ? H8[ew + (ui & 0x3ffff) + 0x62] : ui >>> 24 === 3 ? H8[iw + (ui & 0x7fff) + 0x62] : 255;
        if (scur > 10) { if (el && !el.hidden) { window.__hdShopOn = true; return; } return hide(); }   // v186
        const cv = document.getElementById("mpCanvas"); if (!cv) return hide();
        const r = cv.getBoundingClientRect(); if (!r.width) return hide();
        if (!el) build();
        const sub = H8[iw + 0x41C0], linked = !!(r32(iw + 0x4144) & 0x20);
        const p = H8[iw + 0x3F59] & 1, hero = iw + 0x3C00 + 0x1AC * p, lvl = H8[hero + 0x19C] + 1, heroId = H8[hero + 0x19F];
        const inv = []; for (let i = 0; i < 16; i++) inv.push(r32(hero + 0x3C + 4 * i));
        const win = Math.min(4, H8[ew + 0x3F868 + p]), stash = []; for (let i = 0; i < 5; i++) stash.push(r32(ew + 0x3F840 + 20 * p + 4 * i));
        const wordOf = (c) => c >= 30 ? (c - 30 === win ? inv[15] : stash[c - 30]) : inv[c];
        const gems = H8[hero + 0x184] | H8[hero + 0x185] << 8;
        const firstOpen = !open;
        if (firstOpen) {   // which shop: the nearest Forge / Shrine to the hero
          const level = H8[iw + 0x41F8];   // (read only with the shop open: it reads 0 for a moment while the shop loads)
          if (level !== stockLevel) { stocks.clear(); stockLevel = level; }
          kindNow = 2; vendorAt = "";
          try {
            const at = (a) => ((a >>> 24) === 3 ? iw + (a & 0x7fff) : (a >>> 24) === 2 ? ew + (a & 0x3ffff) : -1);
            const R32 = (a) => { const o = at(a); return o >= 0 ? r32(o) : 0; }, R16 = (a) => { const o = at(a); return o >= 0 ? H8[o] | H8[o + 1] << 8 : 0; };
            const ho = R32(0x03003C00 + 0x1AC * p), hx = R16(ho + 0xae), hy = R16(ho + 0xb2);
            let q = ho, n = 0; while (q && n++ < 400) { const nx = R32(q); if (!nx || nx >>> 24 !== 2) break; q = nx; }
            let best = 1e9; n = 0;
            while (q && q >>> 24 === 2 && n++ < 400) {
              if (R32(q + 0x14) === SHOP_UPD) { const x = R16(q + 0xae), y = R16(q + 0xb2), d = Math.abs(x - hx) + Math.abs(y - hy); if (d < best) { best = d; kindNow = H8[at(q + 0x60)]; vendorAt = x + "," + y; } }
              q = R32(q + 4);
            }
          } catch (e) {}
        }
        let stock = null;
        if (kindNow === 0 && window.__romFull) {   // Forges sell random gear
          const key = kindNow + ":" + vendorAt + ":" + heroId + ":" + p;
          stock = stocks.get(key);
          if (!stock) { try { stock = roll(heroId, lvl, NSTOCK); } catch (e) { stock = []; } stocks.set(key, stock); }
        }
        const txt = window.__gameText(H8, ew), right = txt.filter((q) => q.x >= 112 && q.y >= 64);
        const gameAsk = sub === 2 || right.some((q) => /\?$/.test(q.s));
        if (scur >= 8 && sub === 0 && right.length) {
          const nm = right[0].s.replace(/:.*$/, ""), m = right.map((q) => q.s).join(" ").match(/cost (\d+) gems/i), k = kindNow + ":" + scur;
          const val = nm + (m ? "|" + m[1] : "");
          if (goodsName[k] !== val) { goodsName[k] = val; try { localStorage.setItem("rotk-goods2", JSON.stringify(goodsName)); } catch (e) {} }
        }
        ctx = { M, H8, ew, iw, scur, sub, win, linked, hero, gems, stock, gameAsk };
        if (gameAsk && scur <= 7) { const m = right.map((q) => q.s).join(" ").match(/worth (\d+) gems/i), w = scur === 7 ? inv[15] : inv[scur + 8]; if (m && !empty(w)) worth.set(w, +m[1]); }   // v209
        if (firstOpen) { open = true; hc = fromGame(scur); ask = null; sa = null; note = ""; rep.id = -1; }
        if (!hc) hc = fromGame(scur);
        if (note && performance.now() > noteT) note = "";
        const fs = Math.max(9, Math.round(r.height * 0.029));
        const nrows = stock && stock.length ? 8.6 : 6.9;
        const c = Math.max(22, Math.min(r.height * 0.84 / nrows, (r.width * 0.52 - 2.4 * fs) / 4.5, (r.width * 0.55) / 4.9));
        const key = [r.left, r.top, r.width, r.height, scur, sub, inv.join(), stash.join(), win, gems, right.map((q) => q.x + "," + q.y + q.s).join("|"), JSON.stringify(goodsName).length, r32(ew + 0x3F520 + 4), H8[iw + 0x41BC], hc, ask ? ask.k + ":" + ask.sel : "", sa ? sa.phase + sa.i + ":" + sa.sel + ":" + saTotal() : "", note, stock ? stock.join() : "", kindNow].join("/");
        window.__hdShopOn = true;
        if (key === last && !el.hidden) return;
        last = key;
        el.style.left = r.left + "px"; el.style.top = r.top + "px"; el.style.width = r.width + "px"; el.style.height = r.height + "px";
        el.style.setProperty("--fs", fs + "px"); el.style.setProperty("--c", Math.round(c) + "px");
        const COL = { 3: "#f8e050", 9: "#6fe06f", 12: "#6fe06f", 6: "#ff6450" };
        let L = "";
        if (hc[0] === "s" && stock) {   // left page: gear for sale, from the game file's tables
          const it = stock[+hc.slice(1)];
          if (!it) L += '<div class="nm" style="color:#c9b88f">Sold</div><div class="wh">This one is gone. The Forge gets new gear when you come back to this level.</div>';
          else {
            const rq = reqLevel(it), nA = ents(it).length - 1, pr = price(it);
            L += '<div class="big">' + pic(it) + "</div>";
            L += '<div class="nm" style="color:' + (nA >= 2 ? "#f8e050" : nA === 1 ? "#6fe06f" : "#f3ead6") + '">' + esc(itemName(it)) + "</div>";
            L += '<div style="color:' + (rq > lvl ? "#ff6450" : "#6fe06f") + '">Min. Level: ' + rq + "</div>";
            L += itemStats(it).map((x) => "<div>" + esc(x) + "</div>").join("");
            L += '<div class="tx" style="color:' + (gems >= pr ? "#9fe0ff" : "#ff8a78") + '">That will cost ' + pr + " gems</div>";
            if (ask && ask.k === +hc.slice(1)) {
              L += '<div class="tx" style="color:#f8e050">Are you sure you want to purchase this item?</div>';
              L += '<div class="acts">' + ["Yes", "No"].map((y, i) => '<b data-ay="' + i + '"' + (i === ask.sel ? ' class="sel"' : "") + ">" + y + "</b>").join("") + "</div>";
            }
          }
        } else if (sa || hc === "all") {   // v209 Sell All
          const shop = kindNow === 0 ? "Forge" : "Shrine";
          L += '<div class="nm">Sell All</div>';
          if (!sa) {
            const n = INV.filter((cc) => { const w = wordOf(cc); return !empty(w) && pic(w); }).length;
            L += '<div class="wh">' + (n ? "Sell all " + n + " item" + (n === 1 ? "" : "s") + " in your backpack to the " + shop + " at once. You will be asked first." : "Your backpack is empty.") + "</div>";
          } else if (sa.phase === "count") {
            L += '<div class="wh">Asking the ' + shop + " what your gear is worth&hellip; " + Math.min(sa.i + 1, sa.list.length) + " of " + sa.list.length + "</div>";
            L += '<div class="tip">B: stop</div>';
          } else {
            const tot = saTotal();
            L += '<div class="sal">' + sa.list.map((x) => '<div><span>' + esc(itemName(x.w)) + "</span><span>" + x.v + "</span></div>").join("") + "</div>";
            L += '<div class="tx" style="color:#9fe0ff">You will receive ' + tot + " gems</div>";
            L += '<div class="tx" style="color:#f8e050">Are you sure you want to sell all ' + sa.list.length + " item" + (sa.list.length === 1 ? "" : "s") + "?</div>";
            L += '<div class="acts">' + ["Yes", "No"].map((y, i) => '<b data-sa="' + i + '"' + (i === sa.sel ? ' class="sel"' : "") + ">" + y + "</b>").join("") + "</div>";
          }
        } else {   // the item or goods under the game's cursor, in the shop's own words (v181)
          const vcur = scur === 7 ? 30 + win : scur < 8 ? scur + 8 : -1, w = vcur >= 0 ? wordOf(vcur) : 0;
          if (vcur >= 0 && pic(w)) L += '<div class="big">' + pic(w) + "</div>";
          else if (scur >= 8) { L += '<div class="hdr">' + (kindNow === 0 ? "Forge" : "Shrine") + "</div>"; if (gameAsk) { const v = (goodsName[kindNow + ":" + scur] || "").split("|"); L += '<div class="nm">' + esc((v[0] && v[0].length <= 18 ? v[0] : "") || (GOODS[kindNow] || [])[scur - 8] || "") + "</div>"; } }
          const P = ew + 0x3F520, has = vcur >= 0 && pic(w) && r32(P + 4) === w && r32(P);
          if (has) {
            const name = str(H8, P + 12, 44), text_ = str(H8, P + 0x38, 168), lv = H8[P + 9], low = H8[P + 11], col = H8[P + 8];
            L += '<div class="nm" style="color:' + (COL[col] || "#f3ead6") + '">' + esc(name) + "</div>";
            if (lv) L += '<div style="color:' + (low ? "#ff6450" : "#6fe06f") + '">Min. Level: ' + lv + "</div>";
            if (!gameAsk) L += text_.replace(/\s*\(page 2 of your backpack[^)]*\)/, "").split(/, |\. (?=[A-Z])/).map((x) => x.trim()).filter(Boolean).map((x) => "<div>" + esc(x) + "</div>").join("");
          }
          (has && !gameAsk ? [] : right).forEach((q, i) => {
            const col = /\?$/.test(q.s) ? "#f8e050" : /worth|cost|gems/i.test(q.s) ? "#9fe0ff" : "";
            L += '<div class="' + (i === 0 && !has && !/\?$/.test(q.s) ? "nm" : "tx") + '"' + (col ? ' style="color:' + col + '"' : "") + ">" + esc(q.s) + "</div>";
          });
          if (!right.length && vcur >= 0 && !pic(w)) L += '<div class="nm" style="color:#c9b88f">Backpack slot</div><div class="wh">Empty</div>';
          if (gameAsk) { const sel = H8[iw + 0x41BC]; L += '<div class="acts">' + ["Yes", "No"].map((y, i) => '<b data-y="' + i + '"' + (i === sel ? ' class="sel"' : "") + ">" + y + "</b>").join("") + "</div>"; }
        }
        if (note) L += '<div class="note">' + esc(note) + "</div>";
        if (!(sa && sa.phase === "count")) L += '<div class="tip">' + (gameAsk || ask || sa ? "Yes or No &middot; A: choose &middot; B: No" : "Joystick: move &middot; A: " + (hc[0] === "s" || hc[0] === "g" ? "buy" : hc === "all" ? "sell all" : "sell") + " &middot; B: leave") + "</div>";
        el.children[1].innerHTML = L;
        // right page: gems, the shop's goods, gear for sale, the 12 backpack boxes, Leave
        const cell = (cc) => '<div class="cell' + ("c" + cc === hc ? " cur" : "") + '" data-id="c' + cc + '">' + pic(wordOf(cc)) + "</div>";
        let R = '<div class="row"><div class="gem">&#9670; ' + gems + " gems</div></div>";
        const ng = kindNow === 0 ? 2 : 3;
        R += '<div class="row"><div class="hdr">' + (kindNow === 0 ? "Forge" : "Shrine") + '</div><div class="gd">' + [8, 9, 10].slice(0, ng).map((g) => {
          const v = (goodsName[kindNow + ":" + g] || "").split("|"), nm = (v[0] && v[0].length <= 18 ? v[0] : "") || (GOODS[kindNow] || [])[g - 8] || "Goods";
          return '<div class="cell gs' + ("g" + g === hc ? " cur" : "") + '" data-id="g' + g + '"><span class="gl">' + esc(nm) + (v[1] ? "<small>" + v[1] + " gems</small>" : "") + "</span></div>";
        }).join("") + "</div></div>";
        if (stock && stock.length) R += '<div class="row"><div class="hdr">For sale</div><div class="gr st">' + stock.map((it, k) => {
          const id = "s" + k, pr = it ? price(it) : 0;
          return '<div class="cell sk' + (id === hc ? " cur" : "") + (it ? "" : " sold") + '" data-id="' + id + '">' + (it ? pic(it) + '<span class="pr' + (gems >= pr ? "" : " no") + '">' + pr + "</span>" : '<span class="pr">Sold</span>') + "</div>";
        }).join("") + "</div></div>";
        R += '<div class="row"><div class="hdr">Backpack &middot; tap to sell</div><div class="gr iv">' + INV.map(cell).join("") + "</div></div>";
        R += '<div class="bar"><b data-id="all"' + (hc === "all" ? ' class="cur"' : "") + ">&#9670; Sell All</b></div>";
        el.children[2].innerHTML = R;
        el.hidden = false;
      } catch (e) { if (el) el.hidden = true; window.__hdShopOn = false; open = false; }
    }, 80);
    window.__hdShopDbg = { roll: (h, l, n) => roll(h, l, n), itemName, itemStats, reqLevel, price, get hc() { return hc; }, get sa() { return sa; }, worth, get stocks() { return stocks; } };
  })();
