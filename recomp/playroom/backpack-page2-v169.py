"""Play Room v169: Backpack page 2 for the Orc Head and arrow slots (Jordan, 2026-11-11).
Usage: backpack-page2-v169.py in.html old.gba new.gba out.html
  in.html  = the live page (v168), already rewritten by tools/orcslots/pagejs.py for the new orcslots.bin
  old.gba  = page ROM built from the page before pagejs (buildGame("mod")), new.gba = the same from in.html
What it adds:
  - "Orc Heads >" / "< Backpack" button (#bpBtn) in the Backpack (state 10, no menu open), 1-player only: it sets PGREQ
    0x0203F600 and presses Down; the game code turns the page in its cursor move.
  - Item text panel: Frodo/Legolas only move their item menu into the panel in 2-player games now (page 2 gives the
    1-player Backpack its whole text box back).
  - 2-player games keep the 2-player engine built 2026-11-10 (old slot code, slots locked in link games). That engine runs
    its hook code natively, so it must get a ROM with the old code: linkRom() puts back every byte that differs between
    old.gba and new.gba (91 ranges, about 20 KB) before the 2-player engine (P2 join and online) gets the ROM.
  - 1-player engine ?v=169 (web-backpack2 build, generated from new.gba)."""
import sys, base64

src, old, new, out = sys.argv[1:5]
t = open(src).read()
a = open(old, 'rb').read(); b = open(new, 'rb').read()
assert len(a) == len(b)
rng = []; i = 0; n = len(a)
while i < n:
    if a[i] != b[i]:
        j = i
        while j < n and (a[j] != b[j] or (j + 8 < n and a[j:j + 8] != b[j:j + 8])): j += 1
        rng.append((i, j - i)); i = j
    else: i += 1
blob = b''.join(a[o:o + l] for o, l in rng)
print('ranges', len(rng), 'bytes', len(blob))

def rep(x, y, cnt=1):
    global t
    k = t.count(x); assert k == cnt, (x[:80], k); t = t.replace(x, y)

# 1. the button
rep('''  #pageBtn[hidden] { display: none; }
''', '''  #pageBtn[hidden] { display: none; }
  /* Backpack page button (Jordan, 2026-11-11): turns between the backpack and page 2 (Orc Head and arrow slots). */
  #bpBtn { position: absolute; z-index: 28; left: calc(max(env(safe-area-inset-left, 0px), 0px) + 10px); top: calc(env(safe-area-inset-top, 0px) + 10px);
    min-width: 96px; height: 36px; padding: 0 14px; border-radius: 18px; border: 2px solid #d8b25a; background: rgba(14,11,8,0.82); color: #f3ead6;
    font: 700 14px/1 var(--display); letter-spacing: 0.06em; box-shadow: 0 0 0 2px rgba(0,0,0,0.6), 0 0 12px rgba(240,170,80,0.3);
    touch-action: none; -webkit-user-select: none; user-select: none; cursor: pointer; }
  #bpBtn.on { background: radial-gradient(circle at 50% 40%, #8a6020 0%, #4a3010 70%); color: #fff6dc; border-color: #f6dc94; }
  #bpBtn[hidden] { display: none; }
''')
rep('''  <button id="pageBtn" type="button" hidden>Page 1 of 2</button>
''', '''  <button id="pageBtn" type="button" hidden>Page 1 of 2</button>
  <button id="bpBtn" type="button" hidden>Orc Heads &#9656;</button>
''')
rep('''      // Legolas's arrow slots (Jordan, 2026-11-08): two arrow-only slots under the Orc Head slots (tools/orcslots). In play
''', '''      // Backpack page 2 (Jordan, 2026-11-11): the Orc Head and arrow slots have their own Backpack page (tools/orcslots).
      // Down from the grid's bottom row turns to it and up from the Orc Head row turns back; this button does the same in one tap
      // (PGREQ 0x0203F600 + a Down press, turned by the game code's cursor move). 1-player only: 2-player games keep the old slots.
      (() => {
        const btn = $("bpBtn"), PGREQ = 0x0203F600;
        const ewOf = () => { try { if (window.__mp && window.__mp.ewram) return window.__mp.ewram(); if (window.__mp && window.__mp.wide && window.__mp.M._rotk_ewram) return window.__mp.M._rotk_ewram(); } catch (e) {} return iwram >= 0x40000 ? iwram - 0x40000 : -1; };
        const twoP = () => { try { const mp = window.__mp; return !!(mp && (!mp.wide || mp.online || (mp.M && mp.M._rotk_link_on && mp.M._rotk_link_on()))); } catch (e) { return true; } };
        const H = () => emu.Module.HEAPU8;
        setInterval(() => {
          try {
            if (iwram < 0 || twoP() || gameState() !== 10) { btn.hidden = true; return; }
            const h = H(), ew = ewOf(); if (ew < 0) { btn.hidden = true; return; }
            const ui = (h[iwram + 0x1FE0] | h[iwram + 0x1FE1] << 8 | h[iwram + 0x1FE2] << 16 | h[iwram + 0x1FE3] << 24) >>> 0;
            const cur = ui >>> 24 === 2 ? h[ew + (ui & 0x3ffff) + 0x62] : ui >>> 24 === 3 ? h[iwram + (ui & 0x7fff) + 0x62] : 255;
            const sub = h[iwram + 0x41C0], p2 = cur >= 20 && cur <= 25;
            btn.hidden = sub !== 0 || cur === 255;
            const tx = p2 ? "\\u25C2 Backpack" : "Orc Heads \\u25B8";
            if (btn.textContent !== tx) btn.textContent = tx;
          } catch (e) { btn.hidden = true; }
        }, 150);
        btn.addEventListener("pointerdown", (e) => {
          e.preventDefault();
          // PGREQ plus a short Down press: the game code makes the turn in its own cursor move (a turn made outside it
          // left the cursor showing the picture of the item it had been on)
          try { const ew = ewOf(); if (ew >= 0) { H()[ew + (PGREQ & 0x3ffff)] = 1; emu.gameManager.simulateInput(0, 5, 1); setTimeout(() => { try { emu.gameManager.simulateInput(0, 5, 0); } catch (e) {} }, 90); } } catch (e) {}
          btn.classList.add("on"); setTimeout(() => btn.classList.remove("on"), 140);
        });
      })();
      // Legolas's arrow slots (Jordan, 2026-11-08): two arrow-only slots under the Orc Head slots (tools/orcslots). In play
''')

# 2. item text panel: the Frodo/Legolas menu-in-panel only where the old slot code still runs (2-player engine)
rep('''hid = H8[iw + 0x3C00 + 0x1AC * lp + 0x19F], leg = hid === 0 || hid === 1;''',
    '''hid = H8[iw + 0x3C00 + 0x1AC * lp + 0x19F], leg = (hid === 0 || hid === 1) && !!M._rotk_link_iwram;   // v169: page 2 gives 1-player games the whole text back''')

# 3. old slot code for the 2-player engine
LR = ('''    // 2-player engine (rotk-link ?v=163) still runs the slot code from before Backpack page 2 natively, so it gets a ROM with
    // that code put back (v169: every byte that differs, %d ranges). Rebuild the 2-player engine to drop this.
    window.__linkRom = (r) => {
      const x = r.slice(), B = Uint8Array.from(atob("%s"), (c) => c.charCodeAt(0));
      const R = %s;
      let k = 0; for (let i = 0; i < R.length; i += 2) { x.set(B.subarray(k, k + R[i + 1]), R[i]); k += R[i + 1]; }
      return x;
    };
''' % (len(rng), base64.b64encode(blob).decode(), '[' + ','.join('%d,%d' % (o, l) for o, l in rng) + ']'))
rep('''  function buildGame(mod) {
''', LR.replace('\n    ', '\n  ').replace('    //', '  //', 1) + '''  function buildGame(mod) {
''')
rep('''      m.FS.writeFile("/data/game.gba", rom); m.FS.writeFile("/data/bios.bin", bios);''',
    '''      const romE = linkCfg ? window.__linkRom(rom) : rom;
      const shaE = linkCfg ? Array.from(new Uint8Array(await crypto.subtle.digest("SHA-1", romE)), (x) => x.toString(16).padStart(2, "0")).join("") : sha;
      m.FS.writeFile("/data/game.gba", romE); m.FS.writeFile("/data/bios.bin", bios);''')
rep('''      m.FS.writeFile("/data/game.toml", e.toml.split("dd6d504c587ce487c983968f4f01748457b30ed8").join(sha)''',
    '''      m.FS.writeFile("/data/game.toml", e.toml.split("dd6d504c587ce487c983968f4f01748457b30ed8").join(shaE)''')
# online games (2-player engine on both pages)
rep('''    const unb64 = (t) => Uint8Array.from(atob(t), (c) => c.charCodeAt(0));
    const rom = game.slice();
    const at = (o, hex) => hex.match(/../g).every((b, i) => rom[o + i] === parseInt(b, 16));''',
    '''    const unb64 = (t) => Uint8Array.from(atob(t), (c) => c.charCodeAt(0));
    const rom = window.__linkRom(game);
    const at = (o, hex) => hex.match(/../g).every((b, i) => rom[o + i] === parseInt(b, 16));''')

# 4. 1-player engine version
rep('''const V = isLink ? "?v=163" : "?v=163";''', '''const V = isLink ? "?v=163" : "?v=169";   // v169 solo: Backpack page 2 (web-backpack2 engine, 2026-11-11); link unchanged''')
open(out, 'w').write(t)
print('ok')
