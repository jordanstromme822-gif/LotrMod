#include "runtime.h"
#include "runtime_arm.h"
#include "runtime_bus_bridge.h"
#include "gba_bus.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
// Stress-test main: ROTK_POKES="vblank:addr:value;..." (hex addr/value, 32-bit), ROTK_REPORT="v1,v2,..."
// prints game-frame counter 0x030041A4 and object count at those VBlanks.
extern "C" void (*g_rotk_test_vblank)(void);
struct P { long v; unsigned a, x; };
static std::vector<P> pokes; static std::vector<long> reps; static long vb = 0;
static unsigned r32(gba::GbaBus* b, unsigned a) {
    const unsigned char* m = a >> 24 == 2 ? b->ewram_ptr() + (a - 0x02000000) : b->iwram_ptr() + (a - 0x03000000);
    unsigned v; std::memcpy(&v, m, 4); return v;
}
static void w32(gba::GbaBus* b, unsigned a, unsigned x) {
    unsigned char* m = a >> 24 == 2 ? b->ewram_ptr() + (a - 0x02000000) : b->iwram_ptr() + (a - 0x03000000);
    std::memcpy(m, &x, 4);
}
static void tick() {
    ++vb; auto* b = gbarecomp::active_bus(); if (!b) return;
    for (auto& p : pokes) if (p.v == vb) w32(b, p.a, p.x);
    if (std::getenv("ROTK_GOD")) { unsigned h = r32(b, 0x03003C00); if (h >> 24 == 2) { unsigned char* m = b->ewram_ptr() + (h - 0x02000000) + 0x5A; m[0] = 0x2C; m[1] = 0x01; } }
    for (long r : reps) if (r == vb) {
        int n = 0; unsigned o = r32(b, 0x03002420);
        while (o && n < 400) { ++n; o = r32(b, o); }
        std::printf("REPORT vblank=%ld gameframes=%u level=%u objects=%d spawned=%u\n", vb, r32(b, 0x030041A4),
                    r32(b, 0x03004174) & 0xff, n, r32(b, 0x0203FF0C));
        std::fflush(stdout);
    }
}
int main(int argc, char** argv) {
    if (const char* s = std::getenv("ROTK_POKES")) {
        const char* q = s; P p;
        while (std::sscanf(q, "%ld:%x:%x", &p.v, &p.a, &p.x) == 3) { pokes.push_back(p); q = std::strchr(q, ';'); if (!q) break; ++q; }
    }
    if (const char* s = std::getenv("ROTK_REPORT")) {
        const char* q = s; long v;
        while (std::sscanf(q, "%ld", &v) == 1) { reps.push_back(v); q = std::strchr(q, ','); if (!q) break; ++q; }
    }
    g_rotk_test_vblank = tick;
    gbarecomp::RunOptions opts;
    opts.builtin_game_name = "The Lord of the Rings: The Return of the King (USA, Europe)";
    opts.builtin_rom_sha1 = "428e21fbe621ae78ce654c7688eec4dff796f261";
    return gbarecomp::run_game(argc, argv, opts);
}
