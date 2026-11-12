"""Play Room: Backpack redesign step 1 (Jordan, 2026-11-12; plan https://claude.ai/artifact/8eiYJjb2pi62WvS6thrKbq).
Usage: backpack-step1.py in.html old.gba live.gba new.gba out.html [solo engine version, default bp1]
  in.html  = the live page, already rewritten by tools/orcslots/pagejs.py for the new orcslots.bin
  old.gba  = the ROM the 2-player engine was built from (page ROM sha1 e686d065, before Backpack page 2)
  live.gba = page ROM built from the live page before pagejs (buildGame("mod")), new.gba = the same from in.html
What it adds:
  - HUD icons at the top right while playing: Ent Water, Fresh and Dried Kingsfoil with their counts, red at 0
    (hero = 0x03003C00 + 0x1AC*p: +0x1A9 bit0 Ent Water full, +0x1AA low nibble Fresh, high nibble Dried).
  - Item panel: green up / red down arrows beside each stat of a backpack item, against the item worn in its slot
    (orcslots.c panel_worn() writes the worn item's text to EWRAM 0x0203F740: +0 count, +4 worn item, +8 text), and a
    red "loses" line for each stat only the worn item has.
  - Action list: the item menu (Equip / Discard / Carve Rune / Move Item / Trade) and "Are you sure?" show in the panel
    for every hero, not only Frodo and Legolas.
  - window.__linkRom: the old ranges plus every byte that changed since the live page, taken from old.gba, so the
    2-player engine keeps running the code it was built from.
  - 1-player engine ?v=bp1 (web-backpack-step1 build, generated from new.gba). 2-player engine unchanged."""
import sys, re, base64, json

src, old, live, new, out = sys.argv[1:6]
t = open(src).read()
a = open(old, 'rb').read(); l = open(live, 'rb').read(); b = open(new, 'rb').read()
assert len(a) == len(l) == len(b)

def rep(x, y, cnt=1):
    global t
    k = t.count(x); assert k == cnt, (x[:80], k); t = t.replace(x, y)

# 1. __linkRom: union of the live page's ranges and what changed since, values from old.gba
m = re.search(r"  // 2-player engine \(rotk-link[^\n]*\n(?:  //[^\n]*\n)*  window\.__linkRom = \(r\) => \{\n.*?\n    const R = (\[[0-9,]*\]);\n.*?\n  \};\n", t, re.S)
assert m
R = json.loads(m.group(1))
mark = bytearray(len(a))
for i in range(0, len(R), 2): mark[R[i]:R[i] + R[i + 1]] = b'\1' * R[i + 1]
for i in range(len(a)):
    if l[i] != b[i]: mark[i] = 1
rng = []; i = 0; n = len(a)
while i < n:
    if mark[i]:
        j = i
        while j < n and (mark[j] or (j + 8 < n and any(mark[j:j + 8]))): j += 1
        rng.append((i, j - i)); i = j
    else: i += 1
# drop ranges where old.gba already equals new.gba (nothing to put back)
rng = [(o, k) for o, k in rng if a[o:o + k] != b[o:o + k]]
blob = b''.join(a[o:o + k] for o, k in rng)
print('linkRom ranges', len(R) // 2, '->', len(rng), 'bytes', len(blob))
LR = '''  // 2-player engine (rotk-link ?v=169) still runs the slot code from before Backpack page 2 natively, so it gets a ROM with
  // that code put back (Backpack step 1: every byte that differs, %d ranges). Rebuild the 2-player engine to drop this.
  window.__linkRom = (r) => {
    const x = r.slice(), B = Uint8Array.from(atob("%s"), (c) => c.charCodeAt(0));
    const R = %s;
    let k = 0; for (let i = 0; i < R.length; i += 2) { x.set(B.subarray(k, k + R[i + 1]), R[i]); k += R[i + 1]; }
    return x;
  };
''' % (len(rng), base64.b64encode(blob).decode(), '[' + ','.join('%d,%d' % (o, k) for o, k in rng) + ']')
t = t[:m.start()] + LR + t[m.end():]

# 2. action list for every hero
rep('''leg = (hid === 0 || hid === 1) && !!M._rotk_link_iwram;''',
    '''leg = hid >= 0;   // Backpack step 1 (Jordan, 2026-11-12): the item menu shows in the panel for every hero''')

# 3. compare arrows
rep('''        const right = cur < 8, key = [r32(P), right,''',
    '''        // Compare (Backpack step 1): the worn item in the same slot, text at EWRAM 0x0203F740 (orcslots.c panel_worn())
        const Q = ew + 0x3F740, worn = cur >= 8 && cur < 16 ? r32(Q + 4) : 0, wtext = worn ? str(H8, Q + 8, 200) : "";
        const right = cur < 8, key = [r32(P), right, worn, wtext,''')
rep('''          lines.map((t) => "<div>" + esc(t) + "</div>").join("");''',
    '''          cmpLines(lines, wtext, fs);''')
rep('''  (function itemPanel() {
''', '''  // Compare arrows (Backpack step 1, Jordan 2026-11-12): "7-14 Melee Damage" against the worn "5-11 Melee Damage" gets a
  // green up arrow (ranges by their middle), a stat the worn item doesn't have is green, and each stat only the worn item
  // has shows as a red line under the rest.
  const STAT_RE = /^([+-]?\\d+)(?:-(\\d+))?(%?)\\s+(.+?)\\.?$/;
  const statOf = (s) => { const x = s.match(STAT_RE); return x ? { k: x[4].toLowerCase() + x[3], v: x[2] ? (+x[1] + +x[2]) / 2 : +x[1] } : null; };
  function cmpLines(lines, wtext, fs) {
    const esc = (t) => t.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
    if (!wtext) return lines.map((t) => "<div>" + esc(t) + "</div>").join("");
    const W = {};
    wtext.split(/, |\\. (?=[A-Z])/).map((t) => t.trim()).filter(Boolean).forEach((t) => { const s = statOf(t); if (s) W[s.k] = { v: (W[s.k] ? W[s.k].v : 0) + s.v, t }; });
    const seen = {}, up = '<span style="color:#6fe06f;margin-left:0.35em">\\u25B2</span>', dn = '<span style="color:#ff6450;margin-left:0.35em">\\u25BC</span>';
    let h = lines.map((t) => {
      const s = statOf(t); if (!s) return "<div>" + esc(t) + "</div>";
      seen[s.k] = 1; const w = W[s.k] ? W[s.k].v : 0;
      return "<div>" + esc(t) + (s.v > w ? up : s.v < w ? dn : "") + "</div>";
    }).join("");
    const lost = Object.keys(W).filter((k) => !seen[k]);
    if (lost.length) h += '<div style="margin-top:' + Math.round(fs * 0.4) + 'px;color:#ff8b7b">' + lost.map((k) => "<div>Loses " + esc(W[k].t) + dn + "</div>").join("") + "</div>";
    return h + '<div style="margin-top:' + Math.round(fs * 0.4) + 'px;font-size:' + Math.round(fs * 0.8) + 'px;opacity:0.65">Arrows: against what you wear</div>';
  }

  // HUD icons (Backpack step 1, Jordan 2026-11-12): Ent Water, Fresh and Dried Kingsfoil at the top right while playing,
  // with their counts; an icon turns red when it is at 0. Read from the local hero: 0x03003C00 + 0x1AC*p, +0x1A9 bit0 Ent
  // Water full, +0x1AA low nibble Fresh Kingsfoil, high nibble Dried Kingsfoil.
  (function hudItems() {
    const ICON = {
      ent: (c) => '<svg viewBox="0 0 16 16" width="100%" height="100%"><path d="M6 1.5h4v1.6l-.6.7v2.4l3.4 5.2a2.2 2.2 0 0 1-1.8 3.4H5a2.2 2.2 0 0 1-1.8-3.4l3.4-5.2V3.8L6 3.1z" fill="' + c[0] + '" stroke="#0b0806" stroke-width="1"/><path d="M4.6 10.4h6.8l1 1.6a1.2 1.2 0 0 1-1 1.8H4.6a1.2 1.2 0 0 1-1-1.8z" fill="' + c[1] + '"/></svg>',
      leaf: (c) => '<svg viewBox="0 0 16 16" width="100%" height="100%"><path d="M3 13.5C2.5 7 7 2.5 13.5 2.5 13.5 9 9 13.5 3 13.5z" fill="' + c[0] + '" stroke="#0b0806" stroke-width="1"/><path d="M3.2 13.3 11 5.3" stroke="' + c[1] + '" stroke-width="1.1" fill="none"/></svg>',
    };
    const RED = ["#7a2a24", "#ff6450"];
    let el = null, shown = "";
    setInterval(() => {
      try {
        const M = window.__wideM, hide = () => { if (el && !el.hidden) { el.hidden = true; shown = ""; } };
        if (!M || !M.HEAPU8 || !document.body.classList.contains("playing")) return hide();
        const me = (window.__mp && window.__mp.me) || 0;
        const iw = M._rotk_link_iwram ? M._rotk_link_iwram(me) : M._rotk_iwram();
        if (!iw) return hide();
        const H8 = M.HEAPU8;
        if (H8[iw + 0x41B0] !== 1) return hide();
        const hero = iw + 0x3C00 + 0x1AC * (H8[iw + 0x3F59] & 1);
        const ent = H8[hero + 0x1A9] & 1, kf = H8[hero + 0x1AA], fresh = kf & 15, dried = kf >> 4;
        const cv = document.getElementById("mpCanvas"); if (!cv) return hide();
        const r = cv.getBoundingClientRect(); if (!r.width) return hide();
        const s = Math.max(18, Math.round(r.height * 0.06));
        const key = [ent, fresh, dried, Math.round(r.right), Math.round(r.top), s].join("/");
        if (key === shown && !el.hidden) return;
        shown = key;
        if (!el) { el = document.createElement("div"); el.id = "hudItems"; el.hidden = true; document.body.appendChild(el); }
        el.style.cssText = "position:fixed;z-index:26;pointer-events:none;display:flex;gap:" + Math.round(s * 0.35) + "px;align-items:center;" +
          "right:" + Math.round(window.innerWidth - r.right + s * 0.4) + "px;top:" + Math.round(r.top + s * 0.35) + "px;padding:" + Math.round(s * 0.18) + "px " + Math.round(s * 0.35) + "px;" +
          "border-radius:" + Math.round(s * 0.5) + "px;background:rgba(8,6,4,0.55);font:700 " + Math.round(s * 0.55) + "px/1 var(--ui, system-ui, sans-serif);";
        const one = (name, svg, n) => '<span title="' + name + '" style="display:inline-flex;align-items:center;gap:' + Math.round(s * 0.12) + 'px;color:' + (n ? "#f3ead6" : "#ff6450") + '">' +
          '<span style="display:inline-block;width:' + s + "px;height:" + s + 'px">' + svg + "</span>" + n + "</span>";
        el.innerHTML = one("Ent Water", ICON.ent(ent ? ["#7cc8e8", "#3a9a5a"] : RED), ent) +
          one("Fresh Kingsfoil", ICON.leaf(fresh ? ["#5fc444", "#2a6a1e"] : RED), fresh) +
          one("Dried Kingsfoil", ICON.leaf(dried ? ["#b8943e", "#6a5020"] : RED), dried);
        el.hidden = false;
      } catch (e) { if (el) el.hidden = true; }
    }, 200);
  })();

  (function itemPanel() {
''')

# 4. 1-player engine version (2-player engine unchanged)
m = re.search(r'const V = isLink \? ("\?v=[^"]*") : "\?v=[^"]*";', t); assert m
SOLO_V = sys.argv[6] if len(sys.argv) > 6 else "bp1"
t = t[:m.start()] + 'const V = isLink ? %s : "?v=%s";   // Backpack (2026-11-12): solo engine with the compare record / HD Backpack cursor; link unchanged' % (m.group(1), SOLO_V) + t[m.end():]
open(out, 'w').write(t)
print('ok')
