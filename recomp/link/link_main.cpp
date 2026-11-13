#if defined(__EMSCRIPTEN__) && !defined(ROTK_NODE_BENCH)
#define GBR_WEB_SINGLE 1
#endif
#include "runtime.h"
#include "runtime_arm.h"
#include "runtime_bus_bridge.h"
#include "gba_bus.h"
#include "gba_ppu.h"
#include "view_config.h"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>

// Zoomed-out view for Return of the King (2026-11-07).
//
// The game keeps only a 31x21-tile window of each world layer in VRAM, rebuilt
// from the level's block map whenever the camera crosses a tile. For a wider
// picture, the margins are drawn straight from that same block map:
//   block map:  u16 block index per 32x32 px cell, W cells per row
//               layer A at *0x03005FB4, layer B at *0x0300586C, W = u16 0x03005878
//   block set:  16 tile entries (4x4) per block, A at *0x03005FBC, B at *0x03005FC0
// Each frame the VRAM window of BG2 (foreground) and BG3 (ground) is matched
// against the block map to find which layer it shows and where its top-left
// tile sits in the level; only a verified match draws margins. BG1 (sky) is a
// repeating pattern and simply keeps wrapping; BG0 (HUD) stays native.
// Anything else (menus, maps, cutscenes) shows black side bars.
#if defined(ROTK_OLD_RUNTIME)   // speed comparison against a runtime without the repeat-frame skip
namespace gba { extern "C" { int g_ppu_repeat_skip = 0; unsigned g_ppu_view_sig = 0; } }
#else
namespace gba { extern "C" int g_ppu_repeat_skip; extern "C" unsigned g_ppu_view_sig; }
#endif
namespace rotk_view {

struct Layer {
    bool ok = false;
    std::uint32_t map = 0, set = 0;  // EWRAM offsets
    int ox = 0, oy = 0;              // level tile at VRAM map (0,0)
};

Layer layers[4];
int W = 0, H = 0;
bool ready = false;
bool enabled = false;
const std::uint8_t* ewram = nullptr;
const std::uint8_t* iwram = nullptr;
gba::GbaBus* bus = nullptr;
int last_status = -1;
std::uint64_t memo_gen = 0;  // bumped whenever the block map may have changed

inline std::uint32_t rd32(const std::uint8_t* m, std::uint32_t o) {
    return m[o] | (m[o + 1] << 8) | (m[o + 2] << 16) | (std::uint32_t(m[o + 3]) << 24);
}
inline std::uint16_t rd16(const std::uint8_t* m, std::uint32_t o) {
    return static_cast<std::uint16_t>(m[o] | (m[o + 1] << 8));
}
inline bool ewram_ptr_ok(std::uint32_t p, std::uint32_t len) {
    return p >= 0x02000000u && p + len <= 0x02040000u;
}

// Tile entry of level layer (map,set) at level tile (tx,ty); false if outside.
inline bool level_entry(std::uint32_t map, std::uint32_t set, int tx, int ty, std::uint16_t* out) {
    if (tx < 0 || ty < 0) return false;
    const int bx = tx >> 2, by = ty >> 2;
    if (bx >= W || by >= H) return false;
    const std::uint32_t mo = map + static_cast<std::uint32_t>(by * W + bx) * 2u;
    if (mo + 2 > 0x40000u) return false;
    const std::uint16_t block = rd16(ewram, mo);
    const std::uint32_t so = set + static_cast<std::uint32_t>(block) * 32u +
                             static_cast<std::uint32_t>((ty & 3) * 8 + (tx & 3) * 2);
    if (so + 2 > 0x40000u) return false;
    *out = rd16(ewram, so);
    return true;
}

void prepare(const std::uint8_t* io) {
    ++memo_gen;
    ready = false;
    for (auto& l : layers) l.ok = false;
    bus = gbarecomp::active_bus();
    if (!bus || !io) return;
    ewram = bus->ewram_ptr();
    iwram = bus->iwram_ptr();
    const std::uint8_t* vram = bus->vram_read_view().data();
    if (rd32(iwram, 0x41B0) != 1) return;  // not in a level
    W = rd16(iwram, 0x5878);
    if (W <= 0 || W > 256) return;
    const std::uint32_t mapA = rd32(iwram, 0x5FB4), mapB = rd32(iwram, 0x586C);
    const std::uint32_t setA = rd32(iwram, 0x5FBC), setB = rd32(iwram, 0x5FC0);
    if (!ewram_ptr_ok(mapA, 2) || !ewram_ptr_ok(mapB, 2) || !ewram_ptr_ok(setA, 32) || !ewram_ptr_ok(setB, 32)) return;
    H = 0x2800 / (2 * W);
    const int camx = static_cast<int>(rd32(iwram, 0x5880)), camy = static_cast<int>(rd32(iwram, 0x5884));
    const std::uint32_t maps[2] = {mapA - 0x02000000u, mapB - 0x02000000u};
    const std::uint32_t sets[2] = {setA - 0x02000000u, setB - 0x02000000u};
    const std::uint16_t dispcnt = rd16(io, 0);
    for (int bg = 2; bg < 4; ++bg) {
        if (!(dispcnt & (0x100 << bg))) continue;
        const std::uint16_t cnt = rd16(io, 0x08 + bg * 2);
        if (cnt >> 14) continue;  // expect a 256x256 map
        const std::uint32_t sb = ((cnt >> 8) & 31u) * 0x800u;
        int best = -1, best_l = 0, best_x = 0, best_y = 0;
        for (int l = 0; l < 2; ++l) {
            for (int dy = -3; dy <= 3; ++dy) {
                for (int dx = -3; dx <= 3; ++dx) {
                    const int ox = (camx >> 3) + dx, oy = (camy >> 3) + dy;
                    int match = 0, total = 0;
                    for (int row = 0; row < 21; row += 2) {
                        for (int col = 0; col < 31; col += 2) {
                            std::uint16_t e;
                            const std::uint16_t hw = rd16(vram, sb + static_cast<std::uint32_t>(row * 32 + col) * 2u);
                            ++total;
                            if (level_entry(maps[l], sets[l], ox + col, oy + row, &e) && e == hw) ++match;
                        }
                    }
                    if (match * 100 >= total * 95 && match > best) {
                        best = match; best_l = l; best_x = ox; best_y = oy;
                    }
                }
            }
        }
        if (best >= 0) {
            layers[bg].ok = true;
            layers[bg].map = maps[best_l];
            layers[bg].set = sets[best_l];
            layers[bg].ox = best_x;
            layers[bg].oy = best_y;
        }
    }
    ready = layers[3].ok;
}

int tile_provider(int bg, int x, int y, std::uint16_t* entry) {
    if (!ready) return gba::kWsTilemapUnavailable;
    if (bg == 1) return gba::kWsTilemapKeepWrapped;  // sky repeats
    if (bg < 2 || !layers[bg].ok) return gba::kWsTilemapUnavailable;
    int hofs, vofs;
    if (gba::g_ws_margin_scroll_override_on) {
        hofs = gba::g_ws_margin_scroll_override[bg][0];
        vofs = gba::g_ws_margin_scroll_override[bg][1];
    } else {
        const std::uint8_t* io = gba::g_ws_render_io ? gba::g_ws_render_io : bus->io().raw();
        hofs = rd16(io, 0x10 + bg * 4) & 511;
        vofs = rd16(io, 0x12 + bg * 4) & 511;
    }
    const int px = x + hofs, py = y + vofs;
    const int tx = layers[bg].ox + (px >= 0 ? px >> 3 : -((7 - px) >> 3));
    const int ty = layers[bg].oy + (py >= 0 ? py >> 3 : -((7 - py) >> 3));
    // Neighbouring pixels share a tile: remember the last answer per layer.
    struct Memo { std::uint64_t gen = ~0ull; int tx = 0, ty = 0; std::uint32_t map = 0, set = 0; bool ok = false; std::uint16_t e = 0; };
    static Memo memo[4];
    Memo& m = memo[bg];
    if (m.gen == memo_gen && m.tx == tx && m.ty == ty && m.map == layers[bg].map && m.set == layers[bg].set) {
        if (m.ok) *entry = m.e;
        return m.ok ? gba::kWsTilemapReplace : gba::kWsTilemapUnavailable;
    }
    std::uint16_t e = 0;
    const bool ok = level_entry(layers[bg].map, layers[bg].set, tx, ty, &e);
    m = {memo_gen, tx, ty, layers[bg].map, layers[bg].set, ok, e};
    if (ok) *entry = e;
    return ok ? gba::kWsTilemapReplace : gba::kWsTilemapUnavailable;
}

// The PC build lets the game place sprite pieces up to x=383 (ROM patch at
// 0x08002F90); raw 240..383 is the right margin, everything else keeps the
// hardware's signed meaning.
int obj_x_provider(int raw_x, int* out_x) {
    if (ready && raw_x >= 240 && raw_x < 384) { *out_x = raw_x; return 1; }
    return 0;
}

// 4:3 view (Jordan, 2026-11-07): 320x240, 40 px above and below the native
// picture. The PC ROM also lets sprite pieces reach y=200 (0x08002F88), so raw
// y 160..200 is the bottom margin and 201..255 the top one.
constexpr int kExtraY = 40;
int obj_y_provider(int, std::uint16_t attr0, std::uint16_t, std::uint16_t, int* out_y) {
    if (!ready) return 0;
    const int raw = attr0 & 0xFF;
    *out_y = raw <= 200 ? raw : raw - 256;
    return 1;
}

// The HUD (BG0 rows 120..159) moves down to the bottom of the taller picture.
int hud_provider(int bg, int x, int y, int* sx, int* sy) {
    if (bg != 0 || !ready) return 0;
    if (y >= 160) {
        if (x < 0 || x >= 240 || y - kExtraY < 120) return -1;
        *sx = x; *sy = y - kExtraY;
        return 1;
    }
    if (y >= 120) return -1;
    return 0;
}

void geometry(gbarecomp::ViewGeometry* g, int, int) {
    if (!g || g->width <= 240) return;
    g->height = 160 + 2 * kExtraY;
    g->extra_top = g->extra_bottom = kExtraY;
}

void install(std::uint32_t, std::uint32_t) {
    enabled = true;
    gba::g_ws_tilemap_provider = tile_provider;
    gba::g_ws_authored_margin_layers = 1;
    gba::g_ws_obj_native_clip = 0;
    gba::g_ws_obj_x_provider = obj_x_provider;
    gba::g_ws_obj_attr_y_provider = obj_y_provider;
    gba::g_ws_bg_xy_provider = hud_provider;
    gba::g_ws_bg_xy_provider_layers = 1;
    gba::g_ws_pillarbox = 1;
}

void frame(const gbarecomp::ExtendedViewFrameInfo* f) {
    if (!enabled || !f) return;
    prepare(f->io);
    // Steady view (phone report 2026-11-07: shop screen kept changing size and the edges flickered). The block-map
    // match can drop out for a frame or two over menus drawn on top of a level; keep the last good match (moved with
    // the camera) for up to 30 frames, and only switch to the wide view after 10 good frames in a row.
    static Layer last[4];
    static int good = 0, bad = 0, last_cx = 0, last_cy = 0;
    static bool shown = false;
    const bool in_level = iwram && rd32(iwram, 0x41B0) == 1;
    const int cx = iwram ? static_cast<int>(rd32(iwram, 0x5880)) >> 3 : 0;
    const int cy = iwram ? static_cast<int>(rd32(iwram, 0x5884)) >> 3 : 0;
    if (ready) {
        ++good; bad = 0;
        for (int i = 0; i < 4; ++i) last[i] = layers[i];
        last_cx = cx; last_cy = cy;
        if (!shown && good >= 10) shown = true;
        if (!shown) ready = false;
    } else {
        good = 0; ++bad;
        if (shown && in_level && bad <= 30 && last[3].ok) {
            for (int i = 0; i < 4; ++i) {
                layers[i] = last[i];
                layers[i].ox += cx - last_cx;
                layers[i].oy += cy - last_cy;
            }
            ++memo_gen;
            ready = true;
        } else {
            shown = false;
        }
    }
    gba::g_ws_pillarbox = ready ? 0 : 1;
    {   // What the wide margins are drawn from, for the repeat-frame skip (gba_ppu.cpp g_ppu_view_sig).
        std::uint32_t h = 2166136261u;
        const auto mix = [&h](std::uint32_t v) { h = (h ^ v) * 16777619u; };
        mix(ready); mix(static_cast<std::uint32_t>(W));
        for (const auto& l : layers) { mix(l.ok); mix(l.map); mix(l.set); mix(static_cast<std::uint32_t>(l.ox)); mix(static_cast<std::uint32_t>(l.oy)); }
        if (ready && ewram) {
            std::uint32_t done[4]; int nd = 0;
            for (const auto& l : layers) {
                if (!l.ok || l.map + 0x2800u > 0x40000u) continue;
                bool seen = false; for (int i = 0; i < nd; ++i) seen |= done[i] == l.map;
                if (seen) continue; done[nd++] = l.map;
                const std::uint32_t* m = reinterpret_cast<const std::uint32_t*>(ewram + l.map);
                if (reinterpret_cast<std::uintptr_t>(m) & 3u) { for (std::uint32_t o = 0; o < 0x2800u; ++o) mix(ewram[l.map + o]); }
                else for (std::uint32_t o = 0; o < 0x2800u / 4u; ++o) mix(m[o]);
            }
        }
        gba::g_ppu_view_sig = h;
    }
    const int status = ready ? 1 : 0;
    if (status != last_status && std::getenv("ROTK_VIEW_LOG")) {
        std::fprintf(stderr, "[rotk:view] %s frame=%llu bg2=%d bg3=%d\n", ready ? "wide" : "native",
                     static_cast<unsigned long long>(f->frame_count), layers[2].ok, layers[3].ok);
    }
    last_status = status;
}

}  // namespace rotk_view


// ---- P2 partner: two linked games in one process (Jordan, 2026-11-08) ----
// The shown game (machine 0, Jordan) keeps the wide view, 60 fps smoothing and
// sound; machine 1 (P2) runs alongside with no picture. Its buttons come from the
// page (g_link_p2_keys), which runs the P2 bot.
#include "multiplayer_session.h"
#include "frame_smooth.h"
#include "host_window.h"
#include "gba_bios.h"
#include <fstream>
#include <functional>
#include <memory>
#include <vector>
#include <array>
#include <string>
#include <chrono>
#include <algorithm>
#if !defined(__EMSCRIPTEN__) && __has_include(<valgrind/callgrind.h>)
#include <valgrind/callgrind.h>

// ---- virtual partner (P2 inside one game, 2026-11-13) ----
namespace gba { extern std::uint16_t (*g_link_virtual_word)(std::uint16_t master, std::uint16_t slave); extern bool g_link_virtual1; }
namespace gbarecomp { extern unsigned g_session_skip_mask; }
static const std::uint8_t* g_vp_iw = nullptr;
static const std::uint8_t* g_vp_ew = nullptr;     // machine 0 IWRAM
static std::uint16_t g_vp_keys = 0;               // P2 buttons (GBA bits, 1 = pressed)
static int g_vp_mode = 0;                         // 1 check (real slave sent, prediction compared), 2 virtual
static unsigned g_vp_idx = 99, g_vp_frame = 0;
static std::uint16_t g_vp_prev = 0, g_vp_pk[6];
static unsigned long long g_vp_ok = 0, g_vp_bad = 0, g_vp_badw[16];
static std::uint16_t vp_r16(unsigned a) { return static_cast<std::uint16_t>(g_vp_iw[a & 0x7FFF] | (g_vp_iw[(a + 1) & 0x7FFF] << 8)); }
static std::uint32_t vp_r32(unsigned a) { return vp_r16(a) | (static_cast<std::uint32_t>(vp_r16(a + 2)) << 16); }
static unsigned vp_bs(const std::uint16_t* w) { unsigned s = 0; for (int k = 0; k < 6; ++k) if (k != 1) s += (w[k] & 0xff) + (w[k] >> 8); return s; }
static std::uint16_t vp_word(std::uint16_t m, std::uint16_t real) {
    if (m == 0xC0DE && g_vp_prev != 0xC0DE) g_vp_idx = 0; else ++g_vp_idx;
    g_vp_prev = m;
    static const std::uint16_t hs[5] = {0xBEEF, 0xC0DE, 0xC0DE, 0xBABE, 0xBABE};
    std::uint16_t p = real;
    if (g_vp_idx < 5) p = hs[g_vp_idx];
    else if (g_vp_idx < 11) {
        const unsigned k = g_vp_idx - 5;
        if (k == 0) {
            // master packet in flight (word 0 known now); the rest from machine 0's send buffer
            std::uint16_t mp[6]; mp[0] = m; for (int j = 1; j < 6; ++j) mp[j] = vp_r16(0x03006D14 + 2 * j);
            for (int j = 0; j < 6; ++j) g_vp_pk[j] = 0;
            if ((m & 0xff) == 0x13) {
                g_vp_pk[0] = static_cast<std::uint16_t>(0x13 | (((m >> 8) - 1) & 0xff) << 8);
                g_vp_pk[2] = static_cast<std::uint16_t>(0xFC00 | (g_vp_keys & 0x3ff));
                const std::uint32_t h = vp_r32(0x03003C00 + 0x1AC);
                if (h >> 24 == 2 || h >> 24 == 3) {
                    // hero object (EWRAM or IWRAM); position halfwords at +0xAE / +0xB2
                    auto rd = [](std::uint32_t a) -> std::uint8_t { return a >> 24 == 3 ? g_vp_iw[a & 0x7FFF] : g_vp_ew[a & 0x3FFFF]; };
                    g_vp_pk[3] = static_cast<std::uint16_t>(rd(h + 0xAE) | (rd(h + 0xB2) << 8));
                }
                g_vp_pk[1] = static_cast<std::uint16_t>(mp[1] + vp_bs(mp) - vp_bs(g_vp_pk));
            } else {   // other messages (events) are built the same on both games: master's payload, P2's sequence
                for (int j = 0; j < 6; ++j) g_vp_pk[j] = mp[j];
                g_vp_pk[0] = static_cast<std::uint16_t>((m & 0xff) | (((m >> 8) - 1) & 0xff) << 8);
                g_vp_pk[1] = static_cast<std::uint16_t>(mp[1] + vp_bs(mp) - vp_bs(g_vp_pk));
            }
        }
        p = g_vp_pk[k];
    }
    if (g_vp_mode == 1) {
        if (p == real) ++g_vp_ok; else { ++g_vp_bad; ++g_vp_badw[std::min(g_vp_idx, 15u)];
            static int shown = 0; if (g_vp_frame > 600 && shown++ < 40) std::fprintf(stderr, "[vp] f%u idx%u master %04x real %04x pred %04x\n", g_vp_frame, g_vp_idx, m, real, p); }
        return real;
    }
    return p;
}

#endif
extern gba::GbaBus* g_session_hook_bus;
extern std::uint64_t g_session_slice_lookahead;
extern "C" int g_session_bridge_misses;
extern "C" unsigned g_session_bridged_misses;
extern "C" int g_web_tick_stats[12];
extern "C" unsigned rotk_link_hash();
namespace gba { extern unsigned g_link_hub_starts; }
extern "C" unsigned g_ws_extra, g_ws_extra_left, g_ws_extra_right, g_ws_view_width, g_ws_active;
void runtime_set_frame_start_hook(std::function<void()>);
void runtime_set_vblank_latch_hook(std::function<void()>);
namespace gbarecomp {
#if defined(GBR_WEB_SINGLE)

[[noreturn]] void runtime_web_run_frames(std::function<bool()> frame);
#endif
}
void rotk_link_setup(gbarecomp::GbaInstance& m);

static std::unique_ptr<gbarecomp::GbaMultiplayerSession> g_link;
extern "C" {
unsigned g_link_p2_keys = 0;
int g_link_turbo = 0;                     // extra game frames per picture (fast start)            // set by the page every frame
int g_link_on = 0;
unsigned g_link_frames = 0;
unsigned g_link_level = 0;              // nonzero: the level both games start from the path screen (82 = Moria)
}
// Online play (Jordan, 2026-11-08: online games in Wide). Each player's page runs both games and the pages
// trade only buttons (lockstep, like the Classic online game). ROTK_LINK_NET=1: frames run only when the page
// hands over both players' buttons for that frame (rotk_link_push); ROTK_LINK_SHOW picks the game that is shown
// and heard (0 host, 1 guest). Both games then run in full (no quiet mixer) so both pages stay byte-identical.
static int g_link_net = 0;
static unsigned g_link_show = 0;
static std::vector<std::array<std::uint16_t, 2>> g_net_q;
static std::size_t g_net_head = 0;
// The multiplayer path screen only offers story levels; when the page asks for another level,
// swap it in as the path screen hands its choice to the level loader (both games, same frame).
static void link_force_level() {
    static int armed[2] = {0, 0};
    if (!g_link_level || !g_link) return;
    for (unsigned i = 0; i < 2; ++i) {
        std::uint8_t* iw = g_link->machine(i).bus.iwram_ptr();
        const auto rd = [iw](unsigned o) { return iw[o] | (iw[o + 1] << 8) | (iw[o + 2] << 16) | (unsigned(iw[o + 3]) << 24); };
        const unsigned state = rd(0x41B0);
        static const bool dbg = std::getenv("ROTK_LINK_DBG") != nullptr;
        if (dbg && i == 0 && (state == 11 || armed[i])) std::fprintf(stderr, "lvl st=%u sub=%u pend=%u plvl=%u cur8=%u armed=%d\n", state, rd(0x41C0), rd(0x41F0), iw[0x41F8], iw[0x41B8], armed[i]);
        if (state == 11) armed[i] = 600;            // on the path screen: the next level start is ours
        else if (armed[i] > 0) --armed[i];
        if (armed[i] && (rd(0x41F0) & 0x7f) == 1 && iw[0x41F8] && iw[0x41F8] != g_link_level) { iw[0x41F8] = static_cast<std::uint8_t>(g_link_level); }
        if (armed[i] && state == 1 && iw[0x41F8] == g_link_level) armed[i] = std::min(armed[i], 30);
    }
}
static gba::GbaBios g_link_bios;
static std::vector<std::uint8_t> g_link_rom;

static std::vector<std::uint8_t> read_all(const char* p) {
    std::ifstream f(p, std::ios::binary);
    return std::vector<std::uint8_t>((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
}

namespace {
const char* env(const char* k, const char* d) { const char* v = std::getenv(k); return v && *v ? v : d; }
void write_ppm(const char* path, const std::uint8_t* rgb, unsigned w, unsigned h) {
    FILE* f = std::fopen(path, "wb"); if (!f) return;
    std::fprintf(f, "P6 %u %u 255\n", w, h); std::fwrite(rgb, 1, w * h * 3, f); std::fclose(f);
}
}

static int run_link(const gbarecomp::RunOptions& opts) {
    using namespace gbarecomp;
    const char* rom_path = env("ROTK_LINK_ROM", "/data/rom.gba");
    const char* bios_path = env("ROTK_LINK_BIOS", "/data/bios.bin");
    const char* sav[2] = {env("ROTK_LINK_SAVE0", "/data/p1.sav"), env("ROTK_LINK_SAVE1", "/data/p2.sav")};
    g_link_rom = read_all(rom_path);
    const auto bios_bytes = read_all(bios_path);
    std::string err;
    if (g_link_rom.empty() || !g_link_bios.load_from_bytes(bios_bytes.data(), bios_bytes.size(), "", &err)) {
        std::fprintf(stderr, "[rotk:link] cannot load rom/bios %s\n", err.c_str()); return 1;
    }
    GbaSessionConfig config;
    for (unsigned port = 0; port < 2; ++port) config.machines.push_back({port, "rotk", opts.builtin_rom_sha1});
    config.links = {{GbaLinkMedium::Cable, {0, 1}}};
    config.input_machines = {0, 1};
    g_link = std::make_unique<GbaMultiplayerSession>(std::move(config));
    auto& S = *g_link;
    S.set_native_slices(true);
    g_session_bridge_misses = std::getenv("ROTK_LINK_STRICT") ? 0 : 1;
    // RotK links in multiplayer mode only (5755+ cycles per transfer).
    g_session_slice_lookahead = std::strtoull(env("ROTK_LINK_LOOKAHEAD", "4096"), nullptr, 0);
    for (unsigned i = 0; i < 2; ++i) {
        auto& m = S.machine(i);
        m.bus.set_bios(&g_link_bios);
        m.bus.set_rom(g_link_rom.data(), g_link_rom.size());
        auto& save = m.bus.save();
        save.configure_eeprom(8192);   // the 64 Kbit chip (v124); an older 512-byte save is its first blocks
        const auto bytes = read_all(sav[i]);
        if (!bytes.empty() && !save.load_eeprom_bytes(bytes.data(), bytes.size()))
            std::fprintf(stderr, "[rotk:link] save %u has the wrong size\n", i);
        save.clear_dirty();
        rotk_link_setup(m);
    }
    g_link_net = std::atoi(env("ROTK_LINK_NET", "0")) != 0;
    g_link_show = std::atoi(env("ROTK_LINK_SHOW", "0")) ? 1u : 0u;
    S.machine(1 - g_link_show).ppu.set_rasterization_enabled(false);
    // Repeat frames keep the last picture instead of being drawn again (2026-11-11). ROTK_REPEAT_SKIP=0 turns it off.
    gba::g_ppu_repeat_skip = std::atoi(env("ROTK_REPEAT_SKIP", "1")) != 0;
    { extern gba::GbaBus* g_link_quiet_bus; g_link_quiet_bus = g_link_net ? nullptr : &S.machine(1).bus; }
    {   // same cold start as the link probe (before the wide view: snapshots refuse it)
        auto cold = S.save_state();
        if (!S.load_state(cold, &err)) { std::fprintf(stderr, "[rotk:link] %s\n", err.c_str()); return 1; }
    }
    auto& m0 = S.machine(g_link_show);   // the game shown and heard on this page
    // Same 4:3 view as solo play.
    ViewGeometry g;
    g.width = std::clamp<std::uint32_t>(std::atoi(env("ROTK_LINK_VW", "0")) ? std::atoi(env("ROTK_LINK_VW", "0")) : opts.max_view_width, 240, opts.max_view_width); g.extra_left = (g.width - 240) / 2; g.extra_right = g.width - 240 - g.extra_left;
    if (opts.view_geometry) opts.view_geometry(&g, 0, 0);
    m0.ppu.set_view_margins(g.extra_left, g.extra_right, g.extra_top, g.extra_bottom);
    g_ws_extra_left = static_cast<unsigned>(m0.ppu.view_extra_left());
    g_ws_extra_right = static_cast<unsigned>(m0.ppu.view_extra_right());
    g_ws_extra = std::max(g_ws_extra_left, g_ws_extra_right);
    g_ws_view_width = m0.ppu.render_width();
    g_ws_active = m0.ppu.view_expanded() ? 1u : 0u;
    if (m0.ppu.view_expanded() && opts.extended_view_init) opts.extended_view_init(m0.ppu.view_extra_left(), m0.ppu.view_extra_right());
    g_session_hook_bus = &m0.bus;
    static FrameSmoother smoother;
    smoother.enabled = std::string(env("GBARECOMP_SMOOTH", "1")) != "0";
#if defined(GBR_WEB_SINGLE)
    smoother.check_every = 8;
#endif
    runtime_set_frame_start_hook([&opts, &m0]() {
        if (!opts.extended_view_frame) return;
        ExtendedViewFrameInfo info{};
        info.frame_count = m0.ppu.frame_count();
        info.state_epoch = 1;
        info.view_width = m0.ppu.render_width();
        info.extra_left = m0.ppu.view_extra_left(); info.extra_right = m0.ppu.view_extra_right();
        info.view_height = m0.ppu.render_height();
        info.extra_top = m0.ppu.view_extra_top(); info.extra_bottom = m0.ppu.view_extra_bottom();
        info.io = m0.bus.io().raw(); info.io_size = gba::GbaIo::kIoSize;
        opts.extended_view_frame(&info);
    });
    runtime_set_vblank_latch_hook([&m0]() {
        auto v = m0.bus.vram_read_view();
        smoother.on_latch(m0.bus.io().read16(0x000), m0.bus.io().raw(), v.data(), v.size(), m0.bus.oam_ptr(), m0.bus.pal_ptr());
    });
    g_link_on = 1;
    static std::vector<std::uint8_t> fb;
    static std::uint64_t last_frame = ~0ull;
    static int16_t audio_buf[2048];
#if defined(GBR_WEB_SINGLE)
    static HostWindow win;
    if (!win.open(3, m0.ppu.render_width(), m0.ppu.render_height(), "RotK 2P", nullptr, false, false, false, false)) return 1;
    runtime_web_run_frames([&m0, &S]() {
        auto ev = win.pump();
        if (ev.quit) return false;
        std::array<std::uint16_t, 2> keys{static_cast<std::uint16_t>(~ev.keyinput & 0x3ff), static_cast<std::uint16_t>(g_link_p2_keys & 0x3ff)};
        // Fast start (page sets g_link_turbo while it drives the menus): several game frames per picture, no sound.
        int reps = 1 + (g_link_turbo > 0 ? (g_link_turbo < 8 ? g_link_turbo : 8) : 0);
        if (g_link_net) reps = static_cast<int>(std::min<std::size_t>(g_net_q.size() - g_net_head, 6));
        for (int r = 0; r < reps; ++r) {
            if (g_link_net) { keys = g_net_q[g_net_head++]; if (g_net_head == g_net_q.size()) { g_net_q.clear(); g_net_head = 0; } }
            try { S.run_frame(keys); link_force_level(); } catch (const std::exception& e) {
                std::fprintf(stderr, "[rotk:link] stopped: %s\n", e.what()); return false;
            }
            ++g_link_frames;
            if (r + 1 < reps) for (int b = 0; b < 16; ++b) { std::uint32_t rate = 0; if (!m0.bus.audio().drain_sample_block(audio_buf, 2048, rate)) break; }
        }
        if (m0.ppu.frame_count() != last_frame && m0.ppu.has_latched_framebuffer()) {
            last_frame = m0.ppu.frame_count();
            fb.assign(m0.ppu.latched_framebuffer(), m0.ppu.latched_framebuffer() + m0.ppu.render_bytes());
            smoother.apply(m0.ppu, fb.data(), fb.size());
            {   // play-log counts (in-between / skipped / blended / big moves), like the 1-player engine
                g_web_tick_stats[5] = (int)smoother.mids; g_web_tick_stats[6] = (int)smoother.skipped;
                g_web_tick_stats[7] = (int)smoother.blends; g_web_tick_stats[8] = (int)smoother.incompat;
                g_web_tick_stats[9] = (int)smoother.gaps[1]; g_web_tick_stats[10] = (int)smoother.gaps[2];
                static const bool gdbg = std::getenv("ROTK_GAPS") != nullptr;
                if (gdbg) {   // per-frame pattern: N = new picture, digit = cable transfers this frame
                    static std::string pat; static std::uint64_t gs = 0; static unsigned ls = 0;
                    const std::uint64_t g = smoother.gaps[0] + smoother.gaps[1] + smoother.gaps[2] + smoother.gaps[3];
                    pat += g != gs ? 'N' : '.'; gs = g;
                    const unsigned st = gba::g_link_hub_starts; pat += char('0' + std::min(9u, st - ls)); ls = st;
                    if (pat.size() >= 120) { std::fprintf(stderr, "[pat] %s\n", pat.c_str()); pat.clear(); }
                }
                if (gdbg && (last_frame % 300) == 0) std::fprintf(stderr, "[gaps] %llu/%llu/%llu/%llu\n", (unsigned long long)smoother.gaps[0], (unsigned long long)smoother.gaps[1], (unsigned long long)smoother.gaps[2], (unsigned long long)smoother.gaps[3]);
            }
            win.present(fb.data(), m0.ppu.render_width(), m0.ppu.render_height());
        }
        for (int b = 0; b < 16; ++b) { std::uint32_t rate = 0; const auto n = m0.bus.audio().drain_sample_block(audio_buf, 2048, rate); if (!n) break; win.push_audio_block(audio_buf, n, rate); }
        for (int b = 0; b < 16; ++b) { std::uint32_t rate = 0; if (!S.machine(1 - g_link_show).bus.audio().drain_sample_block(audio_buf, 2048, rate)) break; }
        return true;
    });
#else
    // Headless test: ROTK_LINK_FRAMES frames, buttons from ROTK_LINK_INPUTS ("frame k0 k1" rows),
    // pictures of machine 0 into ROTK_LINK_DUMP every ROTK_LINK_DUMP_EVERY frames.
    const unsigned frames = std::atoi(env("ROTK_LINK_FRAMES", "600"));
    std::vector<std::array<unsigned, 3>> rows;
    if (const char* p = std::getenv("ROTK_LINK_INPUTS")) { std::ifstream f(p); unsigned a, b, c; while (f >> a >> b >> c) rows.push_back({a, b, c}); }
    g_link_level = std::atoi(env("ROTK_LINK_LEVEL", "0"));
    const char* dump = std::getenv("ROTK_LINK_DUMP");
    const unsigned every = std::atoi(env("ROTK_LINK_DUMP_EVERY", "60"));
    std::size_t ri = 0; std::array<std::uint16_t, 2> keys{0, 0};
    // ROTK_LINK_AUTO="p1slot,p2slot": the page's boot (title -> Multiplayer -> Load Game -> path screen) run here,
    // then a fight bot for both heroes (attack + walk in a square, HP kept full) and a speed report every 300
    // frames: host ms per game frame, object count (speed test for big Helm's Deep fights, 2026-11-11).
    int auto_p[2] = {-1, -1};
    if (const char* a = std::getenv("ROTK_LINK_AUTO")) std::sscanf(a, "%d,%d", &auto_p[0], &auto_p[1]);
    const auto iwr = [&S](unsigned i, unsigned o) { const std::uint8_t* iw = S.machine(i).bus.iwram_ptr(); return iw[o] | (iw[o + 1] << 8) | (iw[o + 2] << 16) | (unsigned(iw[o + 3]) << 24); };
    const auto iw8 = [&S](unsigned i, unsigned o) { return unsigned(S.machine(i).bus.iwram_ptr()[o]); };
    struct Press { unsigned k0, k1, hold, after; };
    std::vector<Press> presses; unsigned press_t = 0, phase = 0, phase_t = 0, tries = 0, level_f = 0;
    auto tw = std::chrono::steady_clock::now(); unsigned tw_f = 0;
    const auto auto_keys = [&](unsigned f) -> std::array<std::uint16_t, 2> {
        if (!presses.empty()) {
            Press& p = presses.front();
            if (press_t == 0) press_t = f;
            const unsigned d = f - press_t;
            if (d < p.hold) return {static_cast<std::uint16_t>(p.k0), static_cast<std::uint16_t>(p.k1)};
            if (d >= p.hold + p.after) { presses.erase(presses.begin()); press_t = 0; }
            return {0, 0};
        }
        const unsigned s0 = iwr(0, 0x41B0) & 255, s1 = iwr(1, 0x41B0) & 255;
        if (phase == 0) {   // title menu: both cursors to Multiplayer (2), A
            if (s0 != 5 || s1 != 5 || iw8(0, 0x41C0) != 2 || iw8(1, 0x41C0) != 2) return {0, 0};
            if (!phase_t) phase_t = f;
            if (f - phase_t < 60) return {0, 0};
            const unsigned c0 = iw8(0, 0x41B8), c1 = iw8(1, 0x41B8);
            if (c0 == 2 && c1 == 2) { presses.push_back({1, 1, 6, 60}); phase = 1; phase_t = 0; return {0, 0}; }
            const auto mv = [](unsigned c) { return c < 2 ? 128u : c > 2 ? 64u : 0u; };
            presses.push_back({mv(c0), mv(c1), 4, 24}); return {0, 0};
        }
        if (phase == 1) {   // Load Game: cursors to the slots (2x2 grid), A
            if (s0 != 9 || s1 != 9) return {0, 0};
            if (!phase_t) phase_t = f;
            if (f - phase_t < 120) return {0, 0};
            const unsigned c[2] = {iw8(0, 0x41BC), iw8(1, 0x41BC)};
            if (int(c[0]) == auto_p[0] && int(c[1]) == auto_p[1]) { presses.push_back({1, 1, 4, 60}); phase = 2; phase_t = f; return {0, 0}; }
            const auto mv = [&](unsigned i) { const unsigned w = unsigned(auto_p[i]); return (c[i] & 1) != (w & 1) ? (w & 1 ? 16u : 32u) : (c[i] >> 1) != (w >> 1) ? (w >> 1 ? 128u : 64u) : 0u; };
            if (++tries > 20) { std::fprintf(stderr, "[auto] slots failed\n"); phase = 9; }
            presses.push_back({mv(0), mv(1), 4, 20}); return {0, 0};
        }
        if (phase == 2) {   // path screen: P1 presses A until both games are in the level
            if (s0 == 1 && s1 == 1 && f - phase_t > 200) { phase = 3; level_f = f; std::fprintf(stderr, "[auto] in level %u at frame %u\n", iw8(0, 0x41F8), f); return {0, 0}; }
            if (s0 == 9 && s1 == 9 && iw8(0, 0x41C0) == 0 && iw8(1, 0x41C0) == 0 && f - phase_t > 120) { phase_t = f; presses.push_back({1, 1, 6, 60}); return {0, 0}; }
            if (s0 == 11 && f % 240 == 0) presses.push_back({1, 0, 4, 90});
            return {0, 0};
        }
        if (phase == 3) {   // fight: HP full, attack, walk a slow square
            // ROTK_LINK_POKES="after:addr:value;...": 32-bit RAM writes into both games, frames after the level start
            // (e.g. the test-only spawn ROM from tools/engine/build_spawntest.py for a bigger fight).
            static std::vector<std::array<unsigned, 3>> pokes = [] {
                std::vector<std::array<unsigned, 3>> v; const char* e = std::getenv("ROTK_LINK_POKES");
                for (const char* q = e; q && *q;) { unsigned a, b, c; int n = 0; if (std::sscanf(q, "%u:%x:%x%n", &a, &b, &c, &n) < 3) break; v.push_back({a, b, c}); q += n; if (*q == ';') ++q; }
                return v; }();
            for (const auto& pk : pokes) if (pk[0] == f - level_f) for (unsigned m = 0; m < 2; ++m) {
                std::uint8_t* b = pk[1] >> 24 == 2 ? S.machine(m).bus.ewram_ptr() + (pk[1] & 0x3FFFF) : S.machine(m).bus.iwram_ptr() + (pk[1] & 0x7FFF);
                for (int k = 0; k < 4; ++k) b[k] = static_cast<std::uint8_t>(pk[2] >> (8 * k));
            }
            for (unsigned m = 0; m < 2; ++m) for (unsigned pl = 0; pl < 2; ++pl) {
                const unsigned h = iwr(m, 0x3C00 + 0x1AC * pl);
                if (h >> 24 == 2) { std::uint8_t* e = S.machine(m).bus.ewram_ptr() + (h - 0x02000000u) + 0x5A; e[0] = 0x2C; e[1] = 0x01; }
            }
            const unsigned t = f - level_f;
            static const unsigned dirs[4] = {16, 128, 32, 64};
            const unsigned d0 = dirs[(t / 90) % 4], d1 = dirs[(t / 90 + 2) % 4];
            const unsigned atk = (t % 12) < 4 ? 2u : 0u;
            return {static_cast<std::uint16_t>(((t % 180) < 60 ? d0 : 0) | atk), static_cast<std::uint16_t>(((t % 180) < 60 ? d1 : 0) | atk)};
        }
        return {0, 0};
    };
#if defined(ROTK_OLD_RUNTIME)
#define RS_COUNT(x) 0ull
#else
#define RS_COUNT(x) (unsigned long long)m0.ppu.repeat_frames_##x
#endif
    const auto t0 = std::chrono::steady_clock::now();
    unsigned mids = 0;
    for (unsigned f = 0; f < frames; ++f) {
        while (ri < rows.size() && rows[ri][0] == f) { keys = {static_cast<std::uint16_t>(rows[ri][1]), static_cast<std::uint16_t>(rows[ri][2])}; ++ri; }
        if (auto_p[0] >= 0) keys = auto_keys(f);
        if (const char* vm = std::getenv("ROTK_VP")) { if (!g_vp_mode) { g_vp_mode = vm[0] == 'v' ? 2 : 1; gba::g_link_virtual_word = vp_word; }
            g_vp_iw = S.machine(0).bus.iwram_ptr(); g_vp_ew = S.machine(0).bus.ewram_ptr(); g_vp_keys = keys[1]; g_vp_frame = f;
            static const unsigned vp_at = std::atoi(env("ROTK_VP_AT", "0"));
            if (f % 150 == 0) { auto pos = [&](int pl) { const std::uint32_t h = vp_r32(0x03003C00 + 0x1AC * pl); if (h >> 24 != 2) return std::string("-"); const std::uint8_t* e = g_vp_ew + (h & 0x3FFFF);
                    char b[40]; std::snprintf(b, sizeof b, "%d,%d", e[0xAE] | e[0xAF] << 8, e[0xB2] | e[0xB3] << 8); return std::string(b); };
                std::fprintf(stderr, "[vp] f%u P1 %s P2 %s sub %u state %u\n", f, pos(0).c_str(), pos(1).c_str(), g_vp_iw[0x41C0], g_vp_iw[0x41B0]); }
            if (vp_at && f == vp_at && g_vp_mode == 1) { g_vp_mode = 2; gba::g_link_virtual1 = true; gbarecomp::g_session_skip_mask = 2;
                std::fprintf(stderr, "[vp] f%u second game switched off (ok %llu bad %llu so far)\n", f, g_vp_ok, g_vp_bad); } }
        S.run_frame(keys); link_force_level();
#if !defined(__EMSCRIPTEN__) && __has_include(<valgrind/callgrind.h>)
        if (auto_p[0] >= 0 && phase == 3) {   // profile only frames [ROTK_PROF_FROM, +ROTK_PROF_N) after the level start
            static const unsigned pf = std::atoi(env("ROTK_PROF_FROM", "600")), pn = std::atoi(env("ROTK_PROF_N", "120"));
            if (f - level_f == pf) CALLGRIND_START_INSTRUMENTATION;
            if (f - level_f == pf + pn) { CALLGRIND_STOP_INSTRUMENTATION; CALLGRIND_DUMP_STATS; }
        }
#endif
        if (auto_p[0] >= 0 && phase == 3 && (f - level_f) % 300 == 0) {
            const auto now = std::chrono::steady_clock::now();
            int objs = 0;
            for (unsigned o = iwr(0, 0x2420); o >> 24 == 2 && objs < 400; ++objs) { const std::uint8_t* e = S.machine(0).bus.ewram_ptr() + (o - 0x02000000u); o = e[0] | (e[1] << 8) | (e[2] << 16) | (unsigned(e[3]) << 24); }
            if (tw_f) std::printf("[speed] frames %u-%u: %.2f ms/frame (%.1f fps) objects=%d state=%u/%u lvl=%u gameframe=%u skipped=%llu drawn=%llu redrawn=%llu hash=%08x\n", tw_f, f,
                std::chrono::duration<double, std::milli>(now - tw).count() / (f - tw_f), (f - tw_f) * 1000.0 / std::chrono::duration<double, std::milli>(now - tw).count(), objs,
                iwr(0, 0x41B0) & 255, iwr(1, 0x41B0) & 255, iw8(0, 0x41F8), iwr(0, 0x41A4), RS_COUNT(skipped), RS_COUNT(drawn), RS_COUNT(redrawn), rotk_link_hash());
            std::fflush(stdout);
            tw = now; tw_f = f;
        }
        if (const char* md = std::getenv("ROTK_LINK_MEMDUMP")) { const unsigned a0 = std::atoi(env("ROTK_LINK_MEMDUMP_FROM", "2000")), n = std::atoi(env("ROTK_LINK_MEMDUMP_N", "8"));
            if (f >= a0 && f < a0 + n) for (int i = 0; i < 2; ++i) { char p[512]; std::snprintf(p, sizeof p, "%s/m%d_f%05u.bin", md, i, f); if (FILE* o = std::fopen(p, "wb")) { std::fwrite(S.machine(i).bus.iwram_ptr(), 1, 0x8000, o); std::fwrite(S.machine(i).bus.ewram_ptr(), 1, 0x40000, o); std::fclose(o); } } }
        if (m0.ppu.has_latched_framebuffer()) {
            fb.assign(m0.ppu.latched_framebuffer(), m0.ppu.latched_framebuffer() + m0.ppu.render_bytes());
            if (smoother.apply(m0.ppu, fb.data(), fb.size())) ++mids;
            if (dump && every && f % every == 0) {
                char p[512]; std::snprintf(p, sizeof p, "%s/f%05u.ppm", dump, f);
                write_ppm(p, fb.data(), m0.ppu.render_width(), m0.ppu.render_height());
            }
        }
        for (unsigned i = 0; i < 2; ++i) for (int b = 0; b < 16; ++b) { std::uint32_t rate = 0; if (!S.machine(i).bus.audio().drain_sample_block(audio_buf, 2048, rate)) break; }
    }
    const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
    if (g_vp_mode) { std::fprintf(stderr, "[vp] ok %llu bad %llu by idx:", g_vp_ok, g_vp_bad); for (int k = 0; k < 16; ++k) if (g_vp_badw[k]) std::fprintf(stderr, " %d:%llu", k, g_vp_badw[k]); std::fprintf(stderr, "\n"); }
    std::printf("link frames=%u ms=%.0f fps=%.1f mids=%u size=%ux%u lvl0=%u lvl1=%u\n", frames, ms, frames * 1000.0 / ms, mids,
                m0.ppu.render_width(), m0.ppu.render_height(), m0.bus.iwram_ptr()[0x41F8], S.machine(1).bus.iwram_ptr()[0x41F8]);
    for (unsigned i = 0; i < 2; ++i) if (const char* out = std::getenv(i ? "ROTK_LINK_OUT1" : "ROTK_LINK_OUT0")) {
        const auto b = S.machine(i).bus.save().eeprom_bytes();
        std::FILE* fo = std::fopen(out, "wb"); if (fo) { std::fwrite(b.data(), 1, b.size(), fo); std::fclose(fo); }
    }
#endif
    return 0;
}

// Page access (web build): each game's memory and save.
extern "C" {
const std::uint8_t* rotk_link_iwram(int i) { return g_link ? g_link->machine(i & 1).bus.iwram_ptr() : nullptr; }
const std::uint8_t* rotk_link_ewram(int i) { return g_link ? g_link->machine(i & 1).bus.ewram_ptr() : nullptr; }
void rotk_link_level(unsigned level) { g_link_level = level & 0xff; }
// Online: queue one frame's buttons (GBA bits, 1 = pressed) for both games; returns frames waiting.
int rotk_link_push(unsigned k0, unsigned k1) { g_net_q.push_back({static_cast<std::uint16_t>(k0 & 0x3ff), static_cast<std::uint16_t>(k1 & 0x3ff)}); return static_cast<int>(g_net_q.size() - g_net_head); }
int rotk_link_queued() { return static_cast<int>(g_net_q.size() - g_net_head); }
// Online: hash of both games' work RAM, compared between the two pages now and then (out of step = different).
unsigned rotk_link_hash() {
    if (!g_link) return 0;
    std::uint32_t h = 2166136261u;
    for (unsigned i = 0; i < 2; ++i) {
        const std::uint8_t* iw = g_link->machine(i).bus.iwram_ptr(); const std::uint8_t* ew = g_link->machine(i).bus.ewram_ptr();
        for (unsigned o = 0; o < 0x8000; ++o) h = (h ^ iw[o]) * 16777619u;
        for (unsigned o = 0; o < 0x40000; o += 4) h = (h ^ (ew[o] | ew[o + 1] << 8 | ew[o + 2] << 16 | unsigned(ew[o + 3]) << 24)) * 16777619u;
    }
    return h;
}
// Copies game i's save (8 KB, the 64 Kbit chip; padded with 0xFF if smaller) into out; returns 1 if it changed
// since the last call for that game.
int rotk_link_save(int i, std::uint8_t* out) {
    if (!g_link) return -1;
    auto& s = g_link->machine(i & 1).bus.save();
    const auto b = s.eeprom_bytes();
    const std::size_t n = std::min<std::size_t>(b.size(), 8192);
    std::memcpy(out, b.data(), n);
    if (n < 8192) std::memset(out + n, 0xFF, 8192 - n);
    const bool dirty = s.dirty(); s.clear_dirty();
    return dirty ? 1 : 0;
}
}
int main(int argc, char** argv) {
    gbarecomp::RunOptions opts;
    opts.builtin_game_name = "The Lord of the Rings: The Return of the King (USA, Europe) Modded";
    opts.builtin_rom_sha1 = "dd6d504c587ce487c983968f4f01748457b30ed8";
    opts.max_view_width = 320;
    opts.extended_view_init = rotk_view::install;
    opts.extended_view_frame = rotk_view::frame;
    opts.view_geometry = rotk_view::geometry;
    if (std::getenv("ROTK_LINK")) return run_link(opts);
    return gbarecomp::run_game(argc, argv, opts);
}
