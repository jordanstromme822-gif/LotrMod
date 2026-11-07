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

## Zoomed-out view (2026-11-07)

`main-modded.cpp` widens levels to 320x160. The game keeps only a 31x21-tile window
of BG2 (foreground) and BG3 (ground) in VRAM, rebuilt from a block map (u16 block per
32x32 px; layer A map `*0x03005FB4` / set `*0x03005FBC`, layer B map `*0x0300586C` /
set `*0x03005FC0`, width u16 `0x03005878`, camera `0x03005880`). Each frame the VRAM
window is matched against the block map to anchor it; the PPU margin provider then
reads margin tiles from the level. BG1 (sky) wraps, BG0 (HUD) stays native, non-level
screens get black bars. Sprites: the game skips OAM pieces with x > 255; the PC ROM
patch at 0x08002F90 (`adds r0,r5,#0; adds r0,#0x40; lsrs r0,r0,#6; cmp r0,#6; bhi`)
allows up to x < 384, and raw 240..383 is decoded as the right margin. PC ROM sha1
88f9075bcba049d51c693f98173c677873d7e04f (regenerate with the same game.toml + new sha).
The smoothing patch now also covers the wide view (`g_ws_render_io`,
`g_ws_margin_scroll_override` in gba_ppu).

## 4:3 view (2026-11-07)

Levels now render 320x240 (`view_geometry` adds 40 px above and below). The HUD
(BG0 rows 120..159) is remapped to the bottom of the canvas, and the PC ROM also
patches 0x08002F88 (`movs r0,#0x84`) so sprite pieces reach y=200; raw y 160..200 is
the bottom margin. PC ROM sha1 dd6d504c587ce487c983968f4f01748457b30ed8.

## Phone Play Room: "Wide 4:3, 60 fps" (2026-11-07)

The same engine runs in the Play Room page on phones (no threads or SharedArrayBuffer needed).

- `gbarecomp-pc-and-web.patch` (replaces the smooth60 patch; includes it): single-threaded browser build.
  The run loop becomes an `emscripten_set_main_loop` frame callback (present-in-place off), no blocking sleeps,
  every 8th smoothing picture verified, wide frames shown at full size.
- `web/pc-web.toml`: game config with extra recompiled code. The game's sound mixer lives in IWRAM and patches its own
  `ldrb ..., asr #5` to `asr #4` at boot, so the generator is run on a copy of the PC ROM with those 8 bytes already
  patched (`modded-pc-gen.gba`, see the 0x08FFAB40.. bytes), and the mixer region is one `code_copy` 0x03000B38..0x0300115C.
  Without this the mixer ran in the interpreter every frame (2x slower).
- `main-modded.cpp`: tile provider now remembers the last tile per layer (big win in the wide renderer).
- `web/build.sh`, `web/link.sh`, `web/shim.cpp`: emscripten 3.1.6 build (needs `web/compat.h` for std::bit_cast).
- The page builds the PC ROM itself from the Play Room's Modded game (two cull patches at 0x2F88/0x2F90) and writes its
  SHA-1 into the config, so custom hero stats work. Save = the account copy (`save-rotk-modded`).
- Speed on the test machine (2.1 GHz Xeon VM, headless Chromium): ~55 fps in levels, 60 on menus.
