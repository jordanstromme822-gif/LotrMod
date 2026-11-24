#!/usr/bin/env python3
"""Play Room v263 (part 2): the Backpack page, redesigned for the iPhone first (Jordan, 2026-11-24: "Maybe its own ring
slot would be nice im just worried about the inventory and gear page, its already clustered and we struggled displaying
everything").

  hd-backpack-v263.py in.html out.html      (run after drop-labels-v263.py, which defines window.__itemTier)

- Worn gear is a Diablo 2 style paper doll instead of a 3 x 3 grid: Amulet, Helm, Cloak on top; Weapon, a tall Armor box
  and Shield in the middle; Ring, Gloves; Orc Head, Boots and (for archers) the Arrow slot at the bottom.
- A Ring slot of its own (the 10th worn box). The game has no ring yet: the slot waits for the Three Dwarf Rings
  (Phase 7, Thror's, the Firebeard and the Blacklock rings), and tapping it says so. Box id 40, never sent to the game.
- Words only on empty boxes (they used to sit on top of the item pictures). Box edges show the item's tier in the same
  Diablo 2 colours as the names on the ground: blue magic, yellow rare, gold unique (green kept for set items). The item
  name on the left page uses the same colours. The "can't wear yet" red is lighter so the picture still shows.
- Phone held upright: the page takes the whole screen (it used to fit inside the game picture, about the top 60%, so a
  long item description was cut down to its name). Details on top with room for every line, the doll and the backpack
  under it, then the buttons. Held sideways: three columns (details | doll | backpack).
- B Close and A Use buttons next to Stats and Skills, since the page covers the touch pad.
"""
import sys
src, dst = sys.argv[1:3]
s = open(src, encoding="utf-8").read()
if "v263 Backpack" in s:
    open(dst, "w", encoding="utf-8").write(s); print("v263 backpack already in"); sys.exit(0)
assert "window.__itemTier" in s, "run drop-labels-v263.py first"

# every change is inside the Backpack's own code (the Forge / Shrine after it has look-alike lines)
i0 = s.index("  (function hdBackpack() {"); i1 = s.index("  // v203 HD Forge / Shrine", i0)
head, s, tail = s[:i0], s[i0:i1], s[i1:]
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a)); s = s.replace(a, b)

# --- tiers: the shared Diablo 2 tiers (drop-labels.js) ---
rep("""    const tier = (w) => {
      if (w === 0xFFFFFFFF || !w) return "";
      const cat = w & 15;
      if (cat === 14) return "u";
      if (cat === 7) return "";
      return ((w >>> 16) & 255) !== 255 || (w >>> 24) !== 255 ? "m" : "";
    };""", """    // v263 Backpack: the Diablo 2 tiers shared with the names on the ground (drop-labels.js)
    const tier = (w) => { if (w === 0xFFFFFFFF || !w || (w & 15) === 15) return ""; const t = window.__itemTier ? window.__itemTier(w) : "n"; return t === "n" ? "" : "t" + t; };
    const RING = 40;   // the Ring box (page only until the Three Dwarf Rings, Phase 7)
    let ringAt = -1;   // the game's cursor when the Ring box was tapped (the Ring stays picked until the cursor moves)
    window.__hdBpRing = (on) => { if (on === undefined) return ringAt >= 0; ringAt = on && ctx ? ctx.cur : -1; last = ""; return ringAt >= 0; };
    const V3CSS =
      'html body #hdBp.v3 .lp{flex:0 0 34%}' +
      'html body #hdBp.v3 .rp{display:grid;grid-template-columns:auto auto;grid-template-rows:1fr auto;align-items:center;justify-content:space-evenly;column-gap:calc(var(--c)*0.42);row-gap:calc(var(--fs)*0.4);padding:calc(var(--fs)*0.7) calc(var(--fs)*0.8) calc(var(--fs)*0.6)}' +
      'html body #hdBp.v3 .rp .bar{grid-column:1 / span 2;gap:calc(var(--fs)*0.4);margin:0}' +
      'html body #hdBp.v3 .rp .bar b{padding:calc(var(--fs)*.42) calc(var(--fs)*.7);font-size:calc(var(--fs)*.82)}' +
      'html body #hdBp.v3 .rp .bar .mid{display:flex;gap:calc(var(--fs)*0.4)}' +
      'html body #hdBp.v3 .row{gap:calc(var(--fs)*0.35)}' +
      'html body #hdBp.v3 .dl{display:grid;grid-template-columns:repeat(3,calc(var(--c)*1.08));grid-auto-rows:calc(var(--c)*0.82);gap:calc(var(--c)*0.1);grid-template-areas:"am hm ck" "wp ar sh" "rg ar gl" "oh bt ax"}' +
      'html body #hdBp.v3 .dl .cell{height:auto}' +
      'html body #hdBp.v3 .iv{grid-template-columns:repeat(4,calc(var(--c)*0.98));grid-auto-rows:calc(var(--c)*0.82);gap:calc(var(--c)*0.1)}' +
      'html body #hdBp.v3 .iv .cell,html body #hdBp.v3 .ar .cell{height:auto}' +
      'html body #hdBp.v3 .ar{grid-template-columns:repeat(2,calc(var(--c)*0.98));grid-auto-rows:calc(var(--c)*0.82);margin-top:calc(var(--c)*0.1)}' +
      'html body #hdBp.v3 .cell .hp{left:8%;right:8%;top:8%;bottom:8%}' +
      'html body #hdBp.v3 .dl .cell[data-c="0"] .hp{top:18%;bottom:18%}' +
      'html body #hdBp.v3 .cell .lb{top:50%;bottom:auto;transform:translateY(-50%);font:700 calc(var(--c)*0.15)/1.1 var(--display,Georgia,serif);letter-spacing:.06em;text-transform:uppercase;color:#a8926a;opacity:.7;padding:0 4%}' +
      'html body #hdBp.v3 .cell.tm{border-color:#5f72e6;box-shadow:inset 0 0 calc(var(--c)*0.22) rgba(95,114,230,.35),inset 0 2px 6px rgba(0,0,0,.6)}' +
      'html body #hdBp.v3 .cell.tr{border-color:#d9c548;box-shadow:inset 0 0 calc(var(--c)*0.22) rgba(217,197,72,.32),inset 0 2px 6px rgba(0,0,0,.6)}' +
      'html body #hdBp.v3 .cell.tu{border-color:#c49a4e;box-shadow:inset 0 0 calc(var(--c)*0.26) rgba(214,170,90,.4),inset 0 2px 6px rgba(0,0,0,.6)}' +
      'html body #hdBp.v3 .cell.ts{border-color:#46b85c;box-shadow:inset 0 0 calc(var(--c)*0.22) rgba(70,184,92,.35),inset 0 2px 6px rgba(0,0,0,.6)}' +
      'html body #hdBp.v3 .cell.rw::after{background:rgba(190,24,12,0.26);box-shadow:inset 0 0 0 2px rgba(255,80,60,0.85)}' +
      'html body #hdBp.v3 .cell.gb{border-color:#ffc21a;box-shadow:0 0 0 1px #ffc21a,0 0 calc(var(--c)*0.22) rgba(255,190,30,0.8),inset 0 2px 6px rgba(0,0,0,0.55)}' +
      'html body #hdBp.v3 .cell.cur{border-color:#ffe08a;box-shadow:0 0 0 2px #f6c45a,0 0 calc(var(--c)*.35) rgba(255,190,80,.9),inset 0 0 calc(var(--c)*.25) rgba(255,200,110,.25)}' +
      'html body #hdBp.v3 .cell.rg.e .lb::before{content:"";display:block;margin:0 auto calc(var(--c)*0.06);width:calc(var(--c)*0.3);height:calc(var(--c)*0.3);border-radius:50%;border:calc(var(--c)*0.045) solid rgba(201,154,70,.55);box-shadow:0 0 calc(var(--c)*0.12) rgba(255,200,110,.25)}' +
      'html body #hdBp.v3 .cell.hid{visibility:hidden}' +
      'html body #hdBp.v3 .nm{overflow-wrap:anywhere}' +
      'html body #hdBp.v3 .tr3{font:700 calc(var(--fs)*0.75)/1 var(--display,Georgia,serif);letter-spacing:.12em;text-transform:uppercase}' +
      // phone held upright: the whole screen, details on top, then the doll and the backpack side by side or stacked
      'html body #hdBp.v3.up{padding:calc(env(safe-area-inset-top,0px) + var(--fs)*0.6) calc(env(safe-area-inset-right,0px) + var(--fs)*0.7) calc(env(safe-area-inset-bottom,0px) + var(--fs)*0.6) calc(env(safe-area-inset-left,0px) + var(--fs)*0.7);flex-direction:column;gap:calc(var(--fs)*0.9)}' +
      'html body #hdBp.v3.up .lp{flex:1 1 auto;min-height:calc(var(--fs)*9);padding:calc(var(--fs)*0.9) calc(var(--fs)*1)}' +
      'html body #hdBp.v3.up .lp .big{width:calc(var(--fs)*4.6);height:calc(var(--fs)*3.5);align-self:flex-start;float:none}' +
      'html body #hdBp.v3.up .rp{flex:0 0 auto;grid-template-columns:auto;grid-template-rows:auto auto auto;row-gap:calc(var(--fs)*0.8);padding-top:calc(var(--fs)*1)}' +
      'html body #hdBp.v3.up .rp .bar{grid-column:1}' +
      'html body #hdBp.v3.wd{box-sizing:border-box;padding-left:max(env(safe-area-inset-left,0px),calc(var(--fs)*0.6));padding-right:max(env(safe-area-inset-right,0px),calc(var(--fs)*0.6))}' +
      'html body #hdBp.v3.up .dl{grid-template-columns:repeat(3,calc(var(--c)*1.2))}';
    let cssOn = false;
    const addV3Css = () => { if (cssOn) return; cssOn = true; const st = document.createElement("style"); st.id = "hdBpV3Css"; st.textContent = V3CSS; document.head.appendChild(st); };""")

# --- a tap on the Ring box: never sent to the game ---
rep("""        let c = +t.dataset.c;
        if (sub === 0) {""", """        let c = +t.dataset.c;
        if (c === RING) { if (sub === 0) { ringAt = cur; last = ""; } return; }   // v263: the Ring box (page only)
        if (sub === 0) {""")

# --- where the page sits: the whole screen on an upright phone ---
rep("""        // size: the page sits exactly over the game picture
        const fs = Math.max(9, Math.round(r.height * 0.029));
        const c = Math.max(30, Math.min(r.height * 0.86 / 8.3, (r.width * 0.55) / 4.9));""",
"""        // v263: sideways the page sits exactly over the game picture; upright it takes the whole screen
        const stg = document.getElementById("stage"), sr = stg ? stg.getBoundingClientRect() : null;
        const up = innerHeight > innerWidth * 1.05 && sr && sr.width > 0;
        // sideways with the touch pad showing, the game picture is only the middle of the screen: cover the pad too (the bar has B and A)
        const wide = !up && sr && sr.width > r.width * 1.15;
        const B = (up || wide) ? { left: sr.left, top: sr.top, width: sr.width, height: sr.height } : { left: r.left, top: r.top, width: r.width, height: r.height };
        const fs = up ? Math.max(10, Math.min(15, Math.round(B.width * 0.034))) : Math.max(9, Math.round(B.height * 0.03));
        const c = up ? Math.max(34, Math.min((B.width - fs * 4) / 4.4, B.height * 0.074)) : Math.max(30, Math.min((B.height * 0.9 - fs * 5.2) / 3.75, (B.width * 0.64 - fs * 3) / 8.8));
        if (ringAt >= 0 && ringAt !== cur) ringAt = -1;
        const ringOn = ringAt >= 0 && sub === 0;""")
rep("""        const key = [r.left, r.top, r.width, r.height, cur, sub,""", """        const key = [B.left, B.top, B.width, B.height, up, wide, ringOn, cur, sub,""")
rep("""        el.style.left = r.left + "px"; el.style.top = r.top + "px"; el.style.width = r.width + "px"; el.style.height = r.height + "px";""",
"""        addV3Css(); el.classList.add("v3"); el.classList.toggle("up", !!up); el.classList.toggle("wd", !!wide);
        el.style.left = B.left + "px"; el.style.top = B.top + "px"; el.style.width = B.width + "px"; el.style.height = B.height + "px";""")

# --- left page: the name in its tier colour; the Ring box's own text ---
rep("""        const w = wordOf(vcur);
        if (has && w && (w & 15) !== 15) {""", """        const w = wordOf(vcur);
        if (ringOn) {
          L += '<div class="nm" style="color:#d9b25e">Ring slot</div><div class="wh">Empty</div>' +
            '<div style="margin-top:calc(var(--fs)*0.4);opacity:.85">Kept for the Three Dwarf Rings: Thr&oacute;r\\'s Ring, the Firebeard Ring and the Blacklock Ring, the rarest finds in Middle-earth. They come with Phase 7.</div>';
        } else if (has && w && (w & 15) !== 15) {""")
rep("""            '<div class="nm" style="color:' + (COL[col] || "#f3ead6") + '">' + esc(name) + "</div>" +""",
"""            '<div class="nm" style="color:' + (window.__itemTierColor ? window.__itemTierColor(w) : COL[col] || "#f3ead6") + '">' + esc(name) + "</div>" +
            (tier(w) ? '<div class="tr3" style="color:' + window.__itemTierColor(w) + '">' + { tm: "Magic", tr: "Rare", tu: "Unique", ts: "Set" }[tier(w)] + "</div>" : "") +""")

# --- right page: the paper doll, the backpack, the buttons ---
rep("""            (ar ? '<span class="ct">' + ((ww >>> 16) & 255) + "</span>" : "") + (label ? '<span class="lb">' + label + "</span>" : "") + "</div>";
        };""", """            (ar ? '<span class="ct">' + ((ww >>> 16) & 255) + "</span>" : "") + (label && (ww === 0xFFFFFFFF || !ww || (ww & 15) === 15) ? '<span class="lb">' + label + "</span>" : "") + "</div>";
        };
        const AREA = { 7: "am", 3: "hm", 4: "ck", 1: "wp", 0: "ar", 2: "sh", 5: "gl", 6: "bt", 20: "oh" };""")
rep("""        let R = '<div class="row"><div class="hdr">Equipped</div><div class="gr eq">' +
          EQ.map(([cc, lb]) => cell(cc, lb === "Shield" && (wordOf(2) & 15) === 7 ? "Arrows" : lb, cc === 20 ? "oh" : "")).join("") + "</div></div>";
        R += '<div class="row"><div class="hdr">Backpack</div><div class="gr iv">' +
          INV.map((cc) => cell(cc, "", "")).join("") + "</div></div>";
        if (nas) R += '<div class="row"><div class="gr ar">' + [24, 25].slice(0, nas).map((cc) => cell(cc, "Arrows", "ax")).join("") + "</div></div>";
        R += '<div class="bar"><b data-k="L">&#9666; L&nbsp; Stats</b><b data-k="R">Skills &nbsp;R &#9656;</b></div>';""",
"""        const at = (h, a) => h.replace('<div class="cell ', '<div style="grid-area:' + a + '" class="cell ');
        let R = '<div class="row"><div class="hdr">Equipped</div><div class="dl">' +
          EQ.map(([cc, lb]) => at(cell(cc, lb === "Shield" && (wordOf(2) & 15) === 7 ? "Arrows" : lb, cc === 20 ? "oh" : ""), AREA[cc])).join("") +
          at(cell(RING, "Ring", "rg e" + (ringOn ? " cur" : "")), "rg") +
          (nas ? at(cell(24, "Arrows", "ax"), "ax") : '<div class="cell hid" style="grid-area:ax"></div>') + "</div></div>";
        R += '<div class="row"><div class="hdr">Backpack</div><div class="gr iv">' +
          INV.map((cc) => cell(cc, "", "")).join("") + "</div>" +
          (nas > 1 ? '<div class="gr ar">' + cell(25, "Arrows", "ax") + "</div>" : "") + "</div>";
        R += '<div class="bar"><b data-k="L">&#9666; L&nbsp; Stats</b><span class="mid"><b data-k="B">B&nbsp; Close</b><b data-k="A">A&nbsp; ' + (sub === 0 ? "Use" : "OK") + '</b></span><b data-k="R">Skills &nbsp;R &#9656;</b></div>';""")
# the Ring box isn't the game's cursor box: no "cur" on the real cursor while the Ring is picked
rep("""(ctx.sub === 6 ? (cc === ctx.vtg ? " cur" : "") + (cc === vcur ? " mv" : "") : cc === vcur ? " cur" : "")""",
    """(ctx.sub === 6 ? (cc === ctx.vtg ? " cur" : "") + (cc === vcur ? " mv" : "") : cc === vcur && !ringOn ? " cur" : "")""")
# --- the d-pad (v220 grid wrap, after the backpack): the Ring box is a page box, never the game's ---
def trep(a, b):
    global tail
    assert tail.count(a) == 1, a[:70]
    tail = tail.replace(a, b)
trep("""    if (id < 4 || id > 8) return false;
    if (!v) { if (held[id]) { delete held[id]; return true; } return false; }""",
"""    if (id < 4 || id > 8) return false;
    if (!v) { if (held[id]) { delete held[id]; return true; } return false; }
    if (st === 10 && sub === 0 && id === 8 && window.__hdBpRing && window.__hdBpRing()) { held[8] = 1; return true; }   // v263: A on the empty Ring box does nothing""")
trep("""        const to = nearBox("#hdBp .cell[data-c]", from, id); held[id] = 1;
        if (to === null || busy) return true;
        H[ew + 0x3F603] = to + 1; walkSeq([5]);""",
"""        const to = nearBox("#hdBp .cell[data-c]", from, id); held[id] = 1;
        if (to === null || busy) return true;
        if (to === 40) { if (window.__hdBpRing) window.__hdBpRing(true); return true; }   // v263: the Ring box (page only)
        if (from === 40 && window.__hdBpRing) window.__hdBpRing(false);
        H[ew + 0x3F603] = to + 1; walkSeq([5]);""")
open(dst, "w", encoding="utf-8").write(head + s + tail)
print("ok v263 backpack")
