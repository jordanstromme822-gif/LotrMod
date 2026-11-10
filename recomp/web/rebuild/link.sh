set -e
cd /tmp/rc
G=/tmp/rc/gbarecomp; W=/tmp/rc/w8/recomp
# 1 recompiled Cult-of-GBA BIOS
mkdir -p cobios_gen && gbarecomp/build/gba_recompile --bios bios.bin --config $W/link/cobios.toml --out cobios_gen > cobios.log 2>&1
ls cobios_gen
# 2 runtime with wasm exceptions + that BIOS
if [ ! -f weblinkrt/build.ninja ]; then
  emcmake cmake -S $G -B weblinkrt -G Ninja -DCMAKE_BUILD_TYPE=Release -DGBARECOMP_WEB_HOST=ON \
    -DCMAKE_CXX_FLAGS="-mtail-call -include /tmp/rc/emcompat/compat.h -fwasm-exceptions" \
    -DGBARECOMP_GENERATED_BIOS_DIR=/tmp/rc/cobios_gen > weblinkrt.cfg.log 2>&1
fi
cd weblinkrt && ninja gbarecomp_runtime gbarecomp_debug gbarecomp_gba gbarecomp_armv4t gbarecomp_recompile_core gbarecomp_heal_gate > ../weblinkrt.build.log 2>&1; cd ..
# 3 game-link toml for the arrows-sized ROM
python3 - <<'P'
import hashlib
r=open('/tmp/rc/modded4-pc.gba','rb').read(); sha=hashlib.sha1(r).hexdigest()
t=open('/tmp/rc/w8/recomp/link/game-link.toml').read().replace('dd6d504c587ce487c983968f4f01748457b30ed8',sha)
t=t.replace('path = "bios.bin"','path = "/tmp/rc/bios.bin"').replace('path = "game.gba"','path = "/tmp/rc/modded4-pc.gba"')
open('/tmp/rc/game-link4.toml','w').write(t); print('link rom sha',sha)
P
python3 $W/orcslots/linkfuncs.py /mnt/project-files/engine-build/arrows-sized/orcslots.sym /tmp/rc/game-link4.toml
rm -rf portlink4 && GBARECOMP_CORE=gbarecomp/build/gba_recompile python3 gbarecomp/tools/cli.py build --rom modded4-pc.gba --output portlink4 --config game-link4.toml --codegen-shards 8 > genlink4.log 2>&1
rm -rf gen-link4 && cp -r portlink4/generated gen-link4 && python3 $W/orcslots/genpatch.py gen-link4 /mnt/project-files/engine-build/arrows-sized/orcslots.sym | tail -2
# 4 compile + link
mkdir -p /tmp/rc/link4 && cd /tmp/rc/link4
FL="-std=c++20 -mtail-call -include /tmp/rc/emcompat/compat.h -I$G/src/armv4t -I$G/src/gba -I$G/src/runtime -I$G/src/debug -I$G/external/arm-recomp-core/profiles/armv4t_gba"
ls /tmp/rc/gen-link4/*.cpp | xargs -P4 -I{} sh -c "em++ $FL -O1 -g0 -c {} -o \$(basename {} .cpp).o"
for f in $W/link/link_main.cpp $W/link/mixer_hook.cpp $W/link/shim-web.cpp; do em++ $FL -fwasm-exceptions -O2 -c $f -o $(basename $f .cpp).o; done
RT=/tmp/rc/weblinkrt
em++ -O2 -mtail-call -fwasm-exceptions link_main.o shim-web.o mixer_hook.o recompiled_*.o dispatch_table.o symbol_map.o \
  -Wl,--start-group $RT/libgbarecomp_runtime.a $RT/libgbarecomp_debug.a $RT/libgbarecomp_gba.a $RT/libgbarecomp_armv4t.a $RT/libgbarecomp_recompile_core.a $RT/libgbarecomp_heal_gate.a -Wl,--end-group \
  -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=134217728 -sTOTAL_STACK=16777216 -sFORCE_FILESYSTEM \
  -sEXPORTED_RUNTIME_METHODS=FS,ENV,addRunDependency,removeRunDependency -sINVOKE_RUN=0 \
  -sEXPORTED_FUNCTIONS=_rotk_main,_rotk_pause,_rotk_iwram,_rotk_ewram,_rotk_native_view,_rotk_oam,_rotk_tick_stats,_rotk_bg_tick,_malloc,_free,_rotk_link_p2,_rotk_link_on,_rotk_link_frames,_rotk_link_iwram,_rotk_link_ewram,_rotk_link_save,_rotk_link_level,_rotk_link_turbo,_rotk_link_push,_rotk_link_queued,_rotk_link_hash \
  -lidbfs.js -sENVIRONMENT=web -sEXIT_RUNTIME=1 -sMODULARIZE=1 -sEXPORT_NAME=createRotkLink -o rotk-link.js 2>&1 | grep -i "error" || true
ls -la rotk-link.*
