/* Smooth 360-degree walking test (Jordan, 2026-11-11: "re draw the gaps in between the animation frames").
 *
 * With the Play Room's free-angle joystick on, the page writes the stick's screen angle into EWRAM and points the
 * hero's update (object + 0x14, the game's 0x080236B9) at hero_upd below. After the game's own update has worked
 * out its 8-direction walk, hero_upd:
 *   - turns the walk velocity (+0xB4 / +0xB8, read by the move step 0x080023C0 that runs next) to the stick's exact
 *     angle at the same speed (+0xE4), so collision and everything after it stay the game's own;
 *   - for Frodo (hero id 0), picks one of 16 facings and shows an in-between picture (walk and stand) for the odd
 *     ones. The pictures are a separate data block at 0x0808A000 (tools/turn16/gen16.py), laid out like the game's
 *     own anim table (+0x88), so 0x08000D58 loads them like any other picture.
 * Placed at 0x0809F000 (free) by the page. Runs in the engines' interpreter; nothing here is compiled natively.
 */
typedef unsigned char u8; typedef signed char s8; typedef unsigned short u16; typedef unsigned int u32; typedef int s32;
#include "tables.h"

#define FA        ((volatile u8 *)0x0203FFC0)   /* [4 * player]: +0 bit0 on, bit1 stick held; +1 angle; +2 facing16 | 0x80 */
#define TBL16     0x0808A000u                   /* our anim table: kinds 4 and 6 have 4 in-between facings */
#define TBL16_END 0x0808A400u
#define HERO      0x03003C00u
#define HERO_SZ   0x1ACu
#define DIR5      ((const s8 *)0x08050418)      /* facing 0-7 -> drawn direction 0-4 */
#define U32(o, n) (*(volatile u32 *)((o) + (n)))
#define S32(o, n) (*(volatile s32 *)((o) + (n)))

typedef int (*fn4)(int, int, int, int);
#define UPDATE(o)        ((fn4)0x080236B9)((int)(o), 0, 0, 0)
#define SETPIC(o, t, k, d) ((fn4)0x08000D59)((int)(o), (int)(t), k, d)
#define SETFRAME(o, f)   ((fn4)0x08000DE9)((int)(o), f, 0, 0)

static int frames_of(u32 entry) { return *(const u8 *)(*(const u32 *)(entry + 4) + 6); }

/* show anim kind k, drawn direction d of table t, keeping the walk step */
static void show(u8 *o, u32 t, int k, int d)
{
    int fr = o[0x23];
    SETPIC(o, t, k, d);
    if (fr && fr < frames_of(U32(o, 0x24))) SETFRAME(o, fr);
}

/* the game's facing (0-7) that goes with facing16 f: even = the same, odd = the neighbour the picture is mirrored like */
static int f8_of(int f)
{
    if (!(f & 1)) return f >> 1;
    return f < 8 ? (f - 1) >> 1 : ((f + 1) >> 1) & 7;
}

static void turn(u8 *o)
{
    u32 p = o[0x96];
    if (p > 1) return;
    volatile u8 *fa = FA + 4 * p;
    int on = fa[0] & 1, kind = (s8)o[0x95], f = -1, held = 0;
    int old = (fa[2] & 0x80) ? fa[2] & 15 : -1;
    if (on) {
        if ((fa[0] & 2) && kind == 6 && (S32(o, 0xB4) || S32(o, 0xB8))) {
            int a = fa[1], spd = S32(o, 0xE4) >> 6;
            S32(o, 0xB4) = (spd * SIN[a]) >> 8;
            S32(o, 0xB8) = -((spd * SIN[(a + 64) & 255]) >> 8);
            f = F16[a];
            /* keep the facing until the stick is a few steps into the next one, so it doesn't flicker on a border */
            if (old >= 0 && f != old && (F16[(a + 3) & 255] == old || F16[(a - 3) & 255] == old)) f = old;
            held = 1;
        } else if (old >= 0 && f8_of(old) == o[0xF8]) {
            f = old;                       /* standing: keep the last facing unless the game turned him (attack, hit) */
        } else {
            f = o[0xF8] << 1;
        }
        fa[2] = 0x80 | f;
    } else {
        fa[2] = 0;
    }
    u8 hid = *(volatile u8 *)(HERO + HERO_SZ * p + 0x19F);
    u32 cur = U32(o, 0x24);
    int ours = cur >= TBL16 && cur < TBL16_END;
    if (on && (kind == 4 || kind == 6)) {
        int f8 = f8_of(f), d, flip;
        u32 t;
        if (hid == 0 && (f & 1)) { t = TBL16; d = f < 8 ? (f - 1) >> 1 : (15 - f) >> 1; flip = f > 8; }
        else { t = U32(o, 0x88); d = DIR5[f8]; flip = f8 > 4; }
        if (cur != *(const u32 *)(t + 4 * kind) + 16 * d) show(o, t, kind, d);
        if (flip) o[0xDF] |= 0x10; else o[0xDF] &= ~0x10;
        if (held) o[0xF8] = f8;            /* attacks and skills go the way he faces */
    } else if (ours) {
        int f8 = o[0xF8];
        show(o, U32(o, 0x88), kind, DIR5[f8]);
        if (f8 > 4) o[0xDF] |= 0x10; else o[0xDF] &= ~0x10;
    }
}

int hero_upd(u8 *o)
{
    int r = UPDATE(o);
    turn(o);
    return r;
}
