set -e
cd /tmp/rc && python3 - <<'P'
r=bytearray(open('modded4.gba','rb').read())
assert r[0x2F88]==0x80 and r[0x2F90:0x2F9C]==bytes.fromhex("281c403000283edbff2d3cdc")
r[0x2F88]=0x84; r[0x2F90:0x2F9C]=bytes([0x28,0x1c,0x40,0x30,0x80,0x09,0x06,0x28,0x3d,0xd8,0xc0,0x46])
open('modded4-pc.gba','wb').write(r)
P
mkdir -p o4 && rm -f o4/dump.bin && ./runprof modded4-pc.gba s1.txt o4 > /dev/null
python3 - <<'P'
import hashlib
r=bytearray(open('/tmp/rc/modded4-pc.gba','rb').read()); d=open('/tmp/rc/o4/dump.bin','rb').read()
r[0xFFAAD0:0xFFAAD0+0x624]=d
open('/tmp/rc/modded4-pc-gen.gba','wb').write(r); sha=hashlib.sha1(r).hexdigest(); print('gen sha',sha)
t=open('/tmp/rc/gen2.toml').read().replace('5f5003391739b4a11695ffaeec41c85aa45fcf65',sha).replace('/tmp/rc/modded2-pc-gen.gba','/tmp/rc/modded4-pc-gen.gba')
open('/tmp/rc/gen4.toml','w').write(t)
P
rm -rf port4 && GBARECOMP_CORE=gbarecomp/build/gba_recompile python3 gbarecomp/tools/cli.py build --rom modded4-pc-gen.gba --output port4 --config gen4.toml --codegen-shards 8 > gen4.log 2>&1
rm -rf gen-solo4 && cp -r port4/generated gen-solo4 && python3 /tmp/rc/w8/recomp/orcslots/genpatch.py gen-solo4 /mnt/project-files/engine-build/arrows-sized/orcslots.sym | tail -3
G=/tmp/rc/gbarecomp; mkdir -p /tmp/rc/solo4 && cd /tmp/rc/solo4
FL="-std=c++20 -mtail-call -include /tmp/rc/emcompat/compat.h -I$G/src/armv4t -I$G/src/gba -I$G/src/runtime -I$G/src/debug -I$G/external/arm-recomp-core/profiles/armv4t_gba"
ls /tmp/rc/gen-solo4/*.cpp | xargs -P4 -I{} sh -c "em++ $FL -O1 -c {} -o \$(basename {} .cpp).o"
cp /tmp/rc/solo2/main.o /tmp/rc/solo2/shim-skin.o .
L=/tmp/rc/webrt
em++ -O2 -mtail-call main.o shim-skin.o recompiled_*.o dispatch_table.o symbol_map.o -Wl,--start-group $L/libgbarecomp_runtime.a $L/libgbarecomp_debug.a $L/libgbarecomp_gba.a $L/libgbarecomp_armv4t.a $L/libgbarecomp_recompile_core.a $L/libgbarecomp_heal_gate.a -Wl,--end-group -sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=134217728 -sTOTAL_STACK=16777216 -sFORCE_FILESYSTEM -sEXPORTED_RUNTIME_METHODS=FS,ENV,addRunDependency,removeRunDependency -sINVOKE_RUN=0 -sEXPORTED_FUNCTIONS=_rotk_main,_rotk_pause,_rotk_iwram,_rotk_ewram,_rotk_native_view,_rotk_oam,_rotk_tick_stats,_rotk_bg_tick,_rotk_cpu_speed,_rotk_get_cpu_speed,_rotk_skin,_rotk_skin_slot,_rotk_vram,_rotk_pal,_malloc,_free -lidbfs.js -sENVIRONMENT=web -sEXIT_RUNTIME=1 -sMODULARIZE=1 -sEXPORT_NAME=createRotk -o rotk.js 2>&1 | grep -i error || true
ls -la rotk.*
