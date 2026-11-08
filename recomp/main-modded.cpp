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

int main(int argc, char** argv) {
    gbarecomp::RunOptions opts;
    opts.builtin_game_name = "The Lord of the Rings: The Return of the King (USA, Europe) Modded";
    opts.builtin_rom_sha1 = "dd6d504c587ce487c983968f4f01748457b30ed8";
    opts.max_view_width = 320;
    opts.extended_view_init = rotk_view::install;
    opts.extended_view_frame = rotk_view::frame;
    opts.view_geometry = rotk_view::geometry;
    return gbarecomp::run_game(argc, argv, opts);
}
