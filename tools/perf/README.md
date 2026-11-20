# Play Room speed checks (2026-11-18)

Real Play Room page in headless Chromium (Playwright routes https://site.test/** to a folder holding index.html,
wide/ and skin/ from the artifact; the game file is fed to the #rom input).

- `node run.js <siteDir> <level> [secs] [profile.json]` - warps to a level, walks/attacks, prints pictures per second.
  Env: `DPR=3` (phone-sized canvas), `PASSES=<secs>` + passes.js = time of every WebGL pass (1-pixel read after each
  draw, so SwiftShader times are relative GPU cost), `CMP=1` = render the same paused frame with the v195 changes off/on
  and print pixel differences (needs a test page with ALIVE_OLD, see smooth-v195 notes), `SAVE=<backup json> P2=0,1
  NOWARP=1` = start a P2 game from a saved-games backup.
- `node prof.js profile.json` - self time by function.
- Set `fps < 40` -> `fps < 0` in the test page, otherwise the slow check drops SwiftShader to plain pixels.

v195 numbers (Fangorn, 844x390 at 3x pixel ratio, SwiftShader): last lighting pass 480 -> 191 ms, alive pass 56 -> 20 ms,
whole picture 2.3 -> 3.4 pictures/s. Same-frame pixel difference: mean 0.8-2.2 of 255, < 0.7% of pixels over 24.
