/* Frodo's Knife Toss (Jordan, 2026-11-09): no damage gain per level (the skill table's per-level steps are 0, so
   8 damage at every level, see tools/orcslots.py BYTES). Every hit stuns the foe for half a second (the game's own
   stun, with its stars). From level 2 the knife bounces on to the nearest foe within 64 px of the one it hit that it
   hasn't hit yet: level L hits up to L foes. Each hit does 1/5 less: 100, 80, 60, 40, 20 %.
   Foes under Ring's Persuasion (charmed: +0x69 bit 0x40) are never hit or bounced to; the knife flies through them.
   The game's knife object is kept (picture, speed, sound); kt_cast only gives it our touch. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef signed char s8; typedef short s16;
typedef int (*fn4)(int, int, int, int);
typedef int (*fn7)(int, int, int, int, int, int, int);

#define KNIFE(h)          ((fn4)0x080203BD)((int)(h), 0, 0, 0)   /* the game's Knife Toss handler: returns the knife */
#define KTOUCH(k, t)      ((fn4)0x080169B5)((int)(k), (int)(t), 0, 0)
#define HIT(h, t, d)      ((fn4)0x08010381)((int)(h), (int)(t), d, 0)
#define HITOK(h, t)       ((fn4)0x08011A89)((int)(h), (int)(t), 0, 0)
#define STUN(t, n)        ((fn4)0x0809FF01)((int)(t), n, 0, 0)   /* the game's stun (state 0x1A), tools/turn16/turn16.c kt_stun */
#define STARS(h, t, n)    ((fn7)0x0801C33D)((int)(h), (int)(t), n, 0xC, 8, 0, 8)
#define SOUND(n)          ((fn4)0x08046EED)(n, 0, 0, 0)
#define ANGLE(dx, dy)     ((fn4)0x080329B5)(dx, dy, 0, 0)
#define FMUL(a, b)        ((fn4)0x0803288D)(a, b, 0, 0)
#define SETGFX(o, g, d)   ((fn4)0x08000D59)((int)(o), 0x0806F2DC, g, d)
#define ENEMIES    (*(u8 *volatile *)0x03002420)
#define HERO       0x03003C00u
#define HERO_SZ    0x1ACu

#define I(o, off)  (*(volatile int *)((u8 *)(o) + (off)))
#define U(o, off)  (*(volatile u32 *)((u8 *)(o) + (off)))
#define HP(o)      (*(volatile s16 *)((u8 *)(o) + 0x5A))

#define RANGE 64
#define STUN_T 15                                   /* half a second (30 game ticks a second) */

typedef struct { u8 *k; u8 *hit[5]; u8 *tgt; s16 yoff; u8 n, pad; } ktent;
#define KT   ((volatile ktent *)0x0203F400)         /* 8 knives in flight (0x0203F400-0x0203F4FF) */
#define KTN  8

void kt_touch(u8 *k, u8 *t);
void kt_update(u8 *k);

static int ours(u8 *k) { return k && U(k, 0x18) == (u32)kt_touch && k[0x62] != 4; }

static volatile ktent *find(u8 *k)
{
    for (int i = 0; i < KTN; i++) if (KT[i].k == k) return &KT[i];
    return 0;
}

/* the skill handler (Frodo's skill table, skill 0) */
int kt_cast(u8 *h)
{
    u8 *k = (u8 *)KNIFE(h);
    if (!k) return 0;
    volatile ktent *e = find(k);
    for (int i = 0; !e && i < KTN; i++) if (!ours(KT[i].k)) e = &KT[i];
    if (!e) e = &KT[0];
    U(k, 0x18) = (u32)kt_touch;
    U(k, 0x14) = (u32)kt_update;
    e->k = k;
    e->n = 0;
    e->tgt = 0;
    return (int)k;
}

static int charmed(u8 *t) { return t[0x69] & 0x40; }

static int awake_foe(u8 *e)
{
    u32 f = U(e, 0xE8);
    if ((f & 0x801000) != 0x1000 || !(f & 0x10040400)) return 0;
    u8 s = e[0x62];
    return s != 0x11 && s != 0x15 && s != 4 && HP(e) > 0 && !charmed(e);
}

static u8 *next(u8 *t, volatile ktent *e)
{
    int tx = I(t, 0xAC) >> 16, ty = I(t, 0xB0) >> 16, bd = RANGE * RANGE + 1;
    u8 *best = 0;
    for (u8 *o = ENEMIES; o; o = *(u8 **)o) {
        if (o == t || !awake_foe(o)) continue;
        int seen = 0;
        for (int i = 0; i < e->n; i++) if (e->hit[i] == o) seen = 1;
        if (seen) continue;
        int dx = (I(o, 0xAC) >> 16) - tx, dy = (I(o, 0xB0) >> 16) - ty, d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = o; }
    }
    return best;
}

/* point the knife along (dx, dy), as the game's projectile spawner aims it (0x08043D74) */
static void aim(u8 *k, int dx, int dy)
{
    int a = ANGLE(dx, dy) & 31;
    if (a == k[0x8C] && I(k, 0xB4) | I(k, 0xB8)) return;
    int f = *(const u8 *)(0x0806F129 + a), g = k[0xF8];
    k[0x8C] = a;
    I(k, 0xB4) = FMUL(*(const int *)(0x082821D0 + a * 8), 0x48000);
    I(k, 0xB8) = FMUL(*(const int *)(0x082821D4 + a * 8), 0x48000);
    if (f == g) return;
    k[0xF8] = f;
    if (f > 4) k[0xDF] |= 0x10; else k[0xDF] &= ~0x10;
    SETGFX(k, 1, *(const s8 *)(0x08050418 + f));
}

/* the knife's update: the game's (flight time, Frodo's knife lock), then a bounced knife homes in on its foe */
void kt_update(u8 *k)
{
    ((fn4)0x08020471)((int)k, 0, 0, 0);
    if (k[0x62] == 4) return;
    volatile ktent *e = find(k);
    if (!e || !e->tgt) return;
    u8 *t = e->tgt;
    if (!awake_foe(t)) { e->tgt = 0; return; }
    int dx = I(t, 0xAC) - I(k, 0xAC), dy = I(t, 0xB0) + (e->yoff << 16) - I(k, 0xB0);
    /* the game's collision pass doesn't touch a knife against a second foe, so a bounced knife hits here */
    if (dx > -(8 << 16) && dx < (8 << 16) && dy > -(8 << 16) && dy < (8 << 16)) { e->tgt = 0; kt_touch(k, t); return; }
    aim(k, dx, dy);
}

void kt_touch(u8 *k, u8 *t)
{
    if (!(U(t, 0xE8) & 0x10040400)) return;
    if (charmed(t)) return;                          /* flies through */
    volatile ktent *e = find(k);
    if (!e) { KTOUCH(k, t); return; }
    for (int i = 0; i < e->n; i++) if (e->hit[i] == t) return;
    u8 *h = *(u8 **)(k + 0xC);
    int ok = 1;
    if ((u8)(t[0x61] - 0x1D) <= 1 && t[0x62] != 0xE && t[0x62] != 8) ok = HITOK(h, t) & 0xFF;
    int n = e->n;
    if (ok) {
        int d = (*(volatile u16 *)(k + 0x88) * (5 - n) * 205) >> 10;   /* x (5 - n) / 5 */
        HIT(h, t, d < 1 ? 1 : d);
        if (!(U(t, 0xE8) & 0x4000) && HP(t) > 0 && t[0x62] != 4) {
            STUN(t, STUN_T);
            STARS(h, t, STUN_T);
        }
    }
    e->hit[n] = t;
    e->n = ++n;
    int p = h[0x96], L = p < 4 ? *(volatile u8 *)(HERO + p * HERO_SZ + 0x170) : 1;
    u8 *nt = n < L && n < 5 ? next(t, e) : 0;
    SOUND(7);
    if (nt) {
        e->tgt = nt;
        e->yoff = (I(k, 0xB0) - I(t, 0xB0)) >> 16;     /* the knife flies at the same height above the feet */
        if (I(k, 0x50) < 30) I(k, 0x50) = 30;
        aim(k, I(nt, 0xAC) - I(k, 0xAC), I(nt, 0xB0) + (e->yoff << 16) - I(k, 0xB0));
        return;
    }
    k[0x62] = 4;
    U(k, 0xE8) &= ~4u;
}
