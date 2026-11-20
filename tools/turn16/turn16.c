/* Smooth 360-degree walking (Jordan, 2026-11-11: "re draw the gaps in between the animation frames"; v209, 2026-11-20:
 * "give all characters and enemies 360 points of motion instead of 16 like you did to the traps" -> 32 facings, 11.25
 * degrees apart on the ground, three in-between pictures per gap made by gen32.py).
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

#define FA        ((volatile u8 *)0x0203FFC0)   /* [4 * player]: +0 bit0 on, bit1 stick held; +1 angle; +2 facing32 | 0x80 */
#define IDX32     ((const u32 *)0x09000000)     /* gen32.py: 8 x {game's table, ours 1/4, ours 1/2, ours 3/4}; kinds 4 and 6: 4 gaps each */
#define OURS_LO   0x09000000u                   /* pictures live past the 16 MB game, ROM 0x1000000 on (the page grows the file) */
#define OURS_HI   0x0A000000u
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
    /* keep the walk step and its timer: a facing change must not restart the step, or the legs stop while he moves (v189) */
    if (fr && fr < frames_of(U32(o, 0x24))) SETFRAME(o, fr);
}

/* the game's facing (0-7) nearest facing32 f (attacks and skills go that way) */
static int f8_of(int f) { return ((f + 2) >> 2) & 7; }

/* step facing r toward t: 2 a tick (1 for the last step), a turn of more than lim / 32 snaps */
static int turn_to(int r, int t, int lim)
{
    int d = (t - r) & 31, n = d < 16 ? d : 32 - d;
    if (!d) return r;
    if (n > lim) return t;
    n = n > 2 ? 2 : n;
    return (r + (d < 16 ? n : -n)) & 31;
}

static void turn(u8 *o)
{
    u32 p = o[0x96];
    if (p > 1) return;
    volatile u8 *fa = FA + 4 * p;
    int on = fa[0] & 1, kind = (s8)o[0x95], f = -1, held = 0, want = 0;
    int old = (fa[2] & 0x80) ? fa[2] & 31 : -1;
    if (on) {
        if ((fa[0] & 2) && kind == 6 && (S32(o, 0xB4) || S32(o, 0xB8))) {
            int a = fa[1], spd = S32(o, 0xE4) >> 6;
            S32(o, 0xB4) = (spd * SIN[a]) >> 8;
            S32(o, 0xB8) = -((spd * SIN[(a + 64) & 255]) >> 8);
            want = F32[a];
            /* keep the facing until the stick is a few steps into the next one, so it doesn't flicker on a border */
            if (old >= 0 && want != old && (F32[(a + 3) & 255] == old || F32[(a - 3) & 255] == old)) want = old;
            /* the picture swings round toward the stick (2 facings a tick) instead of snapping; a reversal still snaps */
            f = old >= 0 ? turn_to(old, want, 12) : want;
            held = 1;
        } else if (old >= 0 && f8_of(old) == o[0xF8]) {
            f = old;                       /* standing: keep the last facing unless the game turned him (attack, hit) */
        } else {
            f = o[0xF8] << 2;
        }
        fa[2] = 0x80 | f;
    } else {
        fa[2] = 0;
    }
    u32 cur = U32(o, 0x24), gt = U32(o, 0x88);
    const u32 *ix = 0;
    int ours = cur >= OURS_LO && cur < OURS_HI;
    for (int h = 0; h < 8; h++) if (IDX32[4 * h] == gt) { ix = IDX32 + 4 * h; break; }
    if (on && (kind == 4 || kind == 6)) {
        int d, flip;
        u32 t;
        if (ix && (f & 3)) {
            int m = f < 16 ? f : 32 - f;
            t = ix[m & 3]; d = m >> 2; flip = f > 16;
        } else {
            int f8 = f8_of(f);
            t = gt; d = DIR5[f8]; flip = f8 > 4;
        }
        if (cur != *(const u32 *)(t + 4 * kind) + 16 * d) show(o, t, kind, d);
        if (flip) o[0xDF] |= 0x10; else o[0xDF] &= ~0x10;
        if (held) o[0xF8] = f8_of(want);   /* attacks and skills go the way the stick points */
    } else if (ours) {
        int f8 = o[0xF8];
        show(o, gt, kind, DIR5[f8]);
        if (f8 > 4) o[0xDF] |= 0x10; else o[0xDF] &= ~0x10;
    }
}

#define ENEMIES   (*(u8 *volatile *)0x03002420)

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


/* ---- enemies in 32 facings (v177 16, v209 32) ----
   Enemy species s (object + 0x61) shows anim sets from 0x08056820 + 24 s (0 walk, 1 stand) through 0x08001AC4(object,
   set + 16 * DIR5[facing]). gen32.py's data (past 16 MB) holds 12 in-between entries per walk and stand set (entry
   3 * gap + sub, sub 0-2 = 1/4, 1/2, 3/4 of the way to the next drawn direction); the word at 0x09000080 points at
   SP[82][2] = ours for (species, walk / stand), 0 = none.
   Each tick, for every awake enemy showing a walk or stand picture:
   - turning: the facing it shows (0-31, kept per enemy in ESIDE) swings toward the game's facing, 2 a tick (1 for the
     last step), so it turns through the in-between pictures instead of snapping (more than 90 degrees still snaps);
   - chasing (FA[3] bit 0, set by the page): walking within 22.5 degrees of the hero, its velocity turns to point straight
     at him (same speed), and it faces that exact way. */
#define ET        0x08056820u
#define ENX       (*(const u32 *)0x09000080)
#define ESIDE     ((volatile u32 *)0x0203FB00)   /* 32 x {object, shown facing | 0x100}: free EWRAM (checked in play) */
#define ESIDE_N   32
#define TICKS     (*(volatile u32 *)0x030041A4)
#define SETSET(o, e) ((fn4)0x08001AC5)((int)(o), (int)(e), 0, 0)

static int q64(int n, int d)                /* (n * 64) / d for 0 <= n <= d, without a divide call */
{
    int q = 0;
    for (int b = 32; b; b >>= 1) if ((q + b) * d <= n * 64) q += b;
    if (q < 64 && (q + 1) * d <= n * 64) q++;
    return q;
}

static int atan256(int x, int y)            /* screen angle of (x, y up), 0 = up, clockwise, 256 steps */
{
    int ax = x < 0 ? -x : x, ay = y < 0 ? -y : y, a;
    if (!ax && !ay) return 0;
    if (ax <= ay) a = ATN[q64(ax, ay)]; else a = 64 - ATN[q64(ay, ax)];
    if (y < 0) a = 128 - a;
    if (x < 0) a = -a;
    return a & 255;
}

static volatile u32 *eside(u8 *e)
{
    volatile u32 *free = 0;
    for (int i = 0; i < ESIDE_N; i++) {
        if (ESIDE[2 * i] == (u32)e) return ESIDE + 2 * i;
        if (!free && !ESIDE[2 * i]) free = ESIDE + 2 * i;
    }
    if (!free) { free = ESIDE + 2 * (TICKS & (ESIDE_N - 1)); }
    free[0] = (u32)e; free[1] = 0;
    return free;
}

static const u8 GAP3[12] = { 1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15 };   /* our entry -> facing 1-15 on the right side */

static void enemies(u8 *hero)
{
    u32 sp = ENX;
    if (sp < 0x09000000u || sp >= 0x0A000000u) return;
    int hx = S32(hero, 0xAC) >> 16, hy = S32(hero, 0xB0) >> 16, chase = FA[3] & 1;
    for (u8 *e = ENEMIES; e; e = *(u8 **)e) {
        u32 f = U32(e, 0xE8);
        if ((f & 0x801000) != 0x1000 || !(f & 0x10040400)) continue;
        int s = e[0x61];
        if (s >= 82) continue;
        u32 cur = U32(e, 0x24), p = 0, a = 0;
        int k, r, flip = e[0xDF] & 0x10;
        for (k = 0; k < 2; k++) {
            p = *(const u32 *)(ET + 24 * s + 4 * k); a = ((const u32 *)sp)[2 * s + k];
            if (!a) continue;
            if (cur >= p && cur < p + 0x50) { int d = (cur - p) >> 4; r = flip ? (32 - 4 * d) & 31 : 4 * d; break; }
            if (cur >= a && cur < a + 0xC0) { int m = GAP3[(cur - a) >> 4]; r = flip ? 32 - m : m; break; }
        }
        if (k == 2) continue;
        volatile u32 *sd = eside(e);
        if (sd[1] & 0x100) r = sd[1] & 31;              /* what we showed last tick (the game may have snapped it) */
        int t = e[0xF8] << 2;
        if (chase && k == 0 && (S32(e, 0xB4) || S32(e, 0xB8))) {
            int vx = S32(e, 0xB4), vy = S32(e, 0xB8);
            int at = atan256((hx - (S32(e, 0xAC) >> 16)) * 64, -((hy - (S32(e, 0xB0) >> 16)) * 64));
            int av = atan256(vx >> 4, -(vy >> 4)), dl = (s8)(at - av);
            if (dl >= -16 && dl <= 16) {
                int c = SIN[(dl + 64) & 255], sn = SIN[dl & 255], x = vx >> 4, y = -vy >> 4;
                S32(e, 0xB4) = ((x * c) >> 10) + ((y * sn) >> 10);
                S32(e, 0xB8) = -(((y * c) >> 10) - ((x * sn) >> 10));
                t = F32[at];
            }
        }
        r = turn_to(r, t, 8);
        sd[1] = 0x100 | r;
        u32 want; int wf;
        if (r & 3) { int m = r < 16 ? r : 32 - r; want = a + 16 * (3 * (m >> 2) + (m & 3) - 1); wf = r > 16; }
        else { int f8 = r >> 2; want = p + 16 * DIR5[f8]; wf = f8 > 4; }
        if (want != cur) {
            int fr = e[0x23];
            SETSET(e, want);
            if (fr && fr < frames_of(want)) SETFRAME(e, fr);
        }
        if (wf) e[0xDF] |= 0x10; else e[0xDF] &= ~0x10;
    }
}

/* v179 (one engine, P2 games): the page's stick changes for player 0 go through a small queue stamped with a game tick,
   so both games of a local P2 game apply each change on the same tick (the two games are not always on the same tick when
   the page writes). 8 entries of {u32 tick; u8 fa0; u8 angle; u16 0} at EWRAM 0x0203FC00; page count 0x0203FC41, applied
   count 0x0203FC40. A 1-player game writes FA directly and leaves the queue empty. */
#define FQ        ((volatile u8 *)0x0203FC00)
static void fa_queue(void)
{
    u8 n = FQ[0x40];
    while (n != FQ[0x41]) {
        volatile u8 *e = FQ + 8 * (n & 7);
        if ((s32)(TICKS - *(volatile u32 *)e) < 0) break;
        FA[0] = e[4];
        if (e[4] & 2) FA[1] = e[5];
        n++;
    }
    FQ[0x40] = n;
}

int hero_upd(u8 *o)
{
    if (o[0x96] == 0) fa_queue();
    int r = UPDATE(o);
    turn(o);
    if (o[0x96] == 0) { stun_notes(); enemies(o); }
    return r;
}

