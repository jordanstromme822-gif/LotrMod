# Feel checks (v223, 2026-11-20)

Headless real Play Room (Playwright, https://site.test routed to `$WORK/site`, game file `$WORK/orig.gba`), warps to
Moria (level 82). `PAGE=<built html>` tests a page other than `site/index.html`.

- `MODE=stick DIRS=0,8,...,248 HOLD=700 node t_walk.js > w.txt; python3 sum.py w.txt 0,8,...` - free-stick walk at each
  angle; "leg frames" < 15 while moving = sliding with still legs. v222: 7 of 32 angles froze, v223: 0.
- `HOLD=8 N=6 node t_tap.js` - quick B taps (keyboard x), counts swings. v222: 8-55 ms taps never swung; v223: all.
- `OX=45 OY=0 node t_step.js` - puts the hero 45 px from the nearest foe (test only), taps B: melee step walks in and hits.
