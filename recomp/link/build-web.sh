#!/bin/bash
# Web build of the 2-player engine (Play Room wide/rotk-link.js + rotk-link-0/1.wasm, game-link.txt).
# Runtime: gbarecomp with gbarecomp-link.patch, configured for emscripten with
#   CMAKE_CXX_FLAGS="-include compat.h -fwasm-exceptions" GBARECOMP_GENERATED_BIOS_DIR=<recompiled cobios>
# Game code: gba_recompile --config game-link.toml --codegen-shards 8 --out gen
set -e
G=${G:-/tmp/rc/gbarecomp}; RT=${RT:-/tmp/rc/webrt}; GEN=${GEN:-/tmp/rc/mp/gen}; SRC=$(dirname "$0")
FL="-std=c++20 -mtail-call -include ../web/compat.h -I$G/src/armv4t -I$G/src/gba -I$G/src/runtime -I$G/src/debug -I$G/external/arm-recomp-core/profiles/armv4t_gba"
for f in $GEN/*.cpp; do em++ $FL -O1 -g0 -c $f -o $(basename $f .cpp).o; done
for f in $SRC/link_main.cpp $SRC/mixer_hook.cpp $SRC/shim-web.cpp; do em++ $FL -fwasm-exceptions -O2 -c $f -o $(basename $f .cpp).o; done
em++ -O2 -mtail-call -fwasm-exceptions link_main.o shim-web.o mixer_hook.o recompiled_*.o dispatch_table.o symbol_map.o \
  -Wl,--start-group $RT/libgbarecomp_runtime.a $RT/libgbarecomp_debug.a $RT/libgbarecomp_gba.a $RT/libgbarecomp_armv4t.a $RT/libgbarecomp_recompile_core.a $RT/libgbarecomp_heal_gate.a -Wl,--end-group \
  -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=134217728 -sTOTAL_STACK=16777216 -sFORCE_FILESYSTEM \
  -sEXPORTED_RUNTIME_METHODS=FS,ENV,addRunDependency,removeRunDependency -sINVOKE_RUN=0 \
  -sEXPORTED_FUNCTIONS=_rotk_main,_rotk_pause,_rotk_iwram,_rotk_ewram,_rotk_native_view,_rotk_oam,_rotk_tick_stats,_rotk_bg_tick,_malloc,_free,_rotk_link_p2,_rotk_link_on,_rotk_link_frames,_rotk_link_iwram,_rotk_link_ewram,_rotk_link_save,_rotk_link_level \
  -lidbfs.js -sENVIRONMENT=web -sEXIT_RUNTIME=1 -sMODULARIZE=1 -sEXPORT_NAME=createRotk -o rotk-link.js
# The page loads the wasm as two halves (artifact file size limit).
python3 -c "d=open('rotk-link.wasm','rb').read(); h=len(d)//2; open('rotk-link-0.wasm','wb').write(d[:h]); open('rotk-link-1.wasm','wb').write(d[h:])"
