"""Play Room v271: P2 (the page-played second hero of a 2-player game) works in a big region.

python3 recomp/playroom/p2-region-v271.py IN.html OUT.html

P2's walking grid read the level's collision from EWRAM and gave up on maps over 512 x 512 spots, so in the Isengard
region (924 x 2000 spots, collision in ROM) P2 stood still: it never followed P1, never fought, and a door needing
both heroes never opened. Now the grid reads ROM-backed collision (window.__romFull) and, on a big map, covers a
window of 192 x 160 spots round the two heroes, its positions counted from the window's corner.
"""
import sys
src, out = sys.argv[1:3]
html = open(src, encoding='utf-8').read()
def rep(a, b):
    global html
    assert html.count(a) == 1, a[:80]
    html = html.replace(a, b)
rep("""      const pos = (p) => [m.r16(p + 0xae), m.r16(p + 0xb2)];
      const [x, y] = pos(hero), [px, py] = pos(oh);""",
"""      let gox = 0, goy = 0;   // v271: a big map's grid window corner (px); positions below count from it
      const pos = (p) => [m.r16(p + 0xae) - gox, m.r16(p + 0xb2) - goy];
      let [x, y] = pos(hero), [px, py] = pos(oh);""")
rep("""        const W = m.r16(0x03005F90), Hh = m.r16(0x03005F88), bm = m.r32(0x0300206C), ct = m.r32(0x03002068);
        if (W && Hh && W <= 512 && Hh <= 512) {
          const bw = W >> 2, cell = new Uint8Array(W * Hh), free = new Uint8Array(W * Hh);
          for (let cy = 0; cy < Hh; cy++) for (let cx = 0; cx < W; cx++) { const b = m.r16(bm + 2 * ((cx >> 2) + (cy >> 2) * bw)) & 0xfff, v = m.r8(ct + (b << 4) + ((cx & 3) | ((cy & 3) << 2))) & 7; cell[cx + cy * W] = v === 1 || v === 2 ? 0 : 1; }
          for (let cy = 1; cy < Hh - 1; cy++) for (let cx = 1; cx < W - 1; cx++) { const i = cx + cy * W; free[i] = cell[i] & cell[i - 1] & cell[i + 1]; }
          grid = { W, H: Hh, free };
        }""",
"""        const W0 = m.r16(0x03005F90), H0 = m.r16(0x03005F88), bm = m.r32(0x0300206C), ct = m.r32(0x03002068);
        // v271: collision may be in ROM (the big region's), and a map over 512 spots a side gets a window round both heroes
        const RF = window.__romFull, g8 = (a) => (a >>> 24) >= 8 ? (RF ? RF[a - 0x08000000] | 0 : 0) : m.r8(a), g16 = (a) => g8(a) | g8(a + 1) << 8;
        let W = W0, Hh = H0, ox = 0, oy = 0;
        if (W0 > 512 || H0 > 512) {
          const hx = (m.r16(hero + 0xae) + m.r16(oh + 0xae)) >> 4, hy = (m.r16(hero + 0xb2) + m.r16(oh + 0xb2)) >> 4;
          W = Math.min(W0, 192); Hh = Math.min(H0, 160);
          ox = Math.max(0, Math.min(W0 - W, hx - (W >> 1))) & ~3; oy = Math.max(0, Math.min(H0 - Hh, hy - (Hh >> 1))) & ~3;
        }
        if (W && Hh && W <= 512 && Hh <= 512) {
          const bw = W0 >> 2, cell = new Uint8Array(W * Hh), free = new Uint8Array(W * Hh);
          for (let cy = 0; cy < Hh; cy++) for (let cx = 0; cx < W; cx++) { const X = cx + ox, Y = cy + oy, b = g16(bm + 2 * ((X >> 2) + (Y >> 2) * bw)) & 0xfff, v = g8(ct + (b << 4) + ((X & 3) | ((Y & 3) << 2))) & 7; cell[cx + cy * W] = v === 1 || v === 2 ? 0 : 1; }
          for (let cy = 1; cy < Hh - 1; cy++) for (let cx = 1; cx < W - 1; cx++) { const i = cx + cy * W; free[i] = cell[i] & cell[i - 1] & cell[i + 1]; }
          if (grid0 && (grid0.ox !== ox * 8 || grid0.oy !== oy * 8)) blocked.clear();   // its cells were the old window's
          grid = { W, H: Hh, free, ox: ox * 8, oy: oy * 8 };
        }""")
rep("""      if (!grid || now - gridT > 2000) {
        gridT = now; grid = null; plan = null;""",
"""      if (!grid || now - gridT > 2000) {
        const grid0 = grid; gridT = now; grid = null; plan = null;""")
rep("""      if (!grid) { p2(0); return; }
      const list = [];""",
"""      if (!grid) { p2(0); return; }
      if (grid.ox || grid.oy) { gox = grid.ox; goy = grid.oy; x -= gox; y -= goy; px -= gox; py -= goy; }
      const list = [];""")
open(out, 'w', encoding='utf-8').write(html); print('ok', len(html))
