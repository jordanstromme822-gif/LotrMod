"""Play Room v186: the game's old Backpack never shows (Jordan, 2026-11-17: "Can we remove the old item menu from the game
and just have it fail to the new one").
Usage: hd-always-v186.py playroom-v185.html out.html (page only, same engines and game file as v185).
- HD Backpack and HD Forge/Shrine are always on (the old localStorage "rotk-hdbp" = "0" switch is gone).
- Every Backpack substate is drawn by the HD Backpack, not only 0-3/6/8:
  - 4 Carve Rune: the rune picker is the game's second cursor (UI 0x03001FE4 +0x62, 0-3 = the hero's 4 runes, 4 = back);
    the page shows the 4 runes + Back as boxes with the game's own words (line_wrap capture), taps walk the cursor
    with Left/Right, a tap on the picked box presses A.
  - any other substate (confirm, after Move Item, trade...): the game's own words plus OK / Back buttons (A / B).
- While the Backpack is opening (cursor not set yet, 255) the HD page is drawn with no box picked instead of hiding.
Works in 1-player, P2 and online (page writes travel with the buttons since v180)."""
import sys
src, out = sys.argv[1:3]
t = open(src).read()
def rep(a, b, n=1):
    global t
    k = t.count(a); assert k == n, (a[:90], k); t = t.replace(a, b)

# always on (Backpack + shop)
rep('''    const on = () => { try { return localStorage.getItem("rotk-hdbp") !== "0"; } catch (e) { return true; } };''',
    '''    const on = () => true;   // v186: always (Jordan: no old item menu)''', 2)

# every substate, and no hiding while the cursor is not set yet
rep('''        if (!want || !(sub <= 3 || sub === 6 || sub === 8)) return hide();   // v181: 8 = a message (level too low...)
        const ui = r32(iw + 0x1FE0), cur = ui >>> 24 === 2 ? H8[ew + (ui & 0x3ffff) + 0x62] : ui >>> 24 === 3 ? H8[iw + (ui & 0x7fff) + 0x62] : 255;
        if (cur === 255) return hide();''',
'''        if (!want) return hide();   // v186: every substate (v181: 8 = a message; 4 = Carve Rune; others = the game's words + OK/Back)
        const ui = r32(iw + 0x1FE0), cur = ui >>> 24 === 2 ? H8[ew + (ui & 0x3ffff) + 0x62] : ui >>> 24 === 3 ? H8[iw + (ui & 0x7fff) + 0x62] : 255;''')
rep('''        const wordOf = (c) => c >= 30 ? (c - 30 === win ? inv[15] : stash[c - 30]) : c < 16''', '''        const wordOf = (c) => c > 34 ? 0xFFFFFFFF : c >= 30 ? (c - 30 === win ? inv[15] : stash[c - 30]) : c < 16''')
# shop: keep the HD shop up while the shop cursor is briefly unset
rep('''        if (scur > 10) return hide();''', '''        if (scur > 10) { if (el && !el.hidden) { window.__hdShopOn = true; return; } return hide(); }   // v186''')
rep('''        const ui2 = r32(iw + 0x1FE4), tg = sub !== 6 ? 255 :''', '''        const ui2 = r32(iw + 0x1FE4), tg = sub !== 6 && sub !== 4 ? 255 :''')
rep('''        const vtg = tg === 15 ? 30 + win : tg;   // v181: Move Item's target box''',
    '''        const vtg = sub === 4 ? 255 : tg === 15 ? 30 + win : tg;   // v181: Move Item's target box (v186: sub 4 = rune cursor)
        const other = !(sub <= 4 || sub === 6 || sub === 8);
        const words = sub === 4 || other ? gameText(H8, ew).filter((q) => q.x >= 112).map((q) => q.s).join(" ") : "";''')
rep('''        ctx = { H8, ew, iw, cur, vcur, win, sub, menu, tg, vtg };''', '''        ctx = { H8, ew, iw, cur, vcur, win, sub, menu, tg, vtg };
        if (cur === 255) last = "";''')
rep('''menu ? menu.sel + ":" + menu.o.length : "", vtg, msg].join("/");''', '''menu ? menu.sel + ":" + menu.o.length : "", vtg, msg, tg, words].join("/");''')

# left page: Carve Rune picker and the other substates
rep('''        } else if (sub === 6) L += '<div class="q" style="color:#7cc8e8">Move Item: pick the backpack box to move it to.</div>';''',
'''        } else if (sub === 4) {   // v186: Carve Rune, the game's rune cursor (0-3 runes, 4 = back)
          L += '<div class="q" style="color:#d8b25a">Carve Rune: pick a rune</div><div class="rn">' +
            ["I", "II", "III", "IV", "Back"].map((s, i) => '<b data-r="' + i + '"' + (i === tg ? ' class="sel"' : "") + ">" + s + "</b>").join("") + "</div>" +
            (words ? '<div class="q">' + esc(words) + "</div>" : "") + '<div class="acts"><b class="sel" data-k="A">' + (tg === 4 ? "Back" : "Carve") + '</b><b data-k="B">Cancel</b></div>';
        } else if (other) {   // v186: anything else the game asks: its own words, OK / Back
          L += (words ? '<div class="q" style="color:#f8e050">' + esc(words) + "</div>" : "") + '<div class="acts"><b class="sel" data-k="A">OK</b><b data-k="B">Back</b></div>';
        } else if (sub === 6) L += '<div class="q" style="color:#7cc8e8">Move Item: pick the backpack box to move it to.</div>';''')
rep('''(sub === 0 ? "A or tap again: actions &middot; B: close" : sub === 6 ?''',
    '''(sub === 0 ? "A or tap again: actions &middot; B: close" : sub === 4 ? "&#9666; &#9656; pick &middot; A: carve &middot; B: back" : sub === 6 ?''')
rep('''el.children[1].classList.toggle("mn", !!menu);''', '''el.children[1].classList.toggle("mn", !!menu || sub === 4);''')

# rune boxes style + taps
rep('''        '#hdBp .row{display:flex;flex-direction:column;align-items:center;gap:calc(var(--fs)*0.25)}' +''',
'''        '#hdBp .row{display:flex;flex-direction:column;align-items:center;gap:calc(var(--fs)*0.25)}' +
        '#hdBp .rn{display:flex;gap:calc(var(--fs)*0.35);flex-wrap:wrap;margin-top:calc(var(--fs)*0.3)}' +
        '#hdBp .rn b{min-width:calc(var(--fs)*2.2);text-align:center;font:700 calc(var(--fs)*1)/1 var(--display,Georgia,serif);padding:calc(var(--fs)*0.5) calc(var(--fs)*0.4);border-radius:calc(var(--fs)*0.5);border:2px solid #5a4a34;background:linear-gradient(180deg,#3a3128,#231d17);color:#d9cfb8;cursor:pointer}' +
        '#hdBp .rn b.sel{border-color:#f6dc94;box-shadow:0 0 0 2px #f6dc94,0 0 calc(var(--fs)*0.8) rgba(255,200,100,0.8);color:#fff}' +''')
rep('''        const t = e.target.closest("[data-c],[data-o],[data-k]");
        if (!t) return;
        const { H8, ew, iw, cur, sub } = ctx;''',
'''        const t = e.target.closest("[data-c],[data-o],[data-k],[data-r]");
        if (!t) return;
        const { H8, ew, iw, cur, sub } = ctx;
        if (t.dataset.r !== undefined) {   // v186: a rune box: walk the game's rune cursor there (Left/Right), a tap on the picked one = A
          const want = +t.dataset.r; let n = 0;
          const step = () => {
            const u = (H8[iw + 0x1FE7] === 2 || H8[iw + 0x1FE7] === 3) ? ((H8[iw + 0x1FE4] | H8[iw + 0x1FE5] << 8 | H8[iw + 0x1FE6] << 16) >>> 0) : -1;
            if (u < 0 || H8[iw + 0x41C0] !== 4) return;
            const s = H8[iw + 0x1FE7] === 2 ? H8[ew + (u & 0x3ffff) + 0x62] : H8[iw + (u & 0x7fff) + 0x62];
            if (s === want) { if (n === 0) press(8); return; }
            if (++n > 6) return;
            press(want > s ? 7 : 6, 70); setTimeout(step, 260);
          };
          step();
          return;
        }''')
open(out, 'w').write(t)
print('ok')
