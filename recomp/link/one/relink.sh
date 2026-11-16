set -e
source /tmp/rc/b2/emsdk/emsdk_env.sh >/dev/null 2>&1
G=/tmp/rc/b2/gbarecomp; W=/home/user/lotrmod/recomp; O=${O:-/tmp/rc/b2/one178}; cd $O
FL="-std=c++20 -mtail-call -include /tmp/rc/b2/emcompat/compat.h -DGBARECOMP_NATIVE_RAM_CODE_VIEWS=1 -I$G/src/armv4t -I$G/src/gba -I$G/src/runtime -I$G/src/debug -I$G/external/arm-recomp-core/profiles/armv4t_gba"
for f in $W/link/link_main.cpp $W/link/mixer_hook.cpp $W/link/shim-one.cpp; do em++ $FL -fwasm-exceptions -O2 -c $f -o $(basename $f .cpp).o; done
RT=${RT:-/tmp/rc/b2/rtmix}
em++ -O2 -mtail-call -fwasm-exceptions link_main.o shim-one.o mixer_hook.o recompiled_*.o dispatch_table.o symbol_map.o \
  -Wl,--start-group $RT/libgbarecomp_runtime.a $RT/libgbarecomp_debug.a $RT/libgbarecomp_gba.a $RT/libgbarecomp_armv4t.a $RT/libgbarecomp_recompile_core.a $RT/libgbarecomp_heal_gate.a -Wl,--end-group \
  -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=134217728 -sSTACK_SIZE=16777216 -sFORCE_FILESYSTEM \
  -sEXPORTED_RUNTIME_METHODS=FS,ENV,addRunDependency,removeRunDependency,HEAPU8,HEAP16,HEAP32,HEAPU16,HEAPU32 -sINVOKE_RUN=0 \
  -sINCOMING_MODULE_JS_API=wasmBinary,noInitialRun,onAbort,preRun,postRun,print,printErr,locateFile,instantiateWasm,onRuntimeInitialized,onExit,arguments,thisProgram,noExitRuntime,preInit,monitorRunDependencies,setStatus,canvas \
  -sEXPORTED_FUNCTIONS=_rotk_main,_rotk_pause,_rotk_iwram,_rotk_ewram,_rotk_native_view,_rotk_oam,_rotk_tick_stats,_rotk_bg_tick,_rotk_cpu_speed,_rotk_get_cpu_speed,_rotk_skin,_rotk_skin_slot,_rotk_vram,_rotk_pal,_malloc,_free,_rotk_link_p2,_rotk_link_on,_rotk_link_frames,_rotk_link_iwram,_rotk_link_ewram,_rotk_link_save,_rotk_link_level,_rotk_link_turbo,_rotk_link_push,_rotk_link_queued,_rotk_link_hash,_rotk_link_op,_rotk_link_outbox,_rotk_dbg_pc \
  -lidbfs.js -sENVIRONMENT=web -sEXIT_RUNTIME=1 -sMODULARIZE=1 -sEXPORT_NAME=createRotkLink -o rotk-link.js
python3 -c "
d=open('rotk-link.wasm','rb').read(); n=3; h=-(-len(d)//n)
[open('rotk-link-%d.wasm'%i,'wb').write(d[i*h:(i+1)*h]) for i in range(n)]; print(len(d))"
cp rotk-link.js rotk-link-?.wasm /tmp/rc/site6/wide/
