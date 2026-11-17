#!/usr/bin/env python3
"""Play Room v183: free-angle joystick keeps working when P2 joins (2026-11-17).

  python3 p2-one-joystick-v183.py in.html out.html

Jordan: "I lose Omni directional movment when p2 joins". The stick change queue (turn16.c fa_queue, EWRAM 0x0203FC00)
was written into both games and the page waited until neither queue was full. In one-game P2 (v182) the second game is
switched off, so its queue never empties: after 8 stick changes P1's game got no more and the hero fell back to 8 ways.
Now, once P2 runs inside P1's game, only game 0 gets the queue.
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
old = '''  const freeGames = (M) => M._rotk_link_on ? [0, 1].map((i) => [M._rotk_link_iwram(i), M._rotk_link_ewram(i)]) : [[M._rotk_iwram(), M._rotk_ewram()]];'''
new = '''  // v183: one-game P2 (the second game is switched off): only P1's game, whose queue is the one that empties.
  const freeGames = (M) => M._rotk_link_on ? (M._rotk_link_is_one && M._rotk_link_is_one() ? [0] : [0, 1]).map((i) => [M._rotk_link_iwram(i), M._rotk_link_ewram(i)]) : [[M._rotk_iwram(), M._rotk_ewram()]];'''
assert s.count(old) == 1
s = s.replace(old, new)
open(dst, "w", encoding="utf-8").write(s)
print("ok")
