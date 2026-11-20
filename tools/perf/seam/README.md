# Seamless journey checks (v227, 2026-11-20)

Headless real Play Room like `tools/perf/feel` (`WORK` holds `site/` with the artifact files, including `maps/t/`, and
`orig.gba`). Both warp to a level, put the hero 40 px from one of its exits and walk through it.

- `LV=93 node t_door.js` - real time: prints the level bytes (0x030041F8 / 0x03004174), the load flag and whether the
  flight is on, per game picture, and saves screenshots to `door/`. The flight must start on the picture where
  0x030041F8 changes, end after 0x03004174 matches, and the log must hold no "seam: gave up".
- `LV=56 OUT=pin56 node t_pin.js && python3 sheet.py pin56` - holds the camera at u = 0, 0.1 ... 0.97 (window.__seam.pin)
  and makes a contact sheet. u = 0 must match the game's own picture exactly, the map pictures must line up under the
  game picture, and the last one must match the picture after the flight.
- Tried: 93 > 104 (Haradrim camp), 20 > 21, 56 > 57 (Orthanc, into the Tower Levels).
