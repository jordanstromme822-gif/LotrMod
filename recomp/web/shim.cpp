#include <emscripten.h>
int main(int argc, char** argv);
extern "C" EMSCRIPTEN_KEEPALIVE int rotk_main() {
    static char a0[] = "rotk", a1[] = "--config", a2[] = "/data/game.toml", a3[] = "--window";
    static char* argv[] = {a0, a1, a2, a3, nullptr};
    return main(4, argv);
}
extern "C" int g_web_paused;
extern "C" EMSCRIPTEN_KEEPALIVE void rotk_pause(int p) { g_web_paused = p; }
#include "runtime_bus_bridge.h"
#include "gba_bus.h"
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_iwram() {
    auto* b = gbarecomp::active_bus(); return b ? b->iwram_ptr() : nullptr;
}
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_ewram() {
    auto* b = gbarecomp::active_bus(); return b ? b->ewram_ptr() : nullptr;
}
#include "gba_ppu.h"
extern "C" EMSCRIPTEN_KEEPALIVE int rotk_native_view() { return gba::g_ws_pillarbox ? 1 : 0; }
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_oam() {
    auto* b = gbarecomp::active_bus(); return b ? b->oam_ptr() : nullptr;
}
extern "C" int g_web_tick_stats[5];
extern "C" EMSCRIPTEN_KEEPALIVE const int* rotk_tick_stats() { return g_web_tick_stats; }
