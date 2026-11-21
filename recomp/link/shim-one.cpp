// One engine (2026-11-16, Jordan: "I just want one"): shim-web.cpp (2-player exports) + shim-skin.cpp extras
// (CPU speed, VRAM/palette for the skin pass), so the same build runs 1-player and P2 games.
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
extern "C" int g_link_turbo;
extern "C" EMSCRIPTEN_KEEPALIVE void rotk_link_turbo(int n) { g_link_turbo = n; }
// CPU speed (engine upgrade, 2026-11-10; needs gbarecomp-cpu-speed.patch): percent of the
// real GBA clock, 100-800. 300 keeps about 70 monsters on screen at full speed.
extern "C" void runtime_set_cpu_speed(unsigned pct);
extern "C" unsigned runtime_get_cpu_speed(void);
extern "C" EMSCRIPTEN_KEEPALIVE void rotk_cpu_speed(int pct) { runtime_set_cpu_speed(static_cast<unsigned>(pct)); }
extern "C" EMSCRIPTEN_KEEPALIVE int rotk_get_cpu_speed() { return static_cast<int>(runtime_get_cpu_speed()); }
// Skin (2026-11-10): read-only VRAM and palette for the page's tile matching.
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_vram() {
    const auto* b = gbarecomp::active_bus(); return b ? b->vram_ptr() : nullptr;
}
extern "C" EMSCRIPTEN_KEEPALIVE const unsigned char* rotk_pal() {
    const auto* b = gbarecomp::active_bus(); return b ? b->pal_ptr() : nullptr;
}
// Debug (one engine bring-up): guest PC and the runtime's frame count.
#include "runtime_arm.h"
extern "C" EMSCRIPTEN_KEEPALIVE unsigned rotk_dbg_pc() { return g_cpu.R[15]; }
// Engine speed test hook (2026-11-21): on = 1 draws every margin row twice (old and new path) and compares.
// Returns rows compared * 65536 + rows that differed (both capped).
extern "C" EMSCRIPTEN_KEEPALIVE unsigned rotk_ppu_verify(int on) {
    if (on >= 0) gba::g_ws_ppu_verify = on;
    const unsigned r = gba::g_ws_ppu_verify_rows < 65535u ? gba::g_ws_ppu_verify_rows : 65535u, b = gba::g_ws_ppu_verify_bad < 65535u ? gba::g_ws_ppu_verify_bad : 65535u;
    return r * 65536u + b;
}
#include "frame_smooth.h"
// Smoothing level (2026-11-21, see frame_smooth.h): 2 full, 1 no double-drawn odd steps, 0 off. -1 only reads it.
extern "C" EMSCRIPTEN_KEEPALIVE int rotk_smooth(int level) {
    if (level >= 0) gbarecomp::g_rotk_smooth_level = level > 2 ? 2 : level;
    return gbarecomp::g_rotk_smooth_level;
}
