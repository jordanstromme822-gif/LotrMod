set -e
source /tmp/rc/b2/emsdk/emsdk_env.sh >/dev/null 2>&1
G=/tmp/rc/b2/gbarecomp; cd $O
FL="-std=c++20 -mtail-call -include /tmp/rc/b2/emcompat/compat.h -DGBARECOMP_NATIVE_RAM_CODE_VIEWS=1 -I$G/src/armv4t -I$G/src/gba -I$G/src/runtime -I$G/src/debug -I$G/external/arm-recomp-core/profiles/armv4t_gba"
ls $GEN/*.cpp | xargs -P4 -I{} sh -c "em++ $FL -O1 -g0 -c {} -o \$(basename {} .cpp).o"
