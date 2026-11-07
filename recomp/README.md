# Return of the King: GBARecomp experiment

A trial run of [GBARecomp](https://github.com/mstan/gbarecomp) on the original
US/Europe ROM (BLRE, SHA-1 `ec3d126d37ea6e2ad7030d8a99cf87c6e46c03fd`), done
2026-11-07 on Linux. This turns the GBA code into native C++ instead of
emulating it. **No ROM or BIOS is included here.**

## Result

- The recompiler found 11,344 game functions. The generated code compiles.
- With the open-source [Cult-of-GBA BIOS](https://github.com/Cult-of-GBA/BIOS)
  and the runtime's BIOS HLE, the native build boots to the language screen,
  runs the logos, title menu, hero select and story slides, and plays the
  first level (Aragorn walks, attacks, in-level dialogue shows). It ran headless
  at about 195 frames per second.
- The first build crashed entering the level: the game runs code it copies
  from ROM into IWRAM. The `[[code_copy]]` entries in `game.toml` (found by
  comparing live IWRAM with the ROM in mGBA) and the `[[extra_func]]` entries
  the runtime proposed fixed that.
- Not checked: sound, saving, later levels, 2-player, the Modded ROM patches.
  About 160 million instructions per 7,000 frames still go through the
  runtime's interpreter, so more `[[extra_func]]` work would make it fully native.

## Rebuild

1. Clone gbarecomp next to this folder as `gbarecomp/` (with submodules) and
   build its `gba_recompile` target.
2. `GBARECOMP_CORE=gbarecomp/build/gba_recompile python3 gbarecomp/tools/cli.py build --rom <your rom> --output port --config game.toml`
3. Copy `port/generated` here, then `cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build`.
4. `GBARECOMP_INPUT_REPLAY=first-level.input ./build/RotkRecomp --bios <bios.bin> --rom <your rom> --frames 5300 --dump-png out.png game.toml`

`first-level.input` presses through the menus and story into the first level
(KEYINPUT values, active low, per frame).

## 60 fps smoothing (2026-11-07)

The game draws a new picture every other VBlank (30 fps). `gbarecomp-smooth60.patch`
adds `FrameSmoother` to the runtime: when a new picture arrives it first shows an
in-between picture (world layers scrolled halfway, world sprites shifted with the
camera, HUD left alone), then the real one, so the camera glides at 60 fps with one
VBlank of delay. The world layers here scroll coarsely (fine scroll 0..7, map redrawn
a tile over), so a halfway view outside 0..7 is drawn from the previous frame's map.
It only kicks in when re-rendering the new frame from the snapshot matches the real
picture. `GBARECOMP_SMOOTH=0` turns it off; `GBARECOMP_SMOOTH_TEST=dir,start,count`
dumps real (`r_`) and shown (`s_`, `m` = in-between) frames from headless runs.
Apply with `git apply` inside the gbarecomp clone (base 351572f).
