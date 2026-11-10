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
