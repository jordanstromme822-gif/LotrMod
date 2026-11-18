/* Movement feel (Jordan, 2026-11-17: "stylized pixelated look with a modern feel ... movement, collision, weapons and
 * animations"; "Fix all").
 *
 * The hero's update (object + 0x14) is pointed by the Play Room page at hero_feel below (ROM 0x09400000, past the
 * enemy pictures; the page grows the built game for it). hero_feel runs the 16-facing hook 0x0809F001 first, then:
 *   - weight: a walk starts at half speed and reaches full speed over 8 ticks (about 0.13 s). Stopping stays instant
 *     so nothing slides (Jordan disliked sliding).
 * Why a separate routine: 0x0809F000 is compiled into the engine (game-link.txt [[extra_func]]), so changing turn16.c
 * has no effect without an engine rebuild, and moving code inside it breaks the compiled copy. This routine is not in
 * the engine's list, so the engine's interpreter runs it from the ROM bytes.
 * EWRAM 0x0203FFE8 + player: ticks into the current walk (checked zero in play; the page, the hooks and the Orc Head
 * code use 0x0203FFC0-FFE4 and FFF0-FFF1 around it).
 */
typedef unsigned char u8; typedef signed char s8; typedef unsigned int u32; typedef int s32;
typedef int (*fn4)(int, int, int, int);
#define TURN16    ((fn4)0x0809F001)
#define RAMP      ((volatile u8 *)0x0203FFE8)
#define S32(o, n) (*(volatile s32 *)((o) + (n)))

__attribute__((section(".text.hero_feel"))) int hero_feel(u8 *o, int a, int b, int c)
{
    int r = TURN16((int)o, a, b, c);
    u32 p = o[0x96];
    if (p > 1) return r;
    volatile u8 *rp = RAMP + p;
    int n = *rp;
    if ((s8)o[0x95] == 6 && o[0x62] == 2 && (S32(o, 0xB4) || S32(o, 0xB8))) {
        if (n < 8) {
            S32(o, 0xB4) = (S32(o, 0xB4) * (8 + n)) >> 4;
            S32(o, 0xB8) = (S32(o, 0xB8) * (8 + n)) >> 4;
            *rp = n + 1;
        }
    } else if (n) *rp = 0;
    return r;
}
