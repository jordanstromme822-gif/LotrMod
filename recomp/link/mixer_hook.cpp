// Return of the King's sound mixer (IWRAM 0x03000B38) rewrites the shift amount of
// eight of its own instructions (setter at 0x03000BF0). Linked play needs fixed
// code, so this runs the routine natively, reading the current shift from RAM.
#include "multiplayer_session.h"
#include "runtime_arm.h"
#include "runtime_bus_bridge.h"
#include "gba_bus.h"
#include <cstdint>

// P2's game is never heard: its mixer only moves the pointers and charges the same time.
gba::GbaBus* g_link_quiet_bus = nullptr;
namespace {
constexpr std::uint32_t kStart = 0x03000B38u, kEnd = 0x03000BF0u;
inline std::uint32_t iw32(const std::uint8_t* iw, std::uint32_t a) {
    a &= 0x7FFF; return iw[a] | (iw[a + 1] << 8) | (iw[a + 2] << 16) | (std::uint32_t(iw[a + 3]) << 24);
}
int filter(std::uint32_t pc, int thumb) { return !thumb && ((pc >= kStart && pc < kEnd) || (pc >= 0x03000004u && pc < 0x03000050u)); }
// 0x03000004: small IRQ helper copied to IWRAM whose last word is rewritten after the copy
// (0x0300007C stores BX LR at 0x0300004C). Bumps a counter and restarts two DMA channels.
int irq_helper(gba::GbaBus* bus) {
    const std::uint8_t* iw = bus->iwram_ptr();
    const std::uint32_t c = iw32(iw, 0x0300007C), d1 = iw32(iw, 0x03000080), d2 = iw32(iw, 0x03000084);
    bus->write32(c, bus->read32(c) + 1);
    std::uint32_t h = bus->read16(d1) & ~0x8000u;
    bus->write16(d1, h); h |= 0x8000u; bus->write16(d1, h);
    std::uint32_t r0 = d2, r1 = bus->read16(d2);
    if (r1 & 0x8000u) { r1 &= ~0x8000u; bus->write16(d2, r1); r1 |= 0x8000u; bus->write16(d2, r1); }
    g_cpu.R[0] = r0; g_cpu.R[1] = r1;
    const std::uint32_t lr = g_cpu.R[14];
    if (lr & 1) { g_cpu.cpsr |= CPSR_T_BIT; g_cpu.R[15] = lr & ~1u; } else { g_cpu.R[15] = lr & ~3u; }
    runtime_tick(60);
    return 1;
}
int mixer(std::uint32_t pc, int thumb) {
    if (thumb) return 0;
    gba::GbaBus* bus = gbarecomp::active_bus();
    if (!bus) return 0;
    if (pc == 0x03000004u) return irq_helper(bus);
    if (pc != kStart) return 0;  // whole routine runs at once, so no resume inside it
    const std::uint8_t* iw = bus->iwram_ptr();
    const std::uint32_t r8 = (iw32(iw, 0x03000B30) << 7) >> 3, r9 = (iw32(iw, 0x03000B34) << 7) >> 3;
    const int s0 = (iw32(iw, 0x03000B70) >> 7) & 31, s1 = (iw32(iw, 0x03000BB0) >> 7) & 31;
    const std::uint32_t table = iw32(iw, 0x03000C44);
    std::uint32_t r0 = g_cpu.R[0], r1 = g_cpu.R[1], r2 = g_cpu.R[2], n = g_cpu.R[3] >> 2;
    auto pair = [&](std::uint32_t w, std::uint32_t off, int s) {
        std::uint32_t hi = w >> 16, lo = w - (hi << 16);
        hi -= off; lo -= off;
        const std::uint32_t a = bus->read8(table + static_cast<std::uint32_t>(static_cast<std::int32_t>(hi) >> s));
        const std::uint32_t b = bus->read8(table + static_cast<std::uint32_t>(static_cast<std::int32_t>(lo) >> s));
        return b + (a << 8);
    };
    std::uint32_t sl = 0, fp = 0, last4 = 0, last6 = 0;
    std::uint32_t loops = 0;
    if (bus == g_link_quiet_bus) { loops = n; r0 += 16 * loops; r1 += 4 * loops; r2 += 4 * loops; n = 0; }
    else do {
        const std::uint32_t w4 = bus->read32(r0), w5 = bus->read32(r0 + 4), w6 = bus->read32(r0 + 8), w7 = bus->read32(r0 + 12);
        r0 += 16;
        std::uint32_t a = pair(w4, r8, s0), b = pair(w5, r8, s0);
        last4 = a + (b << 16); bus->write32(r1, last4); r1 += 4;
        a = pair(w6, r9, s1); b = pair(w7, r9, s1);
        last6 = a + (b << 16); bus->write32(r2, last6); r2 += 4;
        fp = b; sl = 0;
        --n; ++loops;
    } while (n);
    (void)sl; (void)fp;
    g_cpu.R[0] = r0; g_cpu.R[1] = r1; g_cpu.R[2] = r2; g_cpu.R[3] = 0;
    g_cpu.R[12] = table;
    const std::uint32_t lr = g_cpu.R[14];
    if (lr & 1) { g_cpu.cpsr |= CPSR_T_BIT; g_cpu.R[15] = lr & ~1u; } else { g_cpu.R[15] = lr & ~3u; }
    runtime_tick(30 + loops * 52);  // about what the ARM loop costs in IWRAM
    return 1;
}
}

void rotk_link_setup(gbarecomp::GbaInstance& m) {
    m.execution.ram_dispatch = mixer;
    m.execution.ram_dispatch_filter = filter;
}
#if defined(GBA_LINK_PROBE_SETUP)
void gba_link_probe_setup(gbarecomp::GbaInstance& m) { rotk_link_setup(m); }
#endif
