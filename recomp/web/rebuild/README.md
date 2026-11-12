# Rebuilding the Play Room engines (solo Wide + 2-player link)

Reference scripts used for the arrows-99 and arrows-sized rebuilds (2026-11-10). Paths are the cloud build box's
(/tmp/rc: gbarecomp checkout with pc-and-web, smooth-v87, link, engine-speed, cpu-speed, obj-ext, oam-ext and skin
patches; emsdk; webrt / weblinkrt runtime builds; runprof mGBA profiler for the mixer dump).

1. `all.sh`: buildrom.js (from the arrows thread's engine-build folder) turns the original ROM into the page ROM.
2. `solo.sh`: PC cull patch at 0x2F88/0x2F90, mixer code dumped at 0x03000B38 (0x624 bytes) and spliced at ROM
   0xFFAAD0, generation toml with that ROM's sha, gbarecomp build (8 shards), orcslots genpatch.py, em++ compile and link.
3. `link.sh`: Cult-of-GBA BIOS recompiled, runtime with -fwasm-exceptions, game-link.toml extra_funcs rewritten by
   linkfuncs.py, gbarecomp build, genpatch.py, link_main/mixer_hook/shim-web, EXPORT_NAME createRotkLink.

The engines are built from the game ROM, so they are not committed; they go to the private project files
(engine-build/web-*) and the Play Room.

## v169 solo engine (Backpack page 2, 2026-11-11)
`solo-v169.sh` = the build used for the web-backpack2 engine. Runtime tree (gbarecomp base 351572f) patched in this order:
pc-and-web, smooth-v87 (`git apply -p4`), link/gbarecomp-link.patch, link/engine-speed-v116.patch, cpu-speed (`patch -F3`, it
overlaps the link patch), obj-ext, oam-ext, then `tools/skin/apply_skin_ppu.py src/gba/gba_ppu.cpp` plus only the
host_window_web.cpp part of gbarecomp-skin.patch, and the `rotk_bg_tick` line in runtime.cpp (see recomp/README.md).
Runtime libs: `emcmake cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DGBARECOMP_WEB_HOST=ON -DCMAKE_CXX_FLAGS="-mtail-call -include compat.h"`
(emsdk 3.1.6, compat.h = recomp/web/compat.h). main.o = recomp/main-modded.cpp, shim-skin.o = recomp/web/shim-skin.cpp (-O2).
The 2-player engine was NOT rebuilt: the page gives it a ROM with the old slot code (recomp/playroom/backpack-page2-v169.py).

## Backpack step 1 solo engine (2026-11-12)
`solo-backpack-step1.sh` = solo-v169.sh with gen7: gen ROM = the step-1 page ROM (live v171 page + pagejs + backpack-step1.py)
plus the PC cull bytes (0x2F88, 20 bytes) and the mixer dump (0xFFAAD0, 0x624 bytes) copied from modded6-pc-gen.gba. Same runtime.
