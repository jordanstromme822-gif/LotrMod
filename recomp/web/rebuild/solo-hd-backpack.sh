set -e
cd /tmp/rc
rm -rf port8 && GBARECOMP_CORE=gbarecomp/build/gba_recompile python3 gbarecomp/tools/cli.py build --rom modded8-pc-gen.gba --output port8 --config gen8.toml --codegen-shards 8 > gen8.log 2>&1
rm -rf gen-solo8 && cp -r port8/generated gen-solo8 && python3 /home/user/lotrmod/recomp/orcslots/genpatch.py gen-solo8 /home/user/lotrmod/tools/orcslots/orcslots.sym | tail -2
source /tmp/rc/emsdk/emsdk_env.sh >/dev/null 2>&1
G=/tmp/rc/gbarecomp; mkdir -p /tmp/rc/solo8 && cd /tmp/rc/solo8 && rm -f *.o && cp /tmp/rc/solo5/main.o /tmp/rc/solo5/shim-skin.o .
FL="-std=c++20 -mtail-call -include /tmp/rc/emcompat/compat.h -I$G/src/armv4t -I$G/src/gba -I$G/src/runtime -I$G/src/debug -I$G/external/arm-recomp-core/profiles/armv4t_gba"
ls /tmp/rc/gen-solo8/*.cpp | xargs -P4 -I{} sh -c "em++ $FL -O1 -c {} -o \$(basename {} .cpp).o"
L=/tmp/rc/webrt-b
em++ -O2 -mtail-call main.o shim-skin.o recompiled_*.o dispatch_table.o symbol_map.o -Wl,--start-group $L/libgbarecomp_runtime.a $L/libgbarecomp_debug.a $L/libgbarecomp_gba.a $L/libgbarecomp_armv4t.a $L/libgbarecomp_recompile_core.a $L/libgbarecomp_heal_gate.a -Wl,--end-group -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=134217728 -sTOTAL_STACK=16777216 -sFORCE_FILESYSTEM -sEXPORTED_RUNTIME_METHODS=FS,ENV,addRunDependency,removeRunDependency -sINVOKE_RUN=0 -sEXPORTED_FUNCTIONS=_rotk_main,_rotk_pause,_rotk_iwram,_rotk_ewram,_rotk_native_view,_rotk_oam,_rotk_tick_stats,_rotk_bg_tick,_rotk_cpu_speed,_rotk_get_cpu_speed,_rotk_skin,_rotk_skin_slot,_rotk_vram,_rotk_pal,_malloc,_free -lidbfs.js -sENVIRONMENT=web -sEXIT_RUNTIME=1 -sMODULARIZE=1 -sEXPORT_NAME=createRotk -o rotk.js
python3 -c "
d=open('rotk.wasm','rb').read(); h=(len(d)+1)//2
open('rotk-0.wasm','wb').write(d[:h]); open('rotk-1.wasm','wb').write(d[h:]); print(len(d))"
echo SOLO8 DONE
