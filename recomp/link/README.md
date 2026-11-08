# P2 helper: two linked games in the Wide engine

Jordan (2026-11-08): "Create a P2 button next to auto. The button allows you to choose one of the
currently non selected heroes from the load menu. After selecting, P2 updates its save when you save.
It acts like the auto except P2 stays on Auto's screen." Picture: Wide 60 fps.

## How it works

- `link_main.cpp` is the PC/web main with a link mode (`ROTK_LINK=1`). It runs two copies of the
  game in a `gbarecomp::GbaMultiplayerSession` joined by the link cable, shows only game 0 (P1) with
  the wide view and in-between pictures, and takes P2's buttons from the page (`rotk_link_p2`).
- Exports for the page: `rotk_link_on`, `rotk_link_frames`, `rotk_link_iwram(i)`, `rotk_link_ewram(i)`,
  `rotk_link_save(i, out)` (512-byte EEPROM copy, returns 1 when changed), `rotk_link_level(82)`
  (forces Moria on both games while the level is still pending after Choose Your Path).
- The session needs every guest PC to have native code, so:
  - the Cult-of-GBA BIOS is recompiled too (`cobios.toml`, generated into the runtime with
    `GBARECOMP_GENERATED_BIOS_DIR`),
  - `game-link.toml` adds the misses found in link play plus every Thumb function-pointer target in the
    ROM (aligned word `0x08xxxxx1` pointing at a `PUSH {..,LR}`),
  - `mixer_hook.cpp` runs the game's self-modifying IWRAM sound mixer (0x03000B38) and IRQ helper
    (0x03000004) natively,
  - any remaining miss is bridged through the interpreter and printed once
    (`[gbarecomp:link] bridged <pc>`); add it to `game-link.toml`.
- `gbarecomp-link.patch`: runtime changes (session hooks on game 0 only, bridging, slice lookahead,
  `runtime_web_run_frames` for the web).
- The web build needs `-fwasm-exceptions` for the runtime libraries, `link_main`, `mixer_hook`, the shim
  and the final link: the session yields with a C++ exception.

## Page side (Play Room `wideP2`)

- The P2 button sits next to Auto. Solo: lists the saved heroes other than the loaded slot
  (`0x03005834`); picking one stores `{p1, p2, moria}` in sessionStorage `rotk-p2` and reloads.
- Start: both games go Title → Multiplayer → Load Game, each cursor (`0x030041BC`) moves to its slot,
  then P1 presses A three times on Choose Your Path.
- Saved-games file: slot k at `0x40 + 0x70 k`, 8-byte blocks with their bytes reversed (hero =
  byte `0x62 >> 4`, level = byte `0x5B` + 1). The page keeps both games' EEPROM copies and writes P1's
  file with slot `p2` taken from P2's game.
- Pause: state 16; `0x030041C0` = 2 means "waiting for the other player". When P1 picks Save Game
  (P1 state 9), P2 saves its own slot (A into the save screen, wait 150 frames, A only if the cursor is
  on P2's slot, Left + A for Yes, A, B). When P1 is waiting, P2 presses B.
- In a level P2 fights enemies and picks up herbs and food within 100 x 62 px of P1, and otherwise
  walks back next to P1. It never equips, discards, sells or uses the Forge.

## Speed notes (2026-11-08, v97)

Profile of the browser build in Moria (2 games, wide view): about 20% in `runtime_should_yield`
(called before every guest instruction of both games), about 14% drawing P1's wide picture,
about 15% in the session loop and device ticking. Compiling the game code at -O2 instead of -O1,
and skipping P2's sound mixing (`g_link_quiet_bus` in mixer_hook.cpp), made no measurable
difference, so v97 still ships the -O1 build without the quiet mixer.
