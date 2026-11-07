#!/bin/bash
G=/tmp/rc/gbarecomp
FL="-std=c++20 -mtail-call -include /tmp/rc/emcompat/compat.h -I$G/src/armv4t -I$G/src/gba -I$G/src/runtime -I$G/src/debug -I$G/external/arm-recomp-core/profiles/armv4t_gba"
ls /tmp/rc/pcgame2/generated/*.cpp | xargs -P4 -I{} sh -c 'f={}; b=$(basename $f .cpp); em++ '"$FL"' -O1 -g0 -c $f -o $b.o 2>$b.err || echo FAIL $b'
echo done
