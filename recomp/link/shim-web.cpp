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
// In 2-player (P2 partner) mode these read the shown game (machine 0).
extern "C" int g_link_on;
extern "C" const unsigned char* rotk_link_iwram(int);
extern "C" const unsigned char* rotk_link_ewram(int);
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_iwram() {
    if (g_link_on) return rotk_link_iwram(0);
    auto* b = gbarecomp::active_bus(); return b ? b->iwram_ptr() : nullptr;
}
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_ewram() {
    if (g_link_on) return rotk_link_ewram(0);
    auto* b = gbarecomp::active_bus(); return b ? b->ewram_ptr() : nullptr;
}
extern "C" unsigned g_link_p2_keys;
extern "C" unsigned g_link_frames;
extern "C" EMSCRIPTEN_KEEPALIVE void rotk_link_p2(unsigned keys) { g_link_p2_keys = keys & 0x3ff; }
extern "C" EMSCRIPTEN_KEEPALIVE int rotk_link_on() { return g_link_on; }
extern "C" EMSCRIPTEN_KEEPALIVE unsigned rotk_link_frames() { return g_link_frames; }
#include "gba_ppu.h"
extern "C" EMSCRIPTEN_KEEPALIVE int rotk_native_view() { return gba::g_ws_pillarbox ? 1 : 0; }
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_oam() {
    if (g_link_on) return nullptr;
    auto* b = gbarecomp::active_bus(); return b ? b->oam_ptr() : nullptr;
}
extern "C" int g_web_tick_stats[5];
extern "C" EMSCRIPTEN_KEEPALIVE const int* rotk_tick_stats() { return g_web_tick_stats; }
