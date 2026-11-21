# One engine (v179, 2026-11-16)

Jordan: "I just want one, not multiple, combine them all into the 1". The 2-player build now runs 1-player games too, so
every hook (Orc Head slots, HD Backpack, 12 slots, turn16 heroes + enemies) works in both, and the old 1-player engine is gone.

Box layout these scripts expect (/tmp/rc/b2, rebuilt per session):
- gbarecomp 351572f with the runtime patches in this order: ../../gbarecomp-pc-and-web.patch, ../gbarecomp-link.patch,
  ../../smooth-v87-steady-poses.patch (`git apply -p4`), ../engine-speed-v116.patch, ../multiplayer-slice-speed.patch,
  ../../gbarecomp-cpu-speed.patch (`patch -p1 -F3`), ../../gbarecomp-obj-ext.patch, ../../gbarecomp-oam-ext.patch,
  `tools/skin/apply_skin_ppu.py src/gba/gba_ppu.cpp`, the host_window_web.cpp half of ../../gbarecomp-skin.patch,
  ../link-speed.patch, ../link-alu-yield.patch, ../one-game-partner.patch. Native `gba_recompile` from that tree.
- cobios_gen: `gba_recompile --bios bios.bin --config ../cobios.toml --out cobios_gen` (bios = pc-app gba_bios_open.bin).
- weblinkrt: emscripten runtime libs, CMAKE_CXX_FLAGS="-mtail-call -include compat.h -fwasm-exceptions",
  GBARECOMP_WEB_HOST=ON, GBARECOMP_GENERATED_BIOS_DIR=cobios_gen, GBARECOMP_NATIVE_RAM_CODE_VIEWS=ON.
  compat.h = ../../web/compat.h plus `#include <cstdlib>` (newer emsdk).
- rtmix: weblinkrt's libs with runtime.cpp.o rebuilt WITHOUT -fwasm-exceptions (same command otherwise, `emar r`).
  Reason: on the web the 1-player main loop outlives run_game()/main(); with wasm EH the 'unwind' that emscripten throws
  ran their destructors and the game froze at boot (PC 0x08000100). link_main's RunOptions is static for the same reason.
- emsdk latest: link flags need -sINCOMING_MODULE_JS_API=wasmBinary,noInitialRun,... and HEAPU8/HEAP16/HEAP32 in
  EXPORTED_RUNTIME_METHODS (see relink.sh).

Steps: grab the page ROM (the ROM the page writes to /data/game.gba), then `regen.sh <rom> <tag>`: first 16 MB as the
generation ROM, game-link.toml + orcslots/linkfuncs.py + turn16funcs.py, generate (8 shards), genpatch.py, compile, link
(shim-one.cpp = shim-web.cpp + CPU speed + VRAM/palette), split into 3 wasm parts.

1-player: link_main main() calls rotk_solo_setup() (mixer_hook.cpp) so the game's IWRAM mixer runs natively, then run_game.
Page patches: recomp/playroom/one-engine-v179.py, then p2-features-v179.py.

## v199 (2026-11-19): movement feel compiled in
regen.sh also runs ../feelfuncs.py, which adds tools/feel hero_feel (ROM 0x8A000, CPU 0x0808A000) as [[extra_func]].
The generation ROM must be the page ROM of a page with recomp/playroom/feel-v199.py applied (feel.bin at 0x8A000); dump
it from the running page (/data/game.gba, first 16 MB). Page engine key ?v=199. Without the compiled entry the link engine
stops with "unreachable" as soon as a hero runs the wrapper (v194). Build box rebuilt from scratch on 2026-11-19 with the
steps above (newest emsdk; rtmix = runtime.cpp.o rebuilt without -fwasm-exceptions + `emar r`). Built files:
/mnt/project-files/engine-build/feel-v199/.

## v236 (2026-11-21): faster Moria (engine speed)
Measured in Moria (level 82, headless Chromium with the CPU profiler on so the box is CPU bound like an iPhone):
the 320x240 wide compositor was ~40% of engine time and the 60 fps FrameSmoother (in-between pictures, odd steps drawn
twice and averaged) ~40% more; the game's own code is a few percent. -O2 instead of -O1 gave nothing measurable.
- ../engine-speed-v236.patch (apply last, `patch -p1` in gbarecomp): gba_ppu.cpp turns on the front-to-back ordered
  wide rows (hidden pixels skipped, whole tiles at a time) and adds a per-layer tile cache in the per-pixel BG loop
  (g_ws_tilemap_tile_invariant); render_scanline_wide has a verify mode (g_ws_ppu_verify) that draws every row both ways
  and counts differences. frame_smooth.h adds g_rotk_smooth_level: 2 full, 1 in-between pictures drawn once, 0 off.
- link_main.cpp install(): tile cache and ordered rows on (ROTK_TILE_CACHE=0 / ROTK_ORDERED=0 turn them off natively).
- shim-one.cpp: rotk_ppu_verify(on) -> rows*65536 + bad rows, rotk_smooth(level) (-1 reads). relink.sh exports both.
- Checked pixel-identical (verify mode, 0 bad rows) in Moria, Fangorn and Helm's Deep. ~15% less engine time per picture.
- Page: recomp/playroom/engine-v236.py (cache key ?v=236 and the smoothing step-down controller).
