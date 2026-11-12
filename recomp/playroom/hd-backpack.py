"""Play Room: HD Backpack (Jordan, 2026-11-12: "Stop limiting to gba").
Usage: hd-backpack.py in.html out.html   (in.html = a page already patched by backpack-step1.py)
The page draws the whole Backpack itself, sharp at screen resolution, over the game while the game's Backpack is open
(state 10). Layout from Jordan's sheet (IMG_3376): left page = the item under the cursor (big picture, name, Min. Level,
stats with green / red compare arrows, then the item menu as a list); right page = worn gear in 3 rows of 3
(amulet helm cloak / weapon armor shield / gloves boots Orc Head), under it the backpack in rows of 4, under that the
arrow slots (Frodo 1, Legolas 2); L / R buttons at the bottom; herbs and Ent Water at the top right.
The game keeps the items and runs every action (equip, discard, Carve Rune, Move Item): the page sets HDMODE
(EWRAM 0x0203F602) so tools/orcslots nav_c moves the cursor on this layout, and a tap on a box sets CURREQ (0x0203F603)
to the box + 1 and presses Down. A second tap on the box under the cursor presses A; a tap on a menu row moves to it
and presses A. Carve Rune and other screens fall back to the game's own picture.
Item pictures: wide/items.png (the game's own 207 Backpack pictures, captured from the Backpack, framed lines cut off,
scaled 4x with EPX; tools/orcslots/itempics.py), private like the game. Setting: localStorage rotk-hdbp ("0" = off)."""
import sys

src, out = sys.argv[1:3]
t = open(src).read()

def rep(x, y, cnt=1):
    global t
    k = t.count(x); assert k == cnt, (x[:80], k); t = t.replace(x, y)

JS = r'''
  // HD Backpack (Jordan, 2026-11-12: "Stop limiting to gba"): see recomp/playroom/hd-backpack.py.
  (function hdBackpack() {
    const CNT = [18, 11, 9, 11, 10, 4, 13, 10, 24, 8, 12, 9, 8, 7, 53], START = [];
    { let s = 0; for (const c of CNT) { START.push(s); s += c; } }
    const AW = 104, AH = 80, ACOLS = 16;
    const EQ = [[7, "Amulet"], [3, "Helm"], [4, "Cloak"], [1, "Weapon"], [0, "Armor"], [2, "Shield"], [5, "Gloves"], [6, "Boots"], [20, "Orc Head"]];
    const INV = [8, 9, 10, 11, 12, 13, 14, 15, 21, 22, 23];
    const COL = { 3: "#f8e050", 9: "#6fe06f", 12: "#6fe06f", 6: "#ff6450" };
    const PGREQ = 0x3F600, HDMODE = 0x3F602, CURREQ = 0x3F603;
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
    const str = (H8, o, n) => { let s = ""; for (let i = 0; i < n; i++) { const c = H8[o + i]; if (!c) break; s += String.fromCharCode(c); } return s; };
    const on = () => { try { return localStorage.getItem("rotk-hdbp") !== "0"; } catch (e) { return true; } };
    const gi = (id, v) => { try { window.EJS_emulator.gameManager.simulateInput(0, id, v); } catch (e) {} };
    const press = (id, ms = 90) => { gi(id, 1); setTimeout(() => gi(id, 0), ms); };
    let el = null, last = "", ctx = null;
    const pic = (w, big) => {
      if (w === 0xFFFFFFFF || w === 0) return "";
      const cat = w & 15, idx = (w >>> 8) & 255;
      if (cat > 14 || idx >= CNT[cat]) return "";
      const n = START[cat] + idx;
      return '<i class="hp" style="background-position:' + ((n % ACOLS) / (ACOLS - 1) * 100).toFixed(3) + "% " + (Math.floor(n / ACOLS) / 12 * 100).toFixed(3) + '%"></i>';
    };
    const tier = (w) => {
      if (w === 0xFFFFFFFF || !w) return "";
      const cat = w & 15;
      if (cat === 14) return "u";
      if (cat === 7) return "";
      return ((w >>> 16) & 255) !== 255 || (w >>> 24) !== 255 ? "m" : "";
    };
    function build() {
      el = document.createElement("div"); el.id = "hdBp"; el.hidden = true;
      el.innerHTML = '<style>' +
        '#hdBp{position:fixed;z-index:23;box-sizing:border-box;display:flex;gap:2.2%;padding:2.2% 2.6% 1.6%;color:#f3ead6;font:600 var(--fs,14px)/1.3 var(--ui,system-ui,sans-serif);' +
        'background:radial-gradient(120% 90% at 30% 0%,#2a2118 0%,#15110c 60%,#0b0907 100%);-webkit-user-select:none;user-select:none;touch-action:none}' +
        '#hdBp[hidden]{display:none}' +
        '#hdBp .pg{position:relative;border:2px solid rgba(216,178,90,0.55);border-radius:calc(var(--fs)*0.8);background:rgba(10,8,6,0.55);box-shadow:inset 0 0 calc(var(--fs)*2) rgba(0,0,0,0.6)}' +
        '#hdBp .lp{flex:0 0 40%;padding:calc(var(--fs)*1.1);overflow-y:auto;display:flex;flex-direction:column;gap:calc(var(--fs)*0.35)}' +
        '#hdBp .rp{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:space-evenly;padding:calc(var(--fs)*0.6) calc(var(--fs)*0.8)}' +
        '#hdBp .hdr{font:700 calc(var(--fs)*0.8)/1 var(--display,Georgia,serif);letter-spacing:.14em;text-transform:uppercase;color:#d8b25a;opacity:.85;align-self:flex-start}' +
        '#hdBp .gr{display:grid;gap:calc(var(--c)*0.12)}' +
        '#hdBp .eq{grid-template-columns:repeat(3,calc(var(--c)*1.28))}' +
        '#hdBp .iv{grid-template-columns:repeat(4,var(--c))}' +
        '#hdBp .ar{grid-template-columns:repeat(2,var(--c))}' +
        '#hdBp .cell{position:relative;height:calc(var(--c)*0.82);border-radius:calc(var(--c)*0.12);background:linear-gradient(180deg,#3a3128,#231d17);border:2px solid #5a4a34;box-shadow:inset 0 2px 6px rgba(0,0,0,0.6);cursor:pointer;overflow:hidden}' +
        '#hdBp .cell.m{border-color:#3f9a46}#hdBp .cell.u{border-color:#b8433a}' +
        '#hdBp .cell.oh{background:linear-gradient(180deg,#3a2622,#22160f)}' +
        '#hdBp .cell.ax{background:linear-gradient(180deg,#25303c,#161d26);border-color:#3c5a78}' +
        '#hdBp .cell.cur{border-color:#f6dc94;box-shadow:0 0 0 2px #f6dc94,0 0 calc(var(--c)*0.3) rgba(255,200,100,0.8),inset 0 2px 6px rgba(0,0,0,0.5)}' +
        '#hdBp .cell.mv{outline:2px dashed #7cc8e8;outline-offset:-5px}' +
        '#hdBp .cell .hp{position:absolute;left:6%;right:6%;top:4%;bottom:14%;background-image:url(wide/items.png);background-size:1600% 1300%;background-repeat:no-repeat;image-rendering:auto}' +
        '#hdBp .cell .lb{position:absolute;left:0;right:0;bottom:2%;text-align:center;font-size:calc(var(--c)*0.15);line-height:1;color:#c9b88f;opacity:.75;pointer-events:none}' +
        '#hdBp .cell .ct{position:absolute;right:6%;top:4%;font-size:calc(var(--c)*0.19);color:#fff;text-shadow:0 1px 2px #000}' +
        '#hdBp .big{width:calc(var(--fs)*6.2);height:calc(var(--fs)*4.8);flex:none;align-self:center;position:relative}' +
        '#hdBp .lp.mn .big{width:calc(var(--fs)*4.2);height:calc(var(--fs)*3.2)}' +
        '#hdBp .big .hp{position:absolute;inset:0;background-image:url(wide/items.png);background-size:1600% 1300%;background-repeat:no-repeat}' +
        '#hdBp .nm{font:700 calc(var(--fs)*1.3)/1.15 var(--display,Georgia,serif)}' +
        '#hdBp .wh{font-size:calc(var(--fs)*0.85);opacity:.65}' +
        '#hdBp .acts{display:flex;flex-direction:column;gap:calc(var(--fs)*0.3);margin-top:calc(var(--fs)*0.3)}' +
        '#hdBp .acts b{font-weight:600;padding:calc(var(--fs)*0.35) calc(var(--fs)*0.8);border-radius:calc(var(--fs)*0.5);border:1px solid rgba(216,178,90,0.5);color:#d9cfb8;cursor:pointer}' +
        '#hdBp .acts b.sel{background:#d8b25a;color:#1a1208;border-color:#f6dc94}' +
        '#hdBp .q{opacity:.85;margin-top:calc(var(--fs)*0.4)}' +
        '#hdBp .tip{margin-top:auto;font-size:calc(var(--fs)*0.8);opacity:.55}' +
        '#hdBp .bar{display:flex;justify-content:space-between;width:100%;margin-top:calc(var(--fs)*0.3)}' +
        '#hdBp .bar b{font:700 calc(var(--fs)*0.85)/1 var(--display,Georgia,serif);letter-spacing:.06em;padding:calc(var(--fs)*0.45) calc(var(--fs)*1);border-radius:999px;border:2px solid #d8b25a;background:rgba(14,11,8,0.85);cursor:pointer}' +
        '#hdBp .row{display:flex;flex-direction:column;align-items:center;gap:calc(var(--fs)*0.25)}' +
        '</style><div class="pg lp"></div><div class="pg rp"></div>';
      document.body.appendChild(el);
      el.addEventListener("pointerdown", (e) => {
        e.preventDefault();
        if (!ctx) return;
        const t = e.target.closest("[data-c],[data-o],[data-k]");
        if (!t) return;
        const { H8, ew, iw, cur, sub } = ctx;
        if (t.dataset.k) { const k = t.dataset.k; if (k === "L" && window.__lBlip) window.__lBlip(); else press(k === "L" ? 10 : k === "R" ? 11 : 0); return; }
        if (t.dataset.o !== undefined) {           // a menu row: move the game's menu to it, then A
          const want = +t.dataset.o, list = ctx.menu ? ctx.menu.o.map((x) => x[0]) : [], at = list.indexOf(ctx.menu ? ctx.menu.sel : -1), to = list.indexOf(want);
          if (to < 0) return;
          let d = to - (at < 0 ? 0 : at), k = 0;
          const step = () => { if (d === 0) { press(8); return; } press(d > 0 ? 5 : 4, 70); d += d > 0 ? -1 : 1; setTimeout(step, 150); };
          step();
          return;
        }
        const c = +t.dataset.c;
        if (sub === 0) {
          if (c === cur) press(8);
          else { H8[ew + CURREQ] = c + 1; press(5); }
        } else if (sub === 6 && c >= 8 && c < 16) {   // Move Item: walk the game's grid cursor there, then A
          let x = (cur & 3), y = (cur >> 2) & 1; const tx = c & 3, ty = (c >> 2) & 1, seq = [];
          while (x < tx) { seq.push(7); x++; } while (x > tx) { seq.push(6); x--; } while (y < ty) { seq.push(5); y++; } while (y > ty) { seq.push(4); y--; }
          seq.push(8);
          const go = () => { const k = seq.shift(); if (k === undefined) return; press(k, 70); setTimeout(go, 150); };
          go();
        }
      });
    }
    setInterval(() => {
      try {
        const M = window.__wideM;
        const hide = () => { window.__hdBpOn = false; if (el && !el.hidden) { el.hidden = true; last = ""; } };
        if (!M || !M.HEAPU8 || !M._rotk_iwram || M._rotk_link_iwram) return hide();
        const iw = M._rotk_iwram(), ew = M._rotk_ewram();
        if (!iw || !ew) return hide();
        const H8 = M.HEAPU8, r32 = (o) => (H8[o] | H8[o + 1] << 8 | H8[o + 2] << 16 | H8[o + 3] << 24) >>> 0;
        const state = H8[iw + 0x41B0], sub = H8[iw + 0x41C0];
        const want = on() && state === 10;
        H8[ew + HDMODE] = want ? 1 : 0;
        if (!want || !(sub <= 3 || sub === 6)) return hide();
        const ui = r32(iw + 0x1FE0), cur = ui >>> 24 === 2 ? H8[ew + (ui & 0x3ffff) + 0x62] : ui >>> 24 === 3 ? H8[iw + (ui & 0x7fff) + 0x62] : 255;
        if (cur === 255) return hide();
        const cv = document.getElementById("mpCanvas"); if (!cv) return hide();
        const r = cv.getBoundingClientRect(); if (!r.width) return hide();
        if (!el) build();
        const p = H8[iw + 0x3F59] & 1, hero = iw + 0x3C00 + 0x1AC * p, hid = H8[hero + 0x19F];
        const inv = []; for (let i = 0; i < 16; i++) inv.push(r32(hero + 0x3C + 4 * i));
        const nOrc = Math.min(4, H8[ew + 0x3FFE0 + p]), orc = [];
        for (let i = 0; i < 4; i++) orc.push(i < nOrc ? (((H8[ew + 0x3FF00 + 8 * p + 2 * i] | H8[ew + 0x3FF01 + 8 * p + 2 * i] << 8) << 16) | 0x17FE) >>> 0 : 0xFFFFFFFF);
        const nas = hid === 1 ? 2 : hid === 0 ? 1 : 0, aw = [r32(ew + 0x3F2A0 + 8 * p), r32(ew + 0x3F2A4 + 8 * p)];
        const wordOf = (c) => c < 16 ? inv[c] : c < 24 ? orc[c - 20] : (aw[c - 24] & 15) === 7 ? aw[c - 24] : 0xFFFFFFFF;
        // the game's item menu (same reading as the item panel): base 0x030041B0, +8 Carve Rune, +0xC option, +0x14 Yes/No
        let menu = null;
        if (sub === 1) {
          const o = [[0, cur < 8 || cur >= 20 ? "Unequip" : "Equip"], [1, "Discard"]];
          if (cur >= 8 && cur < 16 && r32(iw + 0x41B8)) o.push([2, "Carve Rune"]);
          if (cur >= 8 && cur < 16) o.push([3, "Move Item"]);
          if (r32(iw + 0x4144) & 0x20) o.push([4, "Trade"]);
          menu = { q: "What would you like to do with this item?", o, sel: H8[iw + 0x41BC] };
        } else if (sub === 3) menu = { q: "Are you sure you want to discard this item?", o: [[0, "Yes"], [1, "No"]], sel: H8[iw + 0x41C4] };
        ctx = { H8, ew, iw, cur, sub, menu };
        // size: the page sits exactly over the game picture
        const fs = Math.max(9, Math.round(r.height * 0.029));
        const c = Math.max(30, Math.min(r.height * 0.86 / 8.3, (r.width * 0.55) / 4.9));
        const P = ew + 0x3F520, Q = ew + 0x3F740, has = H8[P + 10] === cur && r32(P);
        const worn = cur >= 8 && cur < 16 ? r32(Q + 4) : 0, wtext = worn ? str(H8, Q + 8, 200) : "";
        const key = [r.left, r.top, r.width, r.height, cur, sub, inv.join(), orc.join(), aw.join(), has ? r32(P) : 0, worn, wtext, menu ? menu.sel + ":" + menu.o.length : ""].join("/");
        window.__hdBpOn = true;
        if (key === last && !el.hidden) return;
        last = key;
        el.style.left = r.left + "px"; el.style.top = r.top + "px"; el.style.width = r.width + "px"; el.style.height = r.height + "px";
        el.style.setProperty("--fs", fs + "px"); el.style.setProperty("--c", Math.round(c) + "px");
        // left page
        let L = "";
        const w = wordOf(cur);
        if (has && w !== 0xFFFFFFFF) {
          const name = str(H8, P + 12, 44), text = str(H8, P + 0x38, 168), lv = H8[P + 9], low = H8[P + 11], col = H8[P + 8];
          const lines = text.replace(/\s*\(page 2 of your backpack[^)]*\)/, "").replace(/in an Orc Head slot/, "in the Orc Head slot").split(/, |\. (?=[A-Z])/).map((s) => s.trim()).filter(Boolean);
          L += '<div class="big">' + pic(w) + "</div>" +
            '<div class="nm" style="color:' + (COL[col] || "#f3ead6") + '">' + esc(name) + "</div>" +
            '<div class="wh">' + (cur < 8 || cur === 20 ? "Wearing" : cur >= 24 ? "Arrow slot" : "Backpack") + "</div>" +
            (lv ? '<div style="color:' + (low ? "#ff6450" : "#6fe06f") + '">Min. Level: ' + lv + "</div>" : "") +
            "<div>" + cmpLines(lines, wtext, fs) + "</div>";
        } else {
          const nm = (EQ.find((x) => x[0] === cur) || [0, cur >= 24 ? "Arrow" : cur >= 20 ? "Orc Head" : "Backpack"])[1];
          L += '<div class="nm" style="color:#c9b88f">' + esc(nm) + " slot</div><div class=\"wh\">Empty</div>";
        }
        if (menu) {
          L += '<div class="q">' + esc(menu.q) + '</div><div class="acts">' + menu.o.map(([id, s]) => '<b data-o="' + id + '"' + (id === menu.sel ? ' class="sel"' : "") + ">" + esc(s) + "</b>").join("") + "</div>";
        } else if (sub === 6) L += '<div class="q" style="color:#7cc8e8">Move Item: pick the backpack box to move it to.</div>';
        L += '<div class="tip">' + (sub === 0 ? "A or tap again: actions &middot; B: close" : "B: back") + "</div>";
        el.children[1].innerHTML = L; el.children[1].classList.toggle("mn", !!menu);
        // right page
        const cell = (cc, label, cls) => {
          const ww = wordOf(cc), ar = cc >= 24 && (ww & 15) === 7;
          return '<div class="cell ' + (cls || "") + " " + tier(ww) + (cc === cur ? " cur" : "") + '" data-c="' + cc + '">' + pic(ww) +
            (ar ? '<span class="ct">' + ((ww >>> 16) & 255) + "</span>" : "") + (label ? '<span class="lb">' + label + "</span>" : "") + "</div>";
        };
        let R = '<div class="row"><div class="hdr">Equipped</div><div class="gr eq">' +
          EQ.map(([cc, lb]) => cell(cc, lb === "Shield" && (wordOf(2) & 15) === 7 ? "Arrows" : lb, cc === 20 ? "oh" : "")).join("") + "</div></div>";
        R += '<div class="row"><div class="hdr">Backpack</div><div class="gr iv">' +
          INV.map((cc) => cell(cc, cc >= 20 ? "Orc Head" : "", cc >= 20 ? "oh" : "")).join("") + "</div></div>";
        if (nas) R += '<div class="row"><div class="gr ar">' + [24, 25].slice(0, nas).map((cc) => cell(cc, "Arrows", "ax")).join("") + "</div></div>";
        R += '<div class="bar"><b data-k="L">&#9666; L Skills</b><b data-k="R">Stats R &#9656;</b></div>';
        el.children[2].innerHTML = R;
        el.hidden = false;
      } catch (e) { if (el) el.hidden = true; window.__hdBpOn = false; }
    }, 80);
  })();
'''

rep('''  (function itemPanel() {
''', JS + '''
  (function itemPanel() {
''')
# the old item panel and the page-2 button step aside while the HD Backpack is up
rep('''        if (!M || !M.HEAPU8) return hide();
        const me = (window.__mp && window.__mp.me) || 0;
        const iw = M._rotk_link_iwram ? M._rotk_link_iwram(me) : M._rotk_iwram();
        const ew = M._rotk_link_ewram ? M._rotk_link_ewram(me) : M._rotk_ewram();''',
    '''        if (!M || !M.HEAPU8 || window.__hdBpOn) return hide();
        const me = (window.__mp && window.__mp.me) || 0;
        const iw = M._rotk_link_iwram ? M._rotk_link_iwram(me) : M._rotk_iwram();
        const ew = M._rotk_link_ewram ? M._rotk_link_ewram(me) : M._rotk_ewram();''')
rep('''            if (iwram < 0 || twoP() || gameState() !== 10) { btn.hidden = true; return; }''',
    '''            if (iwram < 0 || twoP() || gameState() !== 10 || window.__hdBpOn) { btn.hidden = true; return; }''')
open(out, 'w').write(t)
print('ok')
