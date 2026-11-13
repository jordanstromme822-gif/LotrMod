/* Smooth 360-degree walking test (Jordan, 2026-11-11: "re draw the gaps in between the animation frames").
 *
 * With the Play Room's free-angle joystick on, the page writes the stick's screen angle into EWRAM and points the
 * hero's update (object + 0x14, the game's 0x080236B9) at hero_upd below. After the game's own update has worked
 * out its 8-direction walk, hero_upd:
 *   - turns the walk velocity (+0xB4 / +0xB8, read by the move step 0x080023C0 that runs next) to the stick's exact
 *     angle at the same speed (+0xE4), so collision and everything after it stay the game's own;
 *   - picks one of 16 facings and shows an in-between picture (walk and stand) for the odd ones, for every hero
 *     (v176; v170-v175 Frodo only). The pictures are a separate data block past the 16 MB game at 0x09000000
 *     (tools/turn16/gen16all.py; the page grows the built game for it), starting with 8 pairs {game's anim table,
 *     ours}; ours is laid out like the game's own table (+0x88), so 0x08000D58 loads them like any other picture.
 * It also turns Frodo's crossbow traps (tools/orcslots/crossbow.c) through 16 facings: each tick a crossbow of this
 * player gets a 16-picture anim set (pictures: xb16.bin at 0x08094400, tools/turn16/xb16.py) and turns one facing
 * a tick toward the nearest foe it would shoot, so it swings round smoothly instead of snapping when it fires.
 * Placed at 0x0809F000 (free) by the page. Runs in the engines' interpreter; nothing here is compiled natively.
 */
typedef unsigned char u8; typedef signed char s8; typedef unsigned short u16; typedef unsigned int u32; typedef int s32;
#include "tables.h"

#define FA        ((volatile u8 *)0x0203FFC0)   /* [4 * player]: +0 bit0 on, bit1 stick held; +1 angle; +2 facing16 | 0x80 */
#define IDX16     ((const u32 *)0x09000000)     /* hero16.bin (gen16all.py): 8 x {game's table, ours}; kinds 4 and 6 have 4 in-between facings */
#define OURS_LO   0x09000000u                   /* pictures live past the 16 MB game, ROM 0x1000000 on (the page grows the file) */
#define OURS_HI   0x09200000u
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
    u32 cur = U32(o, 0x24), gt = U32(o, 0x88), t16 = 0;
    int ours = cur >= OURS_LO && cur < OURS_HI;
    for (int h = 0; h < 8; h++) if (IDX16[2 * h] == gt) { t16 = IDX16[2 * h + 1]; break; }
    if (on && (kind == 4 || kind == 6)) {
        int f8 = f8_of(f), d, flip;
        u32 t;
        if (t16 && (f & 1)) { t = t16; d = f < 8 ? (f - 1) >> 1 : (15 - f) >> 1; flip = f > 8; }
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

/* ---- crossbow traps in 16 facings ---- */
#define XB_UPD    0x08082231u                   /* crossbow.c xb_update (object + 0x14 of a live crossbow) */
#define XB_ANIM8  0x08084408u                   /* crossbow.c xb_anim: the 8-way set */
#define XB_TILES  0x08094400u                   /* xb16.bin: frames 0-7 = facings 0, 2, .. 14; 8-15 = facings 1, 3, .. 15 */
#define XBL       ((u8 *volatile *)0x0203F360)  /* [player * 3 + k] * 2 words: object, then timer / shots / cd */
#define XN        ((volatile u8 *)0x0203F390)
#define ENEMIES   (*(u8 *volatile *)0x03002420)
#define SETANIMSET(o, s) ((fn4)0x08001AC5)((int)(o), (int)(s), 0, 0)
#define ANGLE(dx, dy)    ((fn4)0x080329B5)(dx, dy, 0, 0)

#define REC(n) 0x01, 0x00, 0x10, 0x10, (n) * 0x80 & 0xFF, (n) * 0x80 >> 8, 0x80, 0x00, \
               0xF3, 0x0D, 0xF8, 0x06, 0x01, 0x00, 0xF8, 0xEB, 0x07, 0x00
#define OFS(n) (0x20 + (n) * 0x12) & 0xFF, (0x20 + (n) * 0x12) >> 8
__attribute__((aligned(4))) const u8 xb16_frames[] = {            /* crossbow.c's header and records, 16 frames */
    0x20, 0x10, 0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x01, 0x00, 0x01,
    OFS(0), OFS(1), OFS(2), OFS(3), OFS(4), OFS(5), OFS(6), OFS(7),
    OFS(8), OFS(9), OFS(10), OFS(11), OFS(12), OFS(13), OFS(14), OFS(15),
    REC(0), REC(1), REC(2), REC(3), REC(4), REC(5), REC(6), REC(7),
    REC(8), REC(9), REC(10), REC(11), REC(12), REC(13), REC(14), REC(15)
};
const u32 xb16_anim[4] = { XB_TILES, (u32)xb16_frames, 0, 1 };

static int frame_of(int f) { return (f & 1) ? 8 + (f >> 1) : f >> 1; }
static int facing_of(int fr) { return fr < 8 ? fr << 1 : ((fr - 8) << 1) | 1; }

/* the foe crossbow.c's nearest() would shoot: awake, not under Ring's Persuasion, within a screen */
static u8 *xb_target(u8 *o)
{
    int ox = S32(o, 0xAC) >> 16, oy = S32(o, 0xB0) >> 16, bd = 0x7FFFFFFF;
    u8 *best = 0;
    for (u8 *e = ENEMIES; e; e = *(u8 **)e) {
        u32 f = U32(e, 0xE8);
        if ((f & 0x801000) != 0x1000 || !(f & 0x10040400)) continue;
        u8 st = e[0x62];
        if (st == 0x11 || st == 0x15 || st == 4 || (e[0x69] & 0x40)) continue;
        int dx = (S32(e, 0xAC) >> 16) - ox, dy = (S32(e, 0xB0) >> 16) - oy;
        if (dx < -120 || dx > 120 || dy < -80 || dy > 80) continue;
        int d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = e; }
    }
    return best;
}

static void xb_turn(u32 p)
{
    int n = XN[p];
    if (n > 3) return;
    for (int k = 0; k < n; k++) {
        u8 *o = XBL[(p * 3 + k) * 2];
        if ((u32)o < 0x02000000u || (u32)o >= 0x02040000u || U32(o, 0x14) != XB_UPD || o[0x62] == 4) continue;
        int fr = o[0x23];
        if (U32(o, 0x24) == XB_ANIM8) {          /* new crossbow: same picture from the 16-way set */
            SETANIMSET(o, xb16_anim);
            SETFRAME(o, fr & 7);
            o[0x20] = 0xFF;
        }
        if (U32(o, 0x24) != (u32)xb16_anim) continue;
        u8 *t = xb_target(o);
        if (!t) continue;
        int a = ANGLE(S32(t, 0xAC) - S32(o, 0xAC), S32(t, 0xB0) - S32(o, 0xB0)) & 31;
        int want = ((a + 1) >> 1) & 15;   /* 32 angles -> 16 facings */
        int cur = facing_of(o[0x23] & 15);
        if (cur == want) continue;
        int step = ((want - cur) & 15) < 8 ? 1 : -1;   /* the short way round, one facing a tick */
        SETFRAME(o, frame_of((cur + step) & 15));
        o[0x20] = 0xFF;
    }
}

/* ---- Knife Toss stun (Jordan, 2026-11-11: "Frodo's stuns from knife throw don't show an animation") ----
   knife.c stunned with 0x08008A6C, which is a different status (state 0x12): the foe walked on and the stars it
   asked for (0x0801C33C with flag 8) went away at once, because they only stay while the foe is in state 0x1A.
   The game's own stun (0x08011730, 0x080411F4) is: state 0x1A, timer + 0x50, + 0x64 |= 2, then the stars.
   Set at the moment of the hit it didn't hold: the hit's own reaction (state 6) comes after and replaced it (tested in
   the Play Room page). So kt_stun (knife.c's STUN points here: same code size, nothing in the Orc Head code moves; fixed
   address 0x0809FF01, link.ld) only notes the foe, and the hero's update (hero_upd) stuns it 2 ticks later, puts
   the stars on and holds the stun for its time. Two notes at EWRAM 0x0203FFC8 (next to the free-angle mailbox): foe, Frodo, ticks, wait. */
typedef int (*fn7)(int, int, int, int, int, int, int);
typedef struct { u8 *t; u8 *h; u16 n; u8 wait, pad; } stunnote;   /* pad: stars put on */
#define SN ((volatile stunnote *)0x0203FFC8)

static int stunnable(u8 *t)
{
    u8 st = t[0x62];
    if (!t || (U32(t, 0xE8) & 0x801040) != 0x1000 || !(U32(t, 0xE8) & 0x10040400)) return 0;
    if (*(volatile short *)(t + 0x5A) <= 0) return 0;
    return !(st == 0x11 || st == 0x15 || st == 4 || st == 0x1B || st == 0x13 || t[0x63] == 0x2F);
}

__attribute__((section(".text.kt_stun"))) int kt_stun(u8 *t, int n)
{
    u8 *h = 0;
    h = *(u8 **)(HERO);                                /* player 1's hero object (the solo game's Frodo) */
    int k = (SN[0].t == t || !SN[0].t) ? 0 : 1;
    SN[k].t = t; SN[k].h = h; SN[k].n = n; SN[k].wait = 2; SN[k].pad = 0;
    return 1;
}

static void stun_notes(void)
{
    for (int k = 0; k < 2; k++) {
        u8 *t = SN[k].t;
        if (!t) continue;
        if (SN[k].wait) { SN[k].wait--; continue; }
        if ((u32)t < 0x02000000u || (u32)t >= 0x02040000u || !stunnable(t) || !SN[k].n) { SN[k].t = 0; continue; }
        if (SN[k].pad == 0) {                         /* first tick: the stars, on their own timer (flag 0x10, not 8: */
            SN[k].pad = 1;                            /* with 8 they go as soon as the foe leaves state 0x1A) */
            ((fn7)0x0801C33D)((int)SN[k].h, (int)t, SN[k].n, 0xC, 8, 0, 0x10);
        }
        /* the foe's own update can put it back to walking (state 7) the next tick, so hold it in state 0x1A each tick */
        if (t[0x62] != 0x1A) { t[0x62] = 0x1A; t[0x64] |= 2; }
        S32(t, 0x50) = SN[k].n;
        SN[k].n--;
    }
}

int hero_upd(u8 *o)
{
    int r = UPDATE(o);
    turn(o);
    if (o[0x96] <= 1 && *(volatile u8 *)(HERO + HERO_SZ * o[0x96] + 0x19F) == 0) xb_turn(o[0x96]);
    if (o[0x96] == 0) stun_notes();
    return r;
}

