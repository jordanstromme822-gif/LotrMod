/* Orc Head slots: 4 slots under the Backpack grid that each hold one Orc Head.
 * Orc Heads give their +1 Courage only from these slots (none from the backpack).
 * Built for thumbv4t and placed at 0x0809F000 (freed Spanish text bank) by build.py.
 */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef volatile u16 vu16;

#define HERO       0x03003C00u
#define HERO_SZ    0x1ACu
#define LOCAL_P    (*(volatile u8 *)0x03003F59)
#define KEYS(p)    (*(volatile u16 *)(0x03004094u + 2u * (p)))
#define UI         (*(u8 *volatile *)0x03001FE0)
#define FLAGS      (*(volatile u32 *)0x03004144)
#define COUNT      ((volatile u8 *)0x0203FFE0)
#define QUIET      (*(volatile u8 *)0x0203FFE4)   /* skip the game's next error sound */
#define OAM_COUNT  (*(volatile u8 *)0x03004220)
#define BG1CNT     (*(vu16 *)0x0400000A)
#define ORC        0xFFFF17FEu
#define ORC_SLOT   16           /* slot number passed to the stat routine for our slots */
#define FIRST      20           /* cursor values 20..23 are our slots */

typedef int (*fn4)(int, int, int, int);
typedef int (*fn6)(int, int, int, int, int, int);
#define DB90(it, sl, p, rem)  ((fn4)0x0802DB91)((int)(it), sl, p, rem)
#define AC24(p, rem)          ((fn4)0x0802AC25)(p, rem, 0, 0)
#define DISCARD(sl, p)        ((fn4)0x0802C08D)(sl, p, 0, 0)
#define MKSPRITE(sl)          ((fn4)0x0802E1E1)(sl, 0, 0, 0)
#define CURSHAPE(i)           ((fn4)0x0802E601)(i, 0, 0, 0)
#define SOUND(n)              ((fn4)0x08046EED)(n, 0, 0, 0)
#define CLEARTEXT(a,b,c,d,e,f) ((fn6)0x08012661)(a, b, c, d, e, f)
#define TEXTCOLOR(a,b,c)      ((fn4)0x0801D5C1)(a, b, c, 0)
#define DRAWTEXT(t,x,y,w,s,f) ((fn6)0x0801D6D1)(t, x, y, w, (int)(s), f)
#define OAMADD(i, a)          ((fn4)0x08036541)(i, (int)(a), 0, 0)
#define OAMFINISH()           ((fn4)0x080366A5)(0, 0, 0, 0)
#define STATE_EXIT()          ((fn4)0x0802E875)(0, 0, 0, 0)

extern const u8 orc_tiles[384];
extern const u16 orc_pal[16];

static u32 *inv(int p) { return (u32 *)(HERO + p * HERO_SZ + 0x3C); }
static int is_orc(u32 it) { return (it & 0xFF0F) == 0x170E; }
static int cnt(int p) { int n = COUNT[p]; return n > 4 ? 4 : n; }

/* ---- stats: the game recomputes stats from base + items; add ours ---- */
void ac24_wrap(int p, int rem)
{
    AC24(p, rem);
    for (int i = cnt(p); i > 0; i--) DB90(ORC, ORC_SLOT, p, rem);
}

/* ---- description box for our slots ---- */
static void desc(int cur)
{
    int p = LOCAL_P, c = cur - FIRST, t = 0x13;
    CLEARTEXT(1, 15, 10, 15, 10, 0);
    TEXTCOLOR(0, 3, 0);
    if (c < cnt(p)) {
        t = DRAWTEXT(t, 0x79, 0x50, 0x76, "Orc Head", 0);
        t = DRAWTEXT(t, 0x79, 0x60, 0x76, "+1 Courage while it sits in this slot. Press A to put it back in your backpack.", 0);
    } else {
        t = DRAWTEXT(t, 0x79, 0x50, 0x76, "Orc Head Slot", 0);
        t = DRAWTEXT(t, 0x79, 0x60, 0x76, "Holds one Orc Head (+1 Courage). Press A to move one here from your backpack.", 0);
    }
}

static void place_cursor(u8 *ui, int n)
{
    int c = n - FIRST;
    *(int *)(ui + 0xAC) = (120 + 30 * c) << 16;
    *(int *)(ui + 0xB0) = 80 << 16;
    *(u32 *)(ui + 0xE8) |= 0x80;
    ui[0x62] = n;
    CURSHAPE(12 + c);
}

/* ---- cursor movement (Backpack, no menu open): returns the cursor the game should go on with ---- */
int nav_c(int proposed)
{
    u8 *ui = UI;
    int old = ui[0x62], k = KEYS(LOCAL_P), n = proposed;
    if (old >= FIRST) {
        int c = old - FIRST;
        if (k & 0x40) n = 12 + c;
        else if (k & 0x80) n = 8 + c;
        else if (k & 0x20) n = FIRST + ((c + 3) & 3);
        else if (k & 0x10) n = FIRST + ((c + 1) & 3);
        else n = old;
    } else if (old >= 12 && old <= 15 && (k & 0x80)) n = FIRST + old - 12;
    else if (old >= 8 && old <= 11 && (k & 0x40)) n = FIRST + old - 8;
    if (n < FIRST || n == old) return n;
    place_cursor(ui, n);                 /* the game then sees no change and stops */
    desc(n);
    SOUND(2);
    return n;
}

/* ---- A on one of our slots ---- */
void a_c(int cur, int p)
{
    int c = cur - FIRST, n = cnt(p), j;
    u32 *it = inv(p);
    QUIET = 1;                                       /* the game's own code then plays its error sound; skip it */
    if (FLAGS & 0x20) { SOUND(5); return; }          /* not in 2-player games */
    if (c < n) {                                     /* take one out */
        for (j = 8; j < 16 && (it[j] & 0xF) != 0xF; j++) ;
        if (j == 16) { SOUND(5); return; }
        it[j] = ORC;
        COUNT[p] = n - 1;
        DB90(ORC, ORC_SLOT, p, 1);
        MKSPRITE(j);
        SOUND(2);
    } else {                                         /* put one in */
        for (j = 8; j < 16 && !is_orc(it[j]); j++) ;
        if (j == 16) { SOUND(5); return; }
        DISCARD(j, p);                               /* removes it and its picture (plays a sound) */
        COUNT[p] = n + 1;
        DB90(ORC, ORC_SLOT, p, 0);
    }
    CURSHAPE(12 + c);                                /* the discard path resets the cursor picture */
    desc(cur);
}

void sound_wrap(int n)
{
    if (QUIET) { QUIET = 0; return; }
    SOUND(n);
}

/* ---- every Backpack frame: boxes, text shift, Orc Head pictures ---- */
static int row_empty(const u16 *m, int r)
{
    const u32 *w = (const u32 *)(m + r * 32);
    for (int i = 0; i < 16; i++) if (w[i]) return 0;
    return 1;
}

#define SUBSTATE  (*(volatile u32 *)0x030041C0)
#define BG0_SAVE  ((u16 *)0x0203FF80)          /* 45 entries: the panel under the grid, as the game drew it */

void frame_hook(void)
{
    u16 *bg0 = (u16 *)0x0600F800;
    int sub = SUBSTATE;
    if (bg0[10 * 32 + 15] != bg0[7 * 32 + 15])          /* freshly drawn by the game: keep a copy */
        for (int r = 0; r < 3; r++)
            for (int x = 15; x < 30; x++) BG0_SAVE[r * 15 + x - 15] = bg0[(10 + r) * 32 + x];
    if (sub == 4 || sub == 5) {                          /* Carve Rune uses the space under the grid */
        for (int r = 0; r < 3; r++)
            for (int x = 15; x < 30; x++) bg0[(10 + r) * 32 + x] = BG0_SAVE[r * 15 + x - 15];
        BG1CNT = (BG1CNT & ~0x1F00) | (0x1E << 8);
        OAMFINISH();
        return;
    }
    /* BG0: copy the second grid row's boxes (tile rows 7-9) to rows 10-12 */
    for (int r = 0; r < 3; r++)
        for (int x = 15; x < 30; x++) bg0[(10 + r) * 32 + x] = bg0[(7 + r) * 32 + x];

    /* BG1 (text): show a copy with text rows 10.. moved down to 13..18 */
    const u16 *src = (const u16 *)0x0600F000;
    u32 *dst = (u32 *)0x0600D800;
    const u32 *s32 = (const u32 *)src;
    for (int i = 0; i < 10 * 16; i++) dst[i] = s32[i];
    u8 rows[8]; int n = 0;
    for (int r = 10; r < 18; r++) rows[n++] = r;
    static const u8 order[] = {12, 11, 17, 16, 15, 14, 13};
    while (n > 6) {
        int drop = -1;
        for (int o = 0; o < 7 && drop < 0; o++)
            for (int i = 0; i < n; i++)
                if (rows[i] == order[o] && row_empty(src, order[o])) { drop = i; break; }
        if (drop < 0) drop = n - 1;
        for (int i = drop; i < n - 1; i++) rows[i] = rows[i + 1];
        n--;
    }
    for (int i = 10 * 16; i < 13 * 16; i++) dst[i] = 0;
    for (int d = 0; d < 6; d++) {
        u32 *o = dst + (13 + d) * 16;
        if (d < n) { const u32 *q = s32 + rows[d] * 16; for (int i = 0; i < 16; i++) o[i] = q[i]; }
        else for (int i = 0; i < 16; i++) o[i] = 0;
    }
    for (int i = 19 * 16; i < 20 * 16; i++) dst[i] = 0;
    BG1CNT = (BG1CNT & ~0x1F00) | (0x1B << 8);

    /* Orc Head pictures: tiles 1000-1011, palette 7 */
    u32 *tv = (u32 *)(0x06010000 + 1000 * 32);
    const u32 *ts = (const u32 *)orc_tiles;
    for (int i = 0; i < 96; i++) tv[i] = ts[i];
    u32 *pv = (u32 *)(0x05000200 + 7 * 32);
    const u32 *ps = (const u32 *)orc_pal;
    for (int i = 0; i < 8; i++) pv[i] = ps[i];
    int p = LOCAL_P, c = cnt(p);
    for (int k = 0; k < c; k++) {
        u16 a[4];
        int x = 120 + 30 * k;
        a[0] = 80 | (1 << 14); a[1] = x | (1 << 14); a[2] = 1000 | (1 << 10) | (7 << 12); a[3] = 0;
        OAMADD(OAM_COUNT, a);
        a[0] = 88 | (1 << 14); a[1] = x | (2 << 14); a[2] = 1004 | (1 << 10) | (7 << 12);
        OAMADD(OAM_COUNT, a);
    }
    OAMFINISH();
}

void exit_hook(void)
{
    BG1CNT = (BG1CNT & ~0x1F00) | (0x1E << 8);
    STATE_EXIT();
}
