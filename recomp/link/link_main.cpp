#if defined(__EMSCRIPTEN__)
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
extern gba::GbaBus* g_session_hook_bus;
extern std::uint64_t g_session_slice_lookahead;
extern "C" int g_session_bridge_misses;
extern "C" unsigned g_session_bridged_misses;
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
unsigned g_link_p2_keys = 0;            // set by the page every frame
int g_link_on = 0;
unsigned g_link_frames = 0;
unsigned g_link_level = 0;              // nonzero: the level both games start from the path screen (82 = Moria)
}
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
        save.configure_eeprom(512);
        const auto bytes = read_all(sav[i]);
        if (!bytes.empty() && !save.load_eeprom_bytes(bytes.data(), bytes.size()))
            std::fprintf(stderr, "[rotk:link] save %u has the wrong size\n", i);
        save.clear_dirty();
        rotk_link_setup(m);
    }
    S.machine(1).ppu.set_rasterization_enabled(false);
    {   // same cold start as the link probe (before the wide view: snapshots refuse it)
        auto cold = S.save_state();
        if (!S.load_state(cold, &err)) { std::fprintf(stderr, "[rotk:link] %s\n", err.c_str()); return 1; }
    }
    auto& m0 = S.machine(0);
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
        const std::array<std::uint16_t, 2> keys{static_cast<std::uint16_t>(~ev.keyinput & 0x3ff), static_cast<std::uint16_t>(g_link_p2_keys & 0x3ff)};
        try { S.run_frame(keys); link_force_level(); } catch (const std::exception& e) {
            std::fprintf(stderr, "[rotk:link] stopped: %s\n", e.what()); return false;
        }
        ++g_link_frames;
        if (m0.ppu.frame_count() != last_frame && m0.ppu.has_latched_framebuffer()) {
            last_frame = m0.ppu.frame_count();
            fb.assign(m0.ppu.latched_framebuffer(), m0.ppu.latched_framebuffer() + m0.ppu.render_bytes());
            smoother.apply(m0.ppu, fb.data(), fb.size());
            win.present(fb.data(), m0.ppu.render_width(), m0.ppu.render_height());
        }
        for (int b = 0; b < 16; ++b) { std::uint32_t rate = 0; const auto n = m0.bus.audio().drain_sample_block(audio_buf, 2048, rate); if (!n) break; win.push_audio_block(audio_buf, n, rate); }
        for (int b = 0; b < 16; ++b) { std::uint32_t rate = 0; if (!S.machine(1).bus.audio().drain_sample_block(audio_buf, 2048, rate)) break; }
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
    const auto t0 = std::chrono::steady_clock::now();
    unsigned mids = 0;
    for (unsigned f = 0; f < frames; ++f) {
        while (ri < rows.size() && rows[ri][0] == f) { keys = {static_cast<std::uint16_t>(rows[ri][1]), static_cast<std::uint16_t>(rows[ri][2])}; ++ri; }
        S.run_frame(keys); link_force_level();
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
// Copies game i's 512-byte save into out; returns 1 if it changed since the last call for that game.
int rotk_link_save(int i, std::uint8_t* out) {
    if (!g_link) return -1;
    auto& s = g_link->machine(i & 1).bus.save();
    const auto b = s.eeprom_bytes();
    std::memcpy(out, b.data(), std::min<std::size_t>(b.size(), 512));
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
