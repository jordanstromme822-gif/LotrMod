#!/usr/bin/env python3
"""Play Room: P2 runs inside ONE game (2026-11-16).

  python3 p2-one-game-v180.py in.html out.html

Jordan: "nobody is linking", "I don't need options for the features I want enabled". Once a local P2 is in the level
the engine stops the second game and a stand-in answers its link messages (recomp/link/link_main.cpp, rotk_link_one),
so both heroes run in one game: about 40% less work per frame in fights. Always on for local P2; online games keep
two games (each phone shows its own player's game).

Page side: the P2 helper (play()) read P2's own game. In one-game mode mem(1) reads game 1's memory... no: it reads
game 0's memory with the local-player byte (0x03003F59) answered as 1, so the helper still finds "its" hero (player
block 1) and P1 (block 0). P2's gear swap ran the Backpack menu in P2's own game; there is no P2 game now, so the
helper picks up upgrades but does not swap them in (wear macro skipped). Saves: P2's slot record is built inside P1's game
when P1 saves. P1's menus and pause: P2 waits.
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:90], n)
    s = s.replace(old, new)

rep('''    const mem = (i) => {
      const H8 = M.HEAPU8, iw = linkOn ? M._rotk_link_iwram(i) : M._rotk_iwram(), ew = linkOn ? M._rotk_link_ewram(i) : M._rotk_ewram();
      const at = (a) => ((a >>> 24) === 3 ? iw + (a & 0x7fff) : (a >>> 24) === 2 ? ew + (a & 0x3ffff) : -1);
      const r8 = (a) => { const o = at(a); return o >= 0 ? H8[o] : 0; };''',
'''    const mem = (i) => {
      // One game (v180): P2's game is switched off once P2 is in the level; P2 is player 1 inside game 0.
      const one = i === 1 && linkOn && !!(M._rotk_link_is_one && M._rotk_link_is_one()), g = one ? 0 : i;
      const H8 = M.HEAPU8, iw = linkOn ? M._rotk_link_iwram(g) : M._rotk_iwram(), ew = linkOn ? M._rotk_link_ewram(g) : M._rotk_ewram();
      const at = (a) => ((a >>> 24) === 3 ? iw + (a & 0x7fff) : (a >>> 24) === 2 ? ew + (a & 0x3ffff) : -1);
      const r8 = (a) => { const o = at(a); return o >= 0 ? (one && a === 0x03003F59 ? H8[o] | 1 : H8[o]) : 0; };''')

rep('''    const wearMacro = (k, f) => { wearRun = { k, phase: "open", t: f, tries: 0, outs: 0, log: [] }; };''',
'''    const wearMacro = (k, f) => { if (M._rotk_link_is_one && M._rotk_link_is_one()) return; wearRun = { k, phase: "open", t: f, tries: 0, outs: 0, log: [] }; };''')

rep('''boot = null; setBoot(null); p2(0); say(""); p2Loading(false); show("P2 joined", 2500);''',
'''boot = null; setBoot(null); p2(0); say(""); p2Loading(false); show("P2 joined", 2500);
      try { if (M._rotk_link_one) { M._rotk_link_one(); slog("one game: P2 runs inside P1's game"); } } catch (e) {}''')

# Saves: in one game P2's game never saves, so when P1's game saves, P2's 0x70-byte record is built inside P1's game
# by the game's own builder (rotk_link_p2_record) and goes into P2's slot (EEPROM bytes run reversed per 8-byte block).
rep('''      const merged = copies[0].slice(); merged.set(copies[1].subarray(so, so + 0x70), so);''',
'''      const merged = copies[0].slice(); merged.set(copies[1].subarray(so, so + 0x70), so);
      try {
        if (M._rotk_link_is_one && M._rotk_link_is_one() && M._rotk_link_p2_record && M._rotk_link_p2_record(buf)) {
          const rec = M.HEAPU8.slice(buf, buf + 0x70);
          for (let i = 0; i < 0x70; i++) copies[1][so + (i & ~7) + 7 - (i & 7)] = rec[i];
          merged.set(copies[1].subarray(so, so + 0x70), so); slog("P2 saved (one game)");
        }
      } catch (e) {}''')

# P1's own menus and pause: in one game the helper reads P1's game, so these are P1's screens, not P2's. P2 waits
# (it never presses B to "back out" of P1's Backpack or drives a save of its own).
rep('''      const s0 = state(0), s1 = state(1);
      if (wearRun) { try { runWear(f, s1); } catch (e) { wearRun = null; } return; }''',
'''      const s0 = state(0), s1 = state(1);
      if (wearRun) { try { runWear(f, s1); } catch (e) { wearRun = null; } return; }
      if (M._rotk_link_is_one && M._rotk_link_is_one()) {
        if ([10, 14, 15, 20, 6, 9, 16].includes(s0)) { p2(0); return; }
      }''')

open(dst, "w", encoding="utf-8").write(s)
print("ok")
