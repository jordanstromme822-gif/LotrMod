"""Play Room v181: item menu fixes (Jordan, 2026-11-16: "Item menu doesn't load correctly when - failing to equip item due
to level restriction - entering a forge or shrine - moving an item doesn't allow you to move the item in the inventory").
Usage: item-menu-v181.py playroom-v180.html out.html, then tools/orcslots/pagejs.py out.html (fills the new bl lines).
- HD Backpack keeps showing during the game's messages (substate 8: level too low, backpack full, can't equip) and shows
  the message itself.
- Move Item (substate 6): the box the item goes to is the game's second cursor (UI 0x03001FE4); the HD Backpack lights it
  and marks the item being moved, taps walk that cursor, and a tap on a stash box asks tools/orcslots (MVREQ) to swap.
- Forge / Shrine (state 20): an HD shop drawn by the page over the game's own: the shop's words (captured by line_wrap /
  clr_wrap into EWRAM 0x0203F990), the 3 goods, all 12 backpack boxes (a stash box goes into cell 15 with SWIN), Yes/No.
Works in 1-player, P2 and online (page writes travel with the buttons since v180)."""
import sys
src, out = sys.argv[1:3]
t = open(src).read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)

# engine version (new hooks)
rep('const V = isLink ? "?v=180" : "?v=hd2";', 'const V = isLink ? "?v=181" : "?v=hd2";')
rep('      const V = "?v=180";', '      const V = "?v=181";')
# new hook calls in the game file (pagejs.py fills the bytes)
rep('''        game.set(hexBytes("40f0f9fd"), 0x41FBA); // bl req_wrap
''', '''        game.set(hexBytes("40f0f9fd"), 0x41FBA); // bl req_wrap
        game.set(hexBytes("00f800f0"), 0x1D6F2); // bl line_wrap
        game.set(hexBytes("00f800f0"), 0x1267C); // bl clr_wrap
        game.set(hexBytes("00f800f0"), 0x1DF10); // bl shop_keys
''')
open(out, 'w').write(t)
print('ok')

t = open(out).read()

# ---- HD Backpack ----
# the game's text lines (tools/orcslots line_wrap): [{x, y, s}], and paragraphs of them (a gap or another column starts one)
rep('''    const str = (H8, o, n) => { let s = ""; for (let i = 0; i < n; i++) { const c = H8[o + i]; if (!c) break; s += String.fromCharCode(c); } return s; };
    const on = () => { try { return localStorage.getItem("rotk-hdbp") !== "0"; } catch (e) { return true; } };''',
'''    const str = (H8, o, n) => { let s = ""; for (let i = 0; i < n; i++) { const c = H8[o + i]; if (!c) break; s += String.fromCharCode(c); } return s; };
    const on = () => { try { return localStorage.getItem("rotk-hdbp") !== "0"; } catch (e) { return true; } };
    // v181: the game's own text lines (tools/orcslots line_wrap, EWRAM 0x0203F990): x, y, words
    const gameText = window.__gameText = (H8, ew) => {
      const b = ew + 0x3F990, n = H8[b], L = []; let o = 4;
      for (let i = 0; i < n && o < 0x170; i++) {
        const k = H8[b + o + 2]; let s = "";
        for (let j = 0; j < k; j++) { const c = H8[b + o + 3 + j]; s += c === 10 ? " " : c >= 32 && c < 127 ? String.fromCharCode(c) : ""; }
        L.push({ x: H8[b + o], y: H8[b + o + 1], s: s.trim() }); o += 3 + k;
      }
      L.sort((a, c) => a.y - c.y || a.x - c.x);
      const P = [];
      for (const l of L) {
        if (!l.s) continue;
        const q = P[P.length - 1];
        if (q && l.y - q.y1 <= 12 && Math.abs(l.x - q.x) <= 8) { q.s += (/-$/.test(q.s) ? "" : " ") + l.s; q.y1 = l.y; }
        else P.push({ x: l.x, y: l.y, y1: l.y, s: l.s });
      }
      return P;
    };
    window.__gameTextSeq = (H8, ew) => H8[ew + 0x3F991];''')

# keep the HD Backpack up during the game's messages (substate 8)
rep('''        if (!want || !(sub <= 3 || sub === 6)) return hide();
        const ui = r32(iw + 0x1FE0), cur =''',
'''        if (!want || !(sub <= 3 || sub === 6 || sub === 8)) return hide();   // v181: 8 = a message (level too low...)
        const ui = r32(iw + 0x1FE0), cur =''')
# Move Item: the second cursor is where the item goes
rep('''        const vcur = cur === 15 ? 30 + win : cur;
        // the game's item menu''',
'''        const vcur = cur === 15 ? 30 + win : cur;
        const ui2 = r32(iw + 0x1FE4), tg = sub !== 6 ? 255 : ui2 >>> 24 === 2 ? H8[ew + (ui2 & 0x3ffff) + 0x62] : ui2 >>> 24 === 3 ? H8[iw + (ui2 & 0x7fff) + 0x62] : 255;
        const vtg = tg === 15 ? 30 + win : tg;   // v181: Move Item's target box
        const msg = sub === 8 ? gameText(H8, ew).filter((q) => q.x >= 112 && q.y >= 64).map((q) => q.s).join(" ") : "";
        // the game's item menu''')
rep('''        ctx = { H8, ew, iw, cur, vcur, win, sub, menu };''', '''        ctx = { H8, ew, iw, cur, vcur, win, sub, menu, tg, vtg };''')
rep('''inv.join(), orc.join(), aw.join(), stash.join(), win, has ? r32(P) : 0, worn, wtext, menu ? menu.sel + ":" + menu.o.length : ""].join("/");''',
    '''inv.join(), orc.join(), aw.join(), stash.join(), win, has ? r32(P) : 0, worn, wtext, menu ? menu.sel + ":" + menu.o.length : "", vtg, msg].join("/");''')
rep('''        } else if (sub === 6) L += '<div class="q" style="color:#7cc8e8">Move Item: pick the backpack box to move it to.</div>';
        L += '<div class="tip">' + (sub === 0 ? "A or tap again: actions &middot; B: close" : "B: back") + "</div>";''',
'''        } else if (sub === 6) L += '<div class="q" style="color:#7cc8e8">Move Item: pick the backpack box to move it to.</div>';
        else if (sub === 8) {   // v181: the game's message (level too low, backpack full...), its own words
          let m = msg;
          if (!m) m = has && H8[P + 11] ? "You are not high enough level to equip this item!" : cur < 8 || cur >= 20 ? "Your backpack is full!" : "This hero cannot use this item.";
          L += '<div class="q" style="color:#f8e050;font-size:calc(var(--fs)*1.1)">' + esc(m) + '</div><div class="acts"><b class="sel" data-k="A">OK</b></div>';
        }
        L += '<div class="tip">' + (sub === 0 ? "A or tap again: actions &middot; B: close" : sub === 6 ? "Tap a box or move with the d-pad &middot; A: put it there &middot; B: cancel" : sub === 8 ? "A or B: OK" : "B: back") + "</div>";''')
rep('''          return '<div class="cell ' + (cls || "") + " " + tier(ww) + (cc === vcur ? " cur" : "") + '" data-c="' + cc + '">' + pic(ww) +''',
    '''          return '<div class="cell ' + (cls || "") + " " + tier(ww) + (ctx.sub === 6 ? (cc === ctx.vtg ? " cur" : "") + (cc === vcur ? " mv" : "") : cc === vcur ? " cur" : "") + '" data-c="' + cc + '">' + pic(ww) +''')
# menu rows: step the game's choice until it is on the row (read back each step; a fixed number of presses lost some
# while the menu cursor was still moving, so Move Item opened Carve Rune), then A
rep('''          let d = to - (at < 0 ? 0 : at), k = 0;
          const step = () => { if (d === 0) { press(8); return; } press(d > 0 ? 5 : 4, 70); d += d > 0 ? -1 : 1; setTimeout(step, 150); };
          step();''',
'''          const selAt = ctx.sub === 3 ? 0x41C4 : 0x41BC; let n = 0;
          const step = () => {
            const s = H8[iw + selAt], i = list.indexOf(s);
            if (s === want) { press(8); return; }
            if (++n > 12 || H8[iw + 0x41C0] !== ctx.sub) return;
            press(i < 0 || i < to ? 5 : 4, 70); setTimeout(step, 260);
          };
          step();''')
# taps: OK button; Move Item walks the target cursor, and a stash box swaps through tools/orcslots (MVREQ)
rep('''        if (t.dataset.k) { const k = t.dataset.k; if (k === "L" && window.__lBlip) window.__lBlip(); else press(k === "L" ? 10 : k === "R" ? 11 : 0); return; }''',
    '''        if (t.dataset.k) { const k = t.dataset.k; if (k === "L" && window.__lBlip) window.__lBlip(); else press(k === "L" ? 10 : k === "R" ? 11 : k === "A" ? 8 : 0); return; }''')
rep('''        } else if (sub === 6 && ((c >= 8 && c < 15) || c === 30 + ctx.win)) {   // Move Item: walk the game's grid cursor there, then A
          if (c >= 30) c = 15;
          let x = (cur & 3), y = (cur >> 2) & 1;''',
'''        } else if (sub === 6 && c >= 30 && c < 35 && c !== 30 + ctx.win) {   // v181: Move Item onto a stash box (1-player)
          if (c !== ctx.vcur) H8[ew + 0x3F604] = c - 30 + 1;
        } else if (sub === 6 && ((c >= 8 && c < 15) || c === 30 + ctx.win)) {   // Move Item: walk the game's target cursor there, then A
          if (c >= 30) c = 15;
          const from = ctx.tg >= 8 && ctx.tg < 16 ? ctx.tg : cur;
          let x = (from & 3), y = (from >> 2) & 1;''')
open(out, 'w').write(t)
print('backpack ok')

t = open(out).read()
# ---- HD Forge / Shrine (state 20) ----
import re
css = re.search(r"el\.innerHTML = '<style>' \+\n(.*?)'</style><div class=\"pg lp\"></div><div class=\"pg rp\"></div>';", t, re.S).group(1)
css = css.replace("#hdBp", "#hdSh")
SHOP = r'''
  // v181 HD Forge / Shrine (Jordan, 2026-11-16: "Item menu doesn't load correctly when ... entering a forge or shrine"):
  // the page draws the shop over the game's own like the HD Backpack: the shop's words (tools/orcslots line_wrap), its
  // goods, all 12 backpack boxes. Taps walk the shop's cursor with the d-pad (map measured in the game), a tap on the box
  // under the cursor presses A; a stash box first goes into cell 15 (SWIN, 1-player). See recomp/playroom/item-menu-v181.py.
  (function hdShop() {
    const CNT = [18, 11, 9, 11, 10, 4, 13, 10, 24, 8, 12, 9, 8, 7, 53], START = [];
    { let s = 0; for (const c of CNT) { START.push(s); s += c; } }
    const NAV = { 7: [1, 2, 3, 8, 5, 6, 7, 8, 9, 10, 0], 6: [10, 0, 1, 2, 10, 4, 5, 6, 3, 8, 9], 4: [4, 5, 6, 7, 0, 1, 2, 3, 8, 9, 10], 5: [4, 5, 6, 7, 0, 1, 2, 3, 8, 9, 10] };
    const INV = [8, 9, 10, 11, 12, 13, 14, 30, 31, 32, 33, 34];
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
    const str = (H8, o, n) => { let s = ""; for (let i = 0; i < n; i++) { const c = H8[o + i]; if (!c) break; s += String.fromCharCode(c); } return s; };
    const on = () => { try { return localStorage.getItem("rotk-hdbp") !== "0"; } catch (e) { return true; } };
    const gi = (id, v) => { try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} };
    const sync = () => !!(window.__mp && window.__mp.sync);
    const press = (id, ms = 70) => { const go = () => { gi(id, 1); setTimeout(() => gi(id, 0), ms); }; if (sync()) setTimeout(go, 50); else go(); };
    const keys = (seq) => { const go = () => { const k = seq.shift(); if (k === undefined) return; press(k); setTimeout(go, sync() ? 220 : 150); }; go(); };
    const route = (a, b) => {   // shortest d-pad presses from shop cursor a to b
      const prev = { [a]: null }, q = [a];
      while (q.length) { const c = q.shift(); if (c === b) break; for (const k of [7, 6, 4, 5]) { const n = NAV[k][c]; if (n !== undefined && !(n in prev)) { prev[n] = [c, k]; q.push(n); } } }
      const s = []; let c = b; while (prev[c]) { s.unshift(prev[c][1]); c = prev[c][0]; } return s;
    };
    const pic = (w) => {
      if (w === 0xFFFFFFFF || w === 0 || (w & 15) === 15) return "";
      const cat = w & 15, idx = (w >>> 8) & 255;
      if (cat > 14 || idx >= CNT[cat]) return "";
      const n = START[cat] + idx;
      return '<i class="hp" style="background-position:' + ((n % 16) / 15 * 100).toFixed(3) + "% " + (Math.floor(n / 16) / 12 * 100).toFixed(3) + '%"></i>';
    };
    // the names the shop showed for its goods (shown when the cursor is on them), by level and slot, kept for next time
    let goodsName = {}; try { goodsName = JSON.parse(localStorage.getItem("rotk-goods") || "{}"); } catch (e) {}
    let el = null, last = "", ctx = null;
    function build() {
      el = document.createElement("div"); el.id = "hdSh"; el.hidden = true;
      el.innerHTML = '<style>' +
''' + css + r'''        '#hdSh .gd{grid-template-columns:repeat(3,var(--c))}' +
        '#hdSh .cell.gs{background:linear-gradient(180deg,#2c3a26,#182214);border-color:#4f6e3a}' +
        '#hdSh .cell .gl{position:absolute;inset:8% 6%;display:flex;align-items:center;justify-content:center;text-align:center;font-size:calc(var(--c)*0.16);line-height:1.1;color:#e8dcb8}' +
        '#hdSh .gem{font:700 calc(var(--fs)*1.05)/1 var(--display,Georgia,serif);color:#9fe0ff}' +
        '#hdSh .nm{font:700 calc(var(--fs)*1.25)/1.15 var(--display,Georgia,serif)}' +
        '#hdSh .tx{white-space:pre-wrap}' +
        '</style><div class="pg lp"></div><div class="pg rp"></div>';
      document.body.appendChild(el);
      el.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        if (!ctx) return;
        const t = e.target.closest("[data-c],[data-g],[data-k],[data-y]");
        if (!t) return;
        if (t.dataset.k) { const k = t.dataset.k; press(k === "A" ? 8 : 0); return; }
        if (t.dataset.y !== undefined) { const y = +t.dataset.y, s = ctx.H8[ctx.iw + 0x41BC]; keys(y === s ? [8] : [y < s ? 4 : 5, 8]); return; }
        let to;
        if (t.dataset.g !== undefined) to = +t.dataset.g;
        else {
          const c = +t.dataset.c;
          if (c >= 30 && c !== 30 + ctx.win) {   // a stash box: into cell 15 first (1-player), then the cursor goes there
            if (ctx.linked) return;
            ctx.H8[ctx.ew + 0x3F605] = c - 30 + 1;
            keys(ctx.scur === 7 ? [6, 7] : route(ctx.scur, 7));
            return;
          }
          to = c >= 30 ? 7 : c - 8;
        }
        if (ctx.sub !== 0) return;
        if (to === ctx.scur) { press(8); return; }
        keys(route(ctx.scur, to));
      });
    }
    setInterval(() => {
      try {
        const M = window.__wideM;
        const hide = () => { window.__hdShopOn = false; if (el && !el.hidden) { el.hidden = true; last = ""; } };
        if (!M || !M.HEAPU8 || !M._rotk_iwram || (M._rotk_link_iwram && (!M._rotk_link_on() || (window.__mp && window.__mp.online && !window.__mp.sync)))) return hide();
        const onl = !!(window.__mp && window.__mp.online), me = onl ? window.__mp.me & 1 : 0;
        const iw = onl ? M._rotk_link_iwram(me) : M._rotk_iwram(), ew = onl ? M._rotk_link_ewram(me) : M._rotk_ewram();
        if (!iw || !ew) return hide();
        const H8 = M.HEAPU8, r32 = (o) => (H8[o] | H8[o + 1] << 8 | H8[o + 2] << 16 | H8[o + 3] << 24) >>> 0;
        if (!on() || H8[iw + 0x41B0] !== 20 || !window.__gameText) return hide();
        const ui = r32(iw + 0x1C90), scur = ui >>> 24 === 2 ? H8[ew + (ui & 0x3ffff) + 0x62] : ui >>> 24 === 3 ? H8[iw + (ui & 0x7fff) + 0x62] : 255;
        if (scur > 10) return hide();
        const cv = document.getElementById("mpCanvas"); if (!cv) return hide();
        const r = cv.getBoundingClientRect(); if (!r.width) return hide();
        if (!el) build();
        const sub = H8[iw + 0x41C0], linked = !!(r32(iw + 0x4144) & 0x20);
        const p = H8[iw + 0x3F59] & 1, hero = iw + 0x3C00 + 0x1AC * p, lvl = H8[hero + 0x19C] + 1;
        const inv = []; for (let i = 0; i < 16; i++) inv.push(r32(hero + 0x3C + 4 * i));
        const win = Math.min(4, H8[ew + 0x3F868 + p]), stash = []; for (let i = 0; i < 5; i++) stash.push(r32(ew + 0x3F840 + 20 * p + 4 * i));
        const wordOf = (c) => c >= 30 ? (c - 30 === win ? inv[15] : stash[c - 30]) : inv[c];
        const gems = H8[hero + 0x184] | H8[hero + 0x185] << 8;
        const txt = window.__gameText(H8, ew), right = txt.filter((q) => q.x >= 112 && q.y >= 64);
        const shopId = r32(iw + 0x41F8) & 0xff;   // the level
        if (scur >= 8 && sub === 0 && right.length) { const nm = right[0].s.replace(/:.*$/, ""); if (goodsName[shopId + ":" + scur] !== nm) { goodsName[shopId + ":" + scur] = nm; try { localStorage.setItem("rotk-goods", JSON.stringify(goodsName)); } catch (e) {} } }
        ctx = { H8, ew, iw, scur, sub, win, linked };
        const fs = Math.max(9, Math.round(r.height * 0.029));
        const c = Math.max(30, Math.min(r.height * 0.86 / 6.4, (r.width * 0.55) / 4.9));
        const key = [r.left, r.top, r.width, r.height, scur, sub, inv.join(), stash.join(), win, gems, right.map((q) => q.x + "," + q.y + q.s).join("|"), Object.keys(goodsName).length, r32(ew + 0x3F520 + 4), H8[iw + 0x41BC]].join("/");
        window.__hdShopOn = true;
        if (key === last && !el.hidden) return;
        last = key;
        el.style.left = r.left + "px"; el.style.top = r.top + "px"; el.style.width = r.width + "px"; el.style.height = r.height + "px";
        el.style.setProperty("--fs", fs + "px"); el.style.setProperty("--c", Math.round(c) + "px");
        // left page: the item or goods under the cursor, in the shop's own words
        const vcur = scur === 7 ? 30 + win : scur < 8 ? scur + 8 : -1, w = vcur >= 0 ? wordOf(vcur) : 0;
        let L = "";
        if (vcur >= 0 && pic(w)) L += '<div class="big">' + pic(w) + "</div>";
        else if (scur >= 8) L += '<div class="hdr">For sale</div>';
        const P = ew + 0x3F520, has = vcur >= 0 && pic(w) && r32(P + 4) === w && r32(P);
        const COL = { 3: "#f8e050", 9: "#6fe06f", 12: "#6fe06f", 6: "#ff6450" };
        const ask = sub === 2 || right.some((q) => /\?$/.test(q.s));
        if (has) {   // the item: name, Min. Level and text from the item panel record (tools/orcslots panel)
          const name = str(H8, P + 12, 44), text = str(H8, P + 0x38, 168), lv = H8[P + 9], low = H8[P + 11], col = H8[P + 8];
          L += '<div class="nm" style="color:' + (COL[col] || "#f3ead6") + '">' + esc(name) + "</div>";
          if (lv) L += '<div style="color:' + (low ? "#ff6450" : "#6fe06f") + '">Min. Level: ' + lv + "</div>";
          if (!ask) L += text.replace(/\s*\(page 2 of your backpack[^)]*\)/, "").split(/, |\. (?=[A-Z])/).map((x) => x.trim()).filter(Boolean).map((x) => "<div>" + esc(x) + "</div>").join("");
        }
        const yn = ask ? ["Yes", "No"] : [], sel = H8[iw + 0x41BC];   // the shop's Yes / No: the menu choice
        (has && !ask ? [] : right).forEach((q, i) => {
          const col = /\?$/.test(q.s) ? "#f8e050" : /worth|cost|gems/i.test(q.s) ? "#9fe0ff" : "";
          L += '<div class="' + (i === 0 && !has && !/\?$/.test(q.s) ? "nm" : "tx") + '"' + (col ? ' style="color:' + col + '"' : "") + ">" + esc(q.s) + "</div>";
        });
        if (!right.length && vcur >= 0 && !pic(w)) L += '<div class="nm" style="color:#c9b88f">Backpack slot</div><div class="wh">Empty</div>';
        if (yn.length) L += '<div class="acts">' + yn.map((y, i) => '<b data-y="' + i + '"' + (i === sel ? ' class="sel"' : "") + ">" + y + "</b>").join("") + "</div>";
        L += '<div class="tip">' + (yn.length ? "Tap Yes or No &middot; A: choose &middot; B: No" : "Tap a box, tap again or A: " + (scur >= 8 ? "buy" : "sell") + " &middot; B: leave") + "</div>";
        el.children[1].innerHTML = L;
        // right page: gems, the goods, the 12 backpack boxes
        const cell = (cc) => {
          const ww = wordOf(cc), cur = cc === vcur;
          return '<div class="cell' + (cur ? " cur" : "") + '" data-c="' + cc + '">' + pic(ww) + "</div>";
        };
        let R = '<div class="row"><div class="gem">&#9670; ' + gems + " gems</div></div>";
        R += '<div class="row"><div class="hdr">For sale</div><div class="gr gd">' + [8, 9, 10].map((g) =>
          '<div class="cell gs' + (g === scur ? " cur" : "") + '" data-g="' + g + '"><span class="gl">' + esc(goodsName[shopId + ":" + g] || "Tap to see") + "</span></div>").join("") + "</div></div>";
        R += '<div class="row"><div class="hdr">Backpack &middot; tap to sell</div><div class="gr iv">' + INV.map(cell).join("") + "</div></div>";
        R += '<div class="bar"><b data-k="B">&#9666; Leave</b></div>';
        el.children[2].innerHTML = R;
        el.hidden = false;
      } catch (e) { if (el) el.hidden = true; window.__hdShopOn = false; }
    }, 80);
  })();
'''
rep('''  (function itemPanel() {
''', SHOP + '''
  (function itemPanel() {
''')
open(out, 'w').write(t)
print('shop ok')
