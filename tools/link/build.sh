#!/bin/sh
# Builds link.js + link.wasm (two linked GBAs for the browser).
# Needs emscripten and a wasm build of libmgba 0.10 (see docs/findings.md, "Link play").
set -e
MGBA=${MGBA:-/tmp/mgba}
OUT=${1:-.}
emcc -O3 web.c "$MGBA/build-wasm/libmgba.a" -I"$MGBA/include" -I"$MGBA/build-wasm/include" \
  -DDISABLE_THREADING -D_GNU_SOURCE -DM_CORE_GBA \
  -s MODULARIZE=1 -s EXPORT_NAME=LinkGBA -s ALLOW_MEMORY_GROWTH=1 -s INITIAL_MEMORY=67108864 \
  -s ENVIRONMENT=web -s FILESYSTEM=0 \
  -s EXPORTED_RUNTIME_METHODS='["HEAPU8","HEAP16","HEAPU32"]' \
  -o "$OUT/link.js"
