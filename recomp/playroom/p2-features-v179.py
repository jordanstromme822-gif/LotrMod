#!/usr/bin/env python3
"""Play Room v179, step 2 (after one-engine-v179.py): the 1-player features in local P2 games too.

  p2-features-v179.py in.html out.html tools/turn16/turn16.bin

With one engine built from the page ROM, both games of a local P2 game run every hook, so:
- HD Backpack (and its 12 slots) shows for P1 in P2 games. It drives P1's own game (machine 0); P2's game never runs P1's
  menus. Online games keep the old Backpack (both pages must stay byte-identical).
- Free 360 joystick + 16 facings + enemy turning: the hero hook, the stick mailbox and the chase flag go into BOTH games for
  P1's hero (player 0), at the same frame boundary, so the two games stay the same. Not online.
"""
import re, sys
src, dst, t16 = sys.argv[1:4]
s = open(src).read()
code = open(t16, "rb").read()
assert len(code) <= 0x1000
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a)); s = s.replace(a, b)
s, k = re.subn(r'game\.set\(hexBytes\("[0-9a-f]+"\), 0x9F000\);', lambda m: 'game.set(hexBytes("%s"), 0x9F000);' % code.hex(), s)
assert k == 1, k
# HD Backpack gate
rep("if (!M || !M.HEAPU8 || !M._rotk_iwram || M._rotk_link_iwram) return hide();",
    "if (!M || !M.HEAPU8 || !M._rotk_iwram || (M._rotk_link_iwram && (!M._rotk_link_on() || (window.__mp && window.__mp.online)))) return hide();   // v179: local P2 games too")
# free-angle: every game of the session
rep('const freeM = () => { const M = window.__wideM; return M && window.__turn16 && typeof M._rotk_ewram === "function" && !M._rotk_link_on ? M : null; };',
    '// v179 (one engine): local P2 games too; the writes go into both games (P1 is player 0 in both).\n'
    '  const freeM = () => { const M = window.__wideM; return M && window.__turn16 && typeof M._rotk_ewram === "function" && !(M._rotk_link_on && (!M._rotk_link_on() || (window.__mp && window.__mp.online))) ? M : null; };\n'
    '  const freeGames = (M) => M._rotk_link_on ? [0, 1].map((i) => [M._rotk_link_iwram(i), M._rotk_link_ewram(i)]) : [[M._rotk_iwram(), M._rotk_ewram()]];')
rep("try { const e = M._rotk_ewram() + FREE_MB, H = M.HEAPU8; H[e] = freeOn() ? (held ? 3 : 1) : 0; if (held) H[e + 1] = ang & 255; } catch (e) {}",
    "try {\n"
    "      const H = M.HEAPU8, fa = freeOn() ? (held ? 3 : 1) : 0, a = held ? ang & 255 : 0;\n"
    "      if (!M._rotk_link_on) { const e = M._rotk_ewram() + FREE_MB; H[e] = fa; if (held) H[e + 1] = a; return; }\n"
    "      // P2 game: queue the change for one game tick that neither game has reached yet (turn16.c fa_queue), in both games\n"
    "      if (fa === freeLast[0] && a === freeLast[1]) return;\n"
    "      const g = freeGames(M), dv = new DataView(H.buffer), t = Math.max(...g.map(([iw]) => dv.getUint32(iw + 0x41A4, true))) + 2;\n"
    "      if (g.some(([, ew]) => ((H[ew + 0x3FC41] - H[ew + 0x3FC40]) & 255) >= 8)) return;   // a full queue: try again next call, in both games alike\n"
    "      freeLast = [fa, a];\n"
    "      for (const [, ew] of g) { const q = ew + 0x3FC00, n = H[q + 0x41], e = q + 8 * (n & 7); dv.setUint32(e, t, true); H[e + 4] = fa; H[e + 5] = a; H[q + 0x41] = (n + 1) & 255; }\n"
    "    } catch (e) {}")
rep("window.__freeStick = (held, ang) => {", "let freeLast = [-1, -1];\n  window.__freeStick = (held, ang) => {")
old = """      const H = M.HEAPU8, iw = M._rotk_iwram(), ew = M._rotk_ewram(), dv = new DataView(H.buffer);
      if (H[iw + 0x41B0] !== 1) return;                              // gameplay only
      const hero = dv.getUint32(iw + 0x3C00, true);
      if (hero < 0x02000000 || hero >= 0x02040000) return;
      const at = ew + (hero - 0x02000000) + 0x14, cur = dv.getUint32(at, true);
      if (cur === FREE_GAME) dv.setUint32(at, FREE_HOOK, true);   // always on: it also turns Frodo's crossbows (16 facings)
      if (!freeOn()) H[ew + FREE_MB] = 0;                          // joystick 8 ways: the hook leaves his walk alone
      H[ew + FREE_MB + 3] = enemyChase() ? 1 : 0;                  // v177: chasing enemies walk straight at the hero
"""
new = """      const H = M.HEAPU8, dv = new DataView(H.buffer);
      for (const [iw, ew] of freeGames(M)) {
      if (H[iw + 0x41B0] !== 1) continue;                            // gameplay only
      const hero = dv.getUint32(iw + 0x3C00, true);
      if (hero < 0x02000000 || hero >= 0x02040000) continue;
      const at = ew + (hero - 0x02000000) + 0x14, cur = dv.getUint32(at, true);
      if (cur === FREE_GAME) dv.setUint32(at, FREE_HOOK, true);   // always on: it also turns Frodo's crossbows (16 facings)
      if (!freeOn()) H[ew + FREE_MB] = 0;                          // joystick 8 ways: the hook leaves his walk alone
      H[ew + FREE_MB + 3] = enemyChase() ? 1 : 0;                  // v177: chasing enemies walk straight at the hero
      }
"""
rep(old, new)
open(dst, "w").write(s)
print("p2 features patched", len(s))
