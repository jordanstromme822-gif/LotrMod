# Headless stress test for the CPU speed upgrade

`main.cpp` is a test `main` for the recompiled build: `ROTK_POKES="vblank:addr:value;..."`
writes RAM at given VBlanks, `ROTK_REPORT="v1,v2"` prints the game-frame counter (0x030041A4),
level and object count, `ROTK_GOD=1` keeps the hero's HP at 300. It needs the
`g_rotk_test_vblank` hook from `../gbarecomp-cpu-speed.patch`.

Recipe (2026-11-10): build a spawn-test ROM from the PC ROM (`rotk-modded-pc.gba`, sha dd6d504c)
with `python3 tools/engine/build_spawntest.py rotk-modded-pc.gba game.gba 285E00`, regenerate with
`gba_recompile`, build with this `main.cpp`, then `run.sh <speed %> <copies>` loads save slot 1,
warps to Hornburg Valley (47), clones the level's enemy groups next to the hero and measures.

Result, game frames per second (normal is 30), 300 VBlanks after spawning:

| extra monsters | 100% | 200% | 300% | 400% |
|---|---|---|---|---|
| 34 | 14.0 | 29.6 | | |
| 68 | 6.4 | 14.6 | 24.8 | 30.0 |
| 102 | | | | 22.2 |

Headless on a 4-core cloud server the native build ran 1861 VBlanks in 9-13 s at every speed.
