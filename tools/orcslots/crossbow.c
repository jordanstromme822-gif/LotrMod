/* Frodo's crossbows (Jordan, 2026-11-09): his Snare skill places a small crossbow on the ground instead of a trap.
   Same Spirit cost and damage table as Snare (5 + 3 / level: 8 at level 1, 20 at level 5). A crossbow turns to the
   nearest foe within a GBA screen of it (240 x 160 around it) and shoots a bolt at it once a second, 10 bolts, then
   breaks; it also breaks after 10 seconds + 3 per level above 1. Frodo keeps 1 crossbow (2 from level 3, 3 at
   level 5); placing one more breaks the oldest. Crossbows have no hit points and nothing can hit them.
   Bolts are the game's own arrows (shot as if Frodo fired them), so they look and fly like Legolas's. They take the
   arrows in Frodo's arrow slot (ASLOT[p][0], see orcslots.c), one per shot: the arrow's picture and trail, and its
   damage stats (Damage, Impaling, Fire and Poison Damage), Extra Projectiles and Armor Piercing. With the slot
   empty they are plain bolts. Damage goes through the game's skill damage routine (like Knife Toss and Snare). */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef signed char s8; typedef short s16;
typedef int (*fn4)(int, int, int, int);

#define HERO       0x03003C00u
#define HERO_SZ    0x1ACu
#define FLAGS      (*(volatile u32 *)0x03004144)
#define LEVEL      (*(volatile u32 *)0x03004174)
#define LINKED     (FLAGS & 0x20)
#define ENEMIES    (*(u8 *volatile *)0x03002420)
#define ASLOT      ((volatile u32 (*)[2])0x0203F2A0)
#define ALV        ((volatile u8 *)0x0203F340)
#define NOARROW    0xFFFFFFFFu
#define ARMOR(t)   (*(const u8 *)(0x08057518 + (t) * 20 + 0xC))

#define SNARE(h)          ((fn4)0x080455C1)((int)(h), 0, 0, 0)
#define SETANIMSET(o, s)  ((fn4)0x08001AC5)((int)(o), (int)(s), 0, 0)
#define SETANIM(o, a)     ((fn4)0x08000DE9)((int)(o), a, 0, 0)
#define SKILLVAL(p,s,t,l) ((fn4)0x08043765)(p, s, t, l)
#define ANGLE(dx, dy)     ((fn4)0x080329B5)(dx, dy, 0, 0)
#define ARROW(h, a)       ((fn4)0x080337C9)((int)(h), a, 1, 0)
#define HIT(h, t, d)      ((fn4)0x08010381)((int)(h), (int)(t), d, 0)
#define HITOK(h, t)       ((fn4)0x08011A89)((int)(h), (int)(t), 0, 0)
#define SOUND(n)          ((fn4)0x08046EED)(n, 0, 0, 0)
#define SOUND2(n, h)      ((fn4)0x08046FA1)(n, h, 0, 0)
#define ITEMSTATS(it,sl,p,r) ((fn4)0x0802DB91)((int)(it), sl, p, r)

#define I(o, off)  (*(volatile int *)((u8 *)(o) + (off)))
#define U(o, off)  (*(volatile u32 *)((u8 *)(o) + (off)))

typedef struct { u8 *o; u16 timer; u8 shots, cd; } xbent;
#define XB   ((volatile xbent (*)[3])0x0203F360)   /* [player][3], oldest first */
#define XN   ((volatile u8 *)0x0203F390)           /* [player]: crossbows in the list */
#define XLV  (*(volatile u32 *)0x0203F394)         /* level the list belongs to */
#define TICKS 30
#define SHOTS 10
#define RELOAD TICKS                                /* one bolt a second */

static int is_arrow(u32 w) { return (w & 0xF) == 7; }
static int is_regen(u32 w) { return is_arrow(w) && (w & 0x800000); }
static u32 with_count(u32 w, int n) { return (w & 0xFF00FFFFu) | ((u32)(n & 0xFF) << 16); }

void xb_nop(void) {}
void xb_update(u8 *o);

/* the anim set: 8 directions (0 up, then clockwise), one 16x16 picture each, uncompressed, OBJ palette 3 (the
   palette the game gives Snare's trap; the same in every level). Header and hitbox are Snare's. */
extern const u8 xb_tiles[1024];
#define REC(n) 0x01, 0x00, 0x10, 0x10, (n) * 0x80 & 0xFF, (n) * 0x80 >> 8, 0x80, 0x00, \
               0xF3, 0x0D, 0xF8, 0x06, 0x01, 0x00, 0xF8, 0xEB, 0x07, 0x00
__attribute__((aligned(4))) const u8 xb_frames[] = {
    0x20, 0x10, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x01, 0x00, 0x01,
    0x10, 0x00, 0x22, 0x00, 0x34, 0x00, 0x46, 0x00, 0x58, 0x00, 0x6A, 0x00, 0x7C, 0x00, 0x8E, 0x00,
    REC(0), REC(1), REC(2), REC(3), REC(4), REC(5), REC(6), REC(7)
};
const u32 xb_anim[4] = { (u32)xb_tiles, (u32)xb_frames, 0, 1 };

static void kill(u8 *o)
{
    o[0x62] = 4;
    U(o, 0xE8) = (U(o, 0xE8) & ~1u) | 0x82;
}

static int alive(volatile xbent *e)
{
    u8 *o = e->o;
    return o && U(o, 0x14) == (u32)xb_update && o[0x62] != 4;
}

static void drop(int p, int k)
{
    int n = XN[p];
    for (int i = k; i < n - 1; i++) XB[p][i] = XB[p][i + 1];
    if (n) XN[p] = n - 1;
}

static void tidy(int p)
{
    if (XLV != LEVEL) { XLV = LEVEL; XN[0] = XN[1] = 0; }
    for (int k = XN[p] - 1; k >= 0; k--) if (!alive(&XB[p][k])) drop(p, k);
}

static void brk(int p, int k)
{
    u8 *o = XB[p][k].o;
    drop(p, k);
    kill(o);
    SOUND(7);
}

static int level_of(int p) { return *(volatile u8 *)(HERO + p * HERO_SZ + 0x171); }

/* the skill handler (Frodo's skill table, skill 1) */
int xb_cast(u8 *h)
{
    u8 *o = (u8 *)SNARE(h);           /* the game's own trap object: position, flags, palette, set-trap sound */
    if (!o) return 0;
    h[0x9A]--;                        /* the game's trap count stays 0: the skill never runs out of traps */
    int p = h[0x96];
    if (p > 1) return (int)o;
    U(o, 0x14) = (u32)xb_update;
    U(o, 0x18) = (u32)xb_nop;         /* foes walking over it set nothing off */
    SETANIMSET(o, xb_anim);
    /* on the ground a step in front of Frodo, facing his way (the trap's spot is the point of his throwing frame,
       which some of his pictures don't have) */
    static const s8 fx[8] = {0, 10, 14, 10, 0, -10, -14, -10}, fy[8] = {-9, -7, 0, 7, 10, 7, 0, -7};
    int f = h[0xF8] & 7, x = I(h, 0xAC) + (fx[f] << 16), y = I(h, 0xB0) + (fy[f] << 16);
    I(o, 0xA4) = x; I(o, 0xAC) = x; I(o, 0xCC) = x;
    I(o, 0xA8) = y; I(o, 0xB0) = y; I(o, 0xD0) = y;
    SETANIM(o, f);
    tidy(p);
    int L = level_of(p), max = L >= 5 ? 3 : L >= 3 ? 2 : 1;
    for (int k = XN[p] - 1; k >= 0; k--) if (XB[p][k].o == o) drop(p, k);
    while (XN[p] >= max) brk(p, 0);
    int n = XN[p];
    XB[p][n].o = o;
    XB[p][n].timer = (10 + 3 * (L > 1 ? L - 1 : 0)) * TICKS;
    XB[p][n].shots = SHOTS;
    XB[p][n].cd = TICKS / 3;
    XN[p] = n + 1;
    return (int)o;
}

/* nearest live foe within a screen of the crossbow */
static u8 *nearest(u8 *o)
{
    int ox = I(o, 0xAC) >> 16, oy = I(o, 0xB0) >> 16, bd = 0x7FFFFFFF;
    u8 *best = 0;
    for (u8 *e = ENEMIES; e; e = *(u8 **)e) {
        u32 f = U(e, 0xE8);
        if ((f & 0x801000) != 0x1000 || !(f & 0x10040400)) continue;
        u8 s = e[0x62];
        if (s == 0x11 || s == 0x15 || s == 4) continue;
        int dx = (I(e, 0xAC) >> 16) - ox, dy = (I(e, 0xB0) >> 16) - oy;
        if (dx < -120 || dx > 120 || dy < -80 || dy > 80) continue;
        int d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = e; }
    }
    return best;
}

/* a bolt hits something (the knife's touch, with the bolt's damage and armor piercing) */
void xb_bolt_touch(u8 *b, u8 *t)
{
    static const u8 snd[10] = {0x14, 0x15, 0x16, 0x17, 0x18, 0x1A, 0x19, 0x1A, 0x1B, 0x1C};
    if (!(U(t, 0xE8) & 0x10040400)) return;
    u8 *h = *(u8 **)(b + 0xC);
    int ok = 1;
    if ((u8)(t[0x61] - 0x1D) <= 1 && t[0x62] != 0xE && t[0x62] != 8) ok = HITOK(h, t) & 0xFF;
    if (ok) {
        int d = *(volatile u16 *)(b + 0x88);
        if (b[0x8A]) d += ARMOR(t[0x61]);
        HIT(h, t, d);
    }
    b[0x62] = 4;
    s8 a = (s8)b[0x93];
    if (a >= 0 && a <= 9) *(volatile s16 *)(b + 0x8E) = SOUND2(snd[a], *(volatile s16 *)(b + 0x8E));
    else SOUND(7);
    U(b, 0xE8) &= ~4u;
}

static void shoot(u8 *o, u8 *h, int a, int p, u32 aw, int dmg, int ap)
{
    volatile u32 *it = (volatile u32 *)(HERO + p * HERO_SZ + 0x3C);
    u32 w1 = it[1], w2 = it[2];
    it[1] = NOARROW;                  /* the arrow's trail, not the weapon's */
    it[2] = aw;                       /* the game puts the worn quiver's arrow type on the arrow */
    u8 *b = (u8 *)ARROW(h, a & 31);
    it[1] = w1; it[2] = w2;
    if (!b) return;
    int x = I(o, 0xAC), y = I(o, 0xB0) - (4 << 16);
    I(b, 0xA4) = x; I(b, 0xAC) = x; I(b, 0xCC) = x;
    I(b, 0xA8) = y; I(b, 0xB0) = y; I(b, 0xD0) = y;
    U(b, 0x18) = (u32)xb_bolt_touch;
    *(volatile u16 *)(b + 0x88) = dmg;
    b[0x8A] = ap;
    I(b, 0x50) = 30;
}

static void fire(u8 *o, u8 *h, u8 *t, int p)
{
    int L = level_of(p);
    int a = ANGLE(I(t, 0xAC) - I(o, 0xAC), I(t, 0xB0) - I(o, 0xB0)) & 31;
    SETANIM(o, ((a + 2) >> 2) & 7);
    u32 aw = (!LINKED || ALV[p] == 1) ? ASLOT[p][0] : NOARROW;
    int n = is_arrow(aw) ? (aw >> 16) & 0xFF : 0;
    if (!n) aw = NOARROW;
    volatile s16 *st = (volatile s16 *)(HERO + p * HERO_SZ + 0xA4);
    int dmg = SKILLVAL(p, 1, 0, L) + st[1], extra = 0, ap = 0;   /* + Frodo's own Impaling Damage */
    if (n) {
        s16 b[51];
        for (int k = 0; k < 51; k++) b[k] = st[k];
        ITEMSTATS(aw, 2, p, 0);
        dmg += (st[1] - b[1]) + (st[2] - b[2]) + (st[3] - b[3]) + (st[5] - b[5]);
        extra = st[47] - b[47];
        ap = st[50] - b[50] > 0;
        ITEMSTATS(aw, 2, p, 1);
        ASLOT[p][0] = (n > 1 || is_regen(aw)) ? with_count(aw, n - 1) : NOARROW;
    }
    if (dmg < 1) dmg = 1;
    if (extra < 0) extra = 0;
    if (extra > 2) extra = 2;
    for (int k = 0; k <= extra; k++) shoot(o, h, a + 2 * k - extra, p, aw, dmg, ap);
}

void xb_update(u8 *o)
{
    u8 *h = *(u8 **)(o + 0xC);
    if (h[0x62] == 0x2D) { kill(o); return; }
    int p = h[0x96], k;
    if (p > 1) { kill(o); return; }
    tidy(p);
    for (k = 0; k < XN[p] && XB[p][k].o != o; k++) ;
    if (k == XN[p]) { kill(o); return; }
    volatile xbent *e = &XB[p][k];
    if (e->timer) e->timer--;
    if (!e->timer) { brk(p, k); return; }
    if (e->cd) { e->cd--; return; }
    u8 *t = nearest(o);
    if (!t) return;
    fire(o, h, t, p);
    e->cd = RELOAD;
    if (!--e->shots) brk(p, k);
}
