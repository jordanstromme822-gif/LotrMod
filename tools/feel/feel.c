/* Movement feel (Jordan, 2026-11-17: "stylized pixelated look with a modern feel ... movement, collision, weapons and
 * animations"; "Fix all").
 *
 * The hero's update (object + 0x14) is pointed by the Play Room page at hero_feel below (ROM 0x8A000, CPU 0x0808A000:
 * the German text bank freed by the English-only build, used by Frodo's first 16-facing pictures in v170-v175 and free
 * since they moved past 16 MB in v176). v191-v192 had it at 0x09400000, past 16 MB, which the 2-player/online (link)
 * engine doesn't have: it crashed 2-player games, so v193 kept it to 1-player; v194 moves it here for every game. hero_feel runs the 16-facing hook 0x0809F001 first, then:
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

/* v192 leg speed (Jordan, 2026-11-18: "Frodo still slides running sideways"): the hobbits' walk cycle covers about
   24 px while they move about 37 px running sideways (full speed on screen; up and down is squashed to half), so the
   feet skated. While walking, extra walk frames are put in by the sideways speed: + 1/4 frame a tick at full
   sideways speed, which makes the cycle about 1.5x faster then and leaves up/down as it was. Frodo and Sam only. */
#define SETFRAME(o, f) ((fn4)0x08000DE9)((int)(o), f, 0, 0)
#define LEGS      ((volatile unsigned short *)0x0203FFEC)   /* [player]: extra-frame phase */
#define HERO_ID(p) (*(volatile u8 *)(0x03003C00u + 0x1ACu * (p) + 0x19F))
static void legs(u8 *o, u32 p)
{
    volatile unsigned short *ph = LEGS + p;
    int id = HERO_ID(p);
    if ((id != 0 && id != 6) || (s8)o[0x95] != 6 || o[0x62] != 2) { *ph = 0; return; }
    int vx = S32(o, 0xB4); if (vx < 0) vx = -vx;
    int acc = *ph + (vx >> 8);                 /* 3 px a tick = 768 */
    if (acc >= 3072) {
        acc -= 3072;
        u32 ent = *(volatile u32 *)(o + 0x24);
        int nf = *(const u8 *)(*(const u32 *)(ent + 4) + 6), f = o[0x23] + 1;
        if (nf > 1) SETFRAME(o, f < nf ? f : 0);
    }
    *ph = acc;
}

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
    legs(o, p);
    return r;
}
