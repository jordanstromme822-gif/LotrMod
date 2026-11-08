/* Orc Heads: 4 slots under the Backpack grid, and Orc Head tiers (Jordan, 2026-11-08).
 *
 * Every Orc Head carries a roll in the top half of its item word (the game ignores that half
 * for unique items): bits 15-14 tier (0 normal, 1 magic, 2 rare), bits 13-12 the difficulty
 * table it was rolled on, bits 11-0 a seed its bonuses are worked out from. 0xFFFF is an Orc
 * Head from before tiers. Heads give their bonuses only from the 4 slots.
 * Built for thumbv4t and placed at 0x0807F000 (freed French text bank) by tools/orcslots.py.
 */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef volatile u16 vu16;

#define HERO       0x03003C00u
#define HERO_SZ    0x1ACu
#define LOCAL_P    (*(volatile u8 *)0x03003F59)
#define KEYS(p)    (*(volatile u16 *)(0x03004094u + 2u * (p)))
#define UI         (*(u8 *volatile *)0x03001FE0)
#define FLAGS      (*(volatile u32 *)0x03004144)
#define LEVEL      (*(volatile u32 *)0x03004174)
#define COUNT      ((volatile u8 *)0x0203FFE0)
#define QUIET      (*(volatile u8 *)0x0203FFE4)   /* skip the game's next error sound */
#define CODE       ((volatile u16 (*)[4])0x0203FF00) /* [player][slot]: the heads in the slots */
#define SAVED      ((volatile u16 (*)[4])0x0203F280) /* [save slot][slot]: the slot heads kept in the save file header */
#define CONF       ((volatile u16 (*)[4])0x0203FF38) /* 2-player: heads whose bonuses are on the hero */
#define CONFV      ((volatile u8 *)0x0203FF58)       /* 2-player: CONF[p] is in use */
#define SENT       (*(volatile u8 *)0x0203FF5C)       /* 2-player: our heads were sent */
#define SEED       (*(volatile u32 *)0x0203FF60)
#define APPL       ((volatile u16 (*)[4])0x0203FE40) /* heads whose bonuses are on each hero right now */
#define APPN       ((volatile u8 *)0x0203FE60)
#define OAM_COUNT  (*(volatile u8 *)0x03004220)
#define BG1CNT     (*(vu16 *)0x0400000A)
#define ORC_LO     0x17FEu
#define FIRST      20           /* cursor values 20..23 are our slots */
#define LINKED     (FLAGS & 0x20)
#define SLOT_HDR   0x03005630u  /* the 3 save slot headers in RAM, 0x70 bytes each */

typedef int (*fn4)(int, int, int, int);
typedef int (*fn5)(int, int, int, int, int);
typedef int (*fn6)(int, int, int, int, int, int);
#define AC24(p, rem)          ((fn4)0x0802AC25)(p, rem, 0, 0)
#define DDC4(st, v, p)        ((fn4)0x0802DDC5)(16, st, p, v)
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
#define TEXT(id)              ((const char *)((fn4)0x08047A69)(id, 0, 0, 0))
#define MENUOPT(o, s)         ((fn4)0x0802C5BD)(o, s, 0, 0)
#define MENU_A()              ((fn4)0x0802C659)(0, 0, 0, 0)
#define GAMEDESC(c)           ((fn4)0x0802CFFD)(c, 0, 0, 0)
#define NAME(b, it, n)        ((fn4)0x0802B065)((int)(b), it, n, 0)
#define ITEMDESC(b,p,it,x,y,t) ((fn6)0x0802C47D)((int)(b), p, it, (int)(x), (int)(y), (int)(t))
#define GENITEM(a,b,c,d)      ((fn4)0x0803A77D)(a, b, c, d)
#define RAND(lo, hi)          ((fn4)0x0803A4BD)(lo, hi, 0, 0)
#define SPAWN(x,y,k,it,t)     ((fn5)0x0802EFE9)(x, y, k, it, t)
#define EE_READ(b, n, d)      ((fn4)0x0803CF11)(b, n, (int)(d), 0)
#define EE_WRITE(b, n, s)     ((fn4)0x0803CF41)(b, n, (int)(s), 0)
#define SLOT_WRITE(s, sl)     ((fn4)0x0803CE25)(s, sl, 0, 0)
#define SLOT_READ(d, sl)      ((fn4)0x0803CDE9)(d, sl, 0, 0)
#define LINK_SEND(t,a,b,c)    ((fn4)0x0803FDF1)(t, a, b, c)
#define GP_FRAME(a,b,c,d)     ((fn4)0x080391C5)(a, b, c, d)
#define MENU       ((volatile int *)0x030041B0)   /* [0] game state, [2] carve flag, [3] menu choice, [4] substate, [5] yes/no */
#define ROWS       ((volatile u8 *)0x03001FE8)
#define SETTINGS   (*(volatile u32 *)0x03005820)  /* bit 0: Fast Discard, bits 5-6 difficulty */
#define DIFF       ((SETTINGS >> 5) & 3)
#define DROPTBL    ((const signed char *)0x08057F78)
#define PAGE    (*(volatile u8 *)0x0203F000)
#define PREADY  (*(volatile u8 *)0x0203F001)          /* the page has put the stored page 2 into PBUF */
#define PGEN    (*(volatile u16 *)0x0203F002)         /* bumped on every page-2 write: the page saves it */
#define UREQ    (*(volatile u8 *)0x0203F004)          /* page asks: write UBUF to slot USLOT of page UPAGE */
#define UPAGE   (*(volatile u8 *)0x0203F005)
#define USLOT   (*(volatile u8 *)0x0203F006)
#define SESSPG  (*(volatile u8 *)0x0203F007)          /* page of the slot this play session belongs to */
#define FLIPREQ (*(volatile u8 *)0x0203F008)          /* page's Page button */
#define SESSV   (*(volatile u8 *)0x0203F009)
#define ULOCK   (*(volatile u8 *)0x0203F00A)          /* Undo: the save lock (and its page) from before the undone save */
#define ULOCKPG (*(volatile u8 *)0x0203F00B)
#define PBUF    ((volatile u8 *)0x0203F010)           /* 4 x 0x70: page 2 headers, as in RAM */
#define PHEAD   ((volatile u16 (*)[4])0x0203F1D0)     /* page 2 slot heads (like SAVED) */
#define UBUF    ((volatile u8 *)0x0203F200)           /* 0x70 header + 8 bytes of heads + 2 arrow slot words */
#define HDRS    0x03005630
#define GSTATE  (*(volatile u8 *)0x030041B0)
#define SLOTSUB (*(volatile u8 *)0x030041C0)
#define SAVEMODE (*(volatile u8 *)0x030041B4)
#define DUPELOCK (*(volatile u8 *)0x0203FFF0)
#define READ_ALL()            ((fn4)0x0803CCBD)(0, 0, 0, 0)
#define SLOT_UPD()            ((fn4)0x080306ED)(0, 0, 0, 0)
#define PAUSE_UPD()           ((fn4)0x080397FD)(0, 0, 0, 0)

/* Slot heads of save slot k: bytes 8 + 8k of the save file header (RAM copy 0x030057F0, unused 0xFF in the game's
   template), written with the header checksum the game checks at boot. v117-v121 kept them in EEPROM
   blocks 0x32-0x34, which are the first 3 blocks of save slot 4: saving any game there broke slot 4 (Jordan's Aragorn). */
#define SAVEHDR    ((volatile u8 *)0x030057F0)
#define LINK_MSG   4            /* link message type the game never uses: one player's 4 slot heads */

extern const u8 orc_tiles[384];
extern const u16 orc_pal[16];
extern const u16 slot_pal[16];
static u16 red(u16 v) { return (v >> 12) == 2 ? (v & 0x0FFF) | 0x6000 : v; }

static u32 *inv(int p) { return (u32 *)(HERO + p * HERO_SZ + 0x3C); }
static int is_orc(u32 it) { return (it & 0xFF0F) == 0x170E; }
static int cnt(int p) { int n = COUNT[p]; return n > 4 ? 4 : n; }
static u32 item_of(u16 code) { return ((u32)code << 16) | ORC_LO; }
/* a head from before tiers (0xFFFF), or an unreadable code: tier 3 or difficulty table 3 */
static int is_old(u16 code) { return (code >> 14) == 3 || ((code >> 12) & 3) == 3; }
#define EE_KEY 0xC000           /* EEPROM holds code ^ EE_KEY, so never-written bytes (0x00 or 0xFF) read as old heads */

/* ---------------- rolls ---------------- */
static u32 mix(u32 *s) { u32 x = *s; x ^= x << 13; x ^= x >> 17; x ^= x << 5; *s = x; return x; }
static int pick(u32 *s, int lo, int hi) { return lo + (int)(((mix(s) >> 16) * (u32)(hi - lo + 1)) >> 16); }

/* the bonuses of a head: up to 3 (stat, value) pairs. Stats: 17-21 attributes, 22 Hit Points,
   23 Spirit Points, 24 % Speed, 28 Spirit per hit, 29 Hit Points Regen, 30 Spirit Regen,
   31 % Extra Gems, 32 % Extra Treasure */
static int decode(u16 code, u8 *st, u8 *v)
{
    int tier = code >> 14, tab = (code >> 12) & 3;
    u32 s = (code & 0xFFF) * 2654435761u + 0x9E3779B9u + tier * 77 + tab * 1013;
    if (is_old(code)) { tier = 0; tab = 0; }
    mix(&s); mix(&s);
    if (tier == 0) {                                   /* normal: points to a random attribute */
        st[0] = pick(&s, 17, 21);
        v[0] = tab == 0 ? pick(&s, 1, 5) : pick(&s, 3, 7);
        return 1;
    }
    if (tier == 1) {                                   /* magic */
        if (tab < 2) {
            if (pick(&s, 0, 1)) { st[0] = 30; v[0] = pick(&s, 3, 5); }
            else { st[0] = 29; v[0] = pick(&s, 1, 5); }
        } else {
            int k = pick(&s, 0, 2);
            if (k == 0) { st[0] = 29; v[0] = pick(&s, 3, 5); }
            else if (k == 1) { st[0] = 30; v[0] = pick(&s, 3, 7); }
            else { st[0] = 28; v[0] = pick(&s, 15, 20); }
        }
        return 1;
    }
    int n = 0;                                         /* rare: (attribute or find) and (HP or SP or speed) */
    if (pick(&s, 0, 1)) { st[0] = pick(&s, 17, 21); v[0] = pick(&s, 5, 10); n = 1; }
    else { v[0] = v[1] = pick(&s, 5, 15); st[0] = 32; st[1] = 31; n = 2; }
    int k = pick(&s, 0, 2);
    if (k == 0) { st[n] = 22; v[n] = pick(&s, 25, 40); }
    else if (k == 1) { st[n] = 23; v[n] = pick(&s, 25, 40); }
    else { st[n] = 24; v[n] = 5; }
    return n + 1;
}

static void apply(int p, u16 code, int sign)
{
    u8 st[3], v[3];
    int n = decode(code, st, v);
    for (int i = 0; i < n; i++) DDC4(st[i], sign * v[i], p);
}

static u16 local_code(int tier, int tab)      /* a fresh roll that doesn't touch the game's random numbers */
{
    u32 s = SEED ^ (*(vu16 *)0x04000006 << 16) ^ *(volatile u32 *)0x03001F18;
    SEED = mix(&s);
    return (u16)((tier << 14) | (tab << 12) | (SEED & 0xFFF));
}

/* old Orc Heads (from before tiers) become normal heads with a fresh roll (single player only:
   in a 2-player game each GBA must see the same items) */
static void convert_old(int p)
{
    int tab = DIFF ? 1 : 0;
    u32 *it = inv(p);
    for (int j = 8; j < 16; j++)
        if (is_orc(it[j]) && is_old(it[j] >> 16)) it[j] = item_of(local_code(0, tab));
    for (int i = 0; i < cnt(p); i++)
        if (is_old(CODE[p][i])) CODE[p][i] = local_code(0, tab);
}

/* ---------------- regenerating quivers (Jordan, 2026-11-08) ----------------
   Arrows keep their count in item byte 2 (the game rolls 10-40 and deletes a quiver at 0).
   3% of dropped quivers regenerate: 1 arrow a second, starting 1 second after the last shot,
   up to the count they dropped with; they stay at 0 instead of being deleted.
   Every other bit of an arrow word is used by the game (bits 4-7 are the rune), so a regenerating
   quiver off the hero is written with byte 2 = 0x80 | max (it is full: it regenerates in the pack
   too). The equipped one holds its live count in byte 2 like any quiver, and its max is QMAX[p].
   Saves and the hero sent to the other GBA in 2-player games get the pack form (full), so a loaded
   or joined game starts with the quiver full on both GBAs. */
#define QMAX    ((volatile u8 *)0x0203FE80)   /* [player]: max of the equipped regenerating quiver, 0 = none */
#define QIDLE   ((volatile u8 *)0x0203FE82)   /* [player]: ticks since the last shot or refill */
#define DEBTN   ((volatile u8 *)0x0203FEA0)   /* [player]: arrows missing from the quiver last taken off */
#define QWORD   ((volatile u32 *)0x0203FEA4)  /* [player]: the equipped regenerating quiver's word */
#define DEBTW   ((volatile u32 *)0x0203FEAC)  /* [player]: that quiver's word off the hero */
#define DEBTT   ((volatile u32 *)0x0203FEB4)  /* [player]: QCLK when it was taken off */
#define QCLK    (*(volatile u32 *)0x0203FEBC) /* gameplay ticks */
#define TICKS   30                     /* the game logic runs 30 ticks a second */
#define USE_ARROW(p)   ((fn4)0x0802C411)(p, 0, 0, 0)
#define SAME_ITEM(a,b) ((fn4)0x0802EB09)(a, b, 0, 0)
#define HFLAGS(p)      (*(volatile u16 *)(HERO + (p) * HERO_SZ + 0x18C))
#define ARROWS_ON      0x400                  /* hero flag: shooting from the equipped quiver */

static int is_arrow(u32 w) { return (w & 0xF) == 7; }
static int is_regen(u32 w) { return is_arrow(w) && (w & 0x800000); }
static u32 with_count(u32 w, int n) { return (w & 0xFF00FFFFu) | ((u32)(n & 0xFF) << 16); }

/* ---------------- arrow slots (Legolas; Jordan, 2026-11-08) ----------------
   Two slots under the Orc Head slots that hold only arrows. Picked-up arrows that don't go on the worn quiver
   fill them before the backpack; the page's L puts on the next quiver (worn -> slots -> worn). The EEPROM has
   no room left, so the slots of each save slot are kept by the page on the player's account (AKEEP). */
#define ASLOT   ((volatile u32 (*)[2])0x0203F2A0)    /* [player][2]: the arrows in the 2 slots (not an arrow word = empty) */
#define ASAVED  ((volatile u32 (*)[2])0x0203F2B0)    /* [save slot][2]: of the page of slots shown (like SAVED) */
#define AKEEP   ((volatile u32 (*)[4][2])0x0203F2D0) /* [page][save slot][2]: kept by the page */
#define AGEN    (*(volatile u16 *)0x0203F310)        /* bumped on every AKEEP write: the page saves it */
#define AREADY  (*(volatile u8 *)0x0203F312)         /* the page has put the stored AKEEP in */
#define ACYC    (*(volatile u8 *)0x0203F313)         /* the page's L button (Legolas, in play): next quiver */
#define NOARROW 0xFFFFFFFFu
#define AFIRST  24                                  /* cursor values 24, 25 are the arrow slots */
#define HERO_ID(p) (*(volatile u8 *)(HERO + (p) * HERO_SZ + 0x19F))
#define AE68(it, p)            ((fn4)0x0802AE69)((int)(it), p, 0, 0)
#define ITEMSTATS(it, sl, p, r) ((fn4)0x0802DB91)((int)(it), sl, p, r)
#define WEAPONFLAGS(p)         ((fn4)0x0802D8E1)(p, 0, 0, 0)
static int is_leg(int p) { return p < 2 && HERO_ID(p) == 1; }
static void a_norm(int p) { for (int k = 0; k < 2; k++) if (!is_arrow(ASLOT[p][k])) ASLOT[p][k] = NOARROW; }

/* keep QMAX/QWORD in step with what the hero wears (called every gameplay and Backpack frame) */
static void q_sync(int p)
{
    u32 *it = inv(p), w = it[2];
    if (QMAX[p] && w != QWORD[p]) {                    /* taken off (or swapped): back to the pack form */
        int mx = QMAX[p], cur = (QWORD[p] >> 16) & 0xFF;
        u32 off = with_count(QWORD[p], 0x80 | mx);
        for (int j = 8; j < 16; j++)
            if (it[j] == QWORD[p]) { it[j] = off; break; }
        for (int k = 0; k < 2; k++)
            if (ASLOT[p][k] == QWORD[p]) { ASLOT[p][k] = off; break; }
        DEBTW[p] = off; DEBTN[p] = cur < mx ? mx - cur : 0; DEBTT[p] = QCLK;
        QMAX[p] = 0;
    }
    if (!QMAX[p] && is_regen(w)) {                     /* just put on */
        int mx = (w >> 16) & 0x3F, cur = mx;
        if (w == DEBTW[p] && DEBTN[p]) {               /* the same quiver again: what it has refilled since */
            int miss = DEBTN[p]; volatile int t = (int)(QCLK - DEBTT[p]);
            while (t >= TICKS && miss) { t -= TICKS; miss--; }
            cur = mx - miss;
            DEBTN[p] = 0;
        }
        w = with_count(w, cur);
        it[2] = w;
        QMAX[p] = mx; QWORD[p] = w; QIDLE[p] = 0;
    }
    if (QMAX[p]) {
        if ((w >> 16) & 0xFF) HFLAGS(p) |= ARROWS_ON; else HFLAGS(p) &= ~(ARROWS_ON | 0x20);
    }
}

static void q_frame(int p)
{
    q_sync(p);
    if (!QMAX[p]) return;
    u32 *it = inv(p), w = it[2];
    int cur = (w >> 16) & 0xFF;
    if (cur >= QMAX[p]) { QIDLE[p] = 0; return; }
    if (++QIDLE[p] < TICKS) return;
    QIDLE[p] = 0;
    w = with_count(w, cur + 1);
    it[2] = w; QWORD[p] = w;
    HFLAGS(p) |= ARROWS_ON;
}

/* a shot: the game's 4 calls that use up an arrow */
void arrow_wrap(int p)
{
    if (!QMAX[p]) { USE_ARROW(p); return; }
    u32 *it = inv(p), w = it[2];
    int cur = (w >> 16) & 0xFF;
    if (cur) cur--;
    w = with_count(w, cur);
    it[2] = w; QWORD[p] = w; QIDLE[p] = 0;
    if (!cur) HFLAGS(p) &= ~(ARROWS_ON | 0x20);         /* empty: plain shots, the quiver stays */
    *(volatile u32 *)(0x03003F70 + p * 0x7C + 0x70) |= 0x4000;   /* the game's arrow count label */
    *(volatile u8 *)(0x03003F70 + p * 0x7C + 0x79) = 0x14;
}

/* picking up arrows adds them to a matching quiver: never to or from a regenerating one */
int same_wrap(u32 a, u32 b)
{
    if (is_regen(a) || is_regen(b)) return 0;
    for (int p = 0; p < 2; p++) if (QMAX[p] && a == inv(p)[2]) return 0;
    return SAME_ITEM(a, b);
}

/* the page's L: the worn quiver goes to the end of the arrow slots and the first one is put on, with the game's own
   item stat steps (take off, put on, weapon flags) */
static void a_cycle(int p)
{
    u32 *it = inv(p);
    q_sync(p);
    a_norm(p);
    u32 w0 = it[2], n0 = w0, n1 = ASLOT[p][0], n2 = ASLOT[p][1];
    if ((!is_arrow(w0) && (w0 & 0xF) != 0xF) || (!is_arrow(n1) && !is_arrow(n2))) { SOUND(5); return; }
    for (int k = 0; k < 2; k++) { u32 t = n0; n0 = n1; n1 = n2; n2 = t; if (is_arrow(n0)) break; }
    ASLOT[p][0] = is_arrow(n1) ? n1 : NOARROW;
    ASLOT[p][1] = is_arrow(n2) ? n2 : NOARROW;
    if (is_arrow(w0)) ITEMSTATS(w0, 2, p, 1);
    it[2] = n0;
    ITEMSTATS(n0, 2, p, 0);
    WEAPONFLAGS(p);
    q_sync(p);
    if ((it[2] >> 16) & 0xFF) HFLAGS(p) |= ARROWS_ON;
    *(volatile u32 *)(0x03003F70 + p * 0x7C + 0x70) |= 0x4000;   /* the game's arrow count label */
    *(volatile u8 *)(0x03003F70 + p * 0x7C + 0x79) = 0x14;
    SOUND(2);
}

/* picking up arrows (0x0802ACE8 -> 0x0802AE68): with no worn quiver the game puts them on, a matching worn quiver
   takes them as before; otherwise a matching arrow slot, then an empty arrow slot, then the backpack */
int apick_wrap(u32 *item, int p)
{
    u32 w = *item, *it = inv(p);
    if (LINKED || !is_leg(p) || !is_arrow(w) || !is_arrow(it[2]) || same_wrap(it[2], w)) return AE68(item, p);
    a_norm(p);
    int n = (w >> 16) & 0xFF;
    if (!is_regen(w))
        for (int k = 0; k < 2 && n; k++) {
            u32 a = ASLOT[p][k];
            if (!is_arrow(a) || !same_wrap(a, w)) continue;
            int c = (a >> 16) & 0xFF, m = 99 - c;
            if (m <= 0) continue;
            if (m > n) m = n;
            ASLOT[p][k] = with_count(a, c + m);
            n -= m;
        }
    w = with_count(w, n); *item = w;
    if (!n) return 1;
    for (int k = 0; k < 2; k++)
        if (!is_arrow(ASLOT[p][k])) { ASLOT[p][k] = w; *item = with_count(w, 0); return 1; }
    return AE68(item, p);
}

/* is this word a regenerating quiver, and its live count and max */
static int q_info(u32 w, int *cur)
{
    if (!is_arrow(w)) return 0;
    if (is_regen(w)) { *cur = (w >> 16) & 0x3F; return *cur; }
    for (int p = 0; p < 2; p++)
        if (QMAX[p] && w == inv(p)[2]) { *cur = (w >> 16) & 0xFF; return QMAX[p]; }
    return 0;
}

/* what is on each hero is tracked, so taking bonuses off is always exact */
static void set_applied(int p, volatile u16 *codes, int n)
{
    for (int i = 0; i < APPN[p] && i < 4; i++) apply(p, APPL[p][i], -1);
    for (int i = 0; i < n; i++) { APPL[p][i] = codes[i]; apply(p, codes[i], 1); }
    APPN[p] = n;
}

/* ---- stats: the game recomputes stats from base + items on load and level up; add the slots ---- */
void ac24_wrap(int p, int rem)
{
    AC24(p, rem);
    if (rem) { set_applied(p, 0, 0); return; }
    APPN[p] = 0;                                       /* the game has just rebuilt the stats */
    if (!LINKED) { convert_old(p); set_applied(p, CODE[p], cnt(p)); }
    else if (CONFV[p]) set_applied(p, CONF[p], cnt(p));
}

/* ---- 2-player games: every GBA sends its player's slot heads once (link message 4); recv4 (stubs.s)
   stores them on both GBAs on the same frame and the next gameplay frame puts them on. ---- */
int gp_hook(int a, int b, int c, int d)
{
    int r = GP_FRAME(a, b, c, d);
#ifdef DEBUG_SPAWN
    if (*(volatile u16 *)0x0203FE70) {
        u8 *h = *(u8 **)HERO;
        SPAWN(*(int *)(h + 0xAC) + (8 << 16), *(int *)(h + 0xB0), 84, (int)item_of(*(volatile u16 *)0x0203FE72), 0x708);
        *(volatile u16 *)0x0203FE70 = 0;
    }
    if (*(volatile u16 *)0x0203FE74) {                 /* add item word 0x0203FE78 as if picked up */
        *(volatile u32 *)0x0203FE7C = ((fn4)0x0802ACE9)(*(volatile u32 *)0x0203FE78, 0, 0, 0);
        *(volatile u16 *)0x0203FE74 = 0;
    }
#endif
    if (LINKED && !SENT) {
        int p = LOCAL_P;
        SENT = 1;
        LINK_SEND(LINK_MSG, CODE[p][0] | (CODE[p][1] << 16), CODE[p][2] | (CODE[p][3] << 16), 0);
    }
    for (int p = 0; p < 4; p++)                        /* heads that came from the other GBA: both GBAs, same frame */
        if (CONFV[p] == 2) { CONFV[p] = 1; set_applied(p, CONF[p], cnt(p)); }
    if (DUPELOCK && !SESSV) { SESSPG = PAGE; SESSV = 1; } else if (!DUPELOCK) SESSV = 0;
    if (ACYC) { ACYC = 0; if (!LINKED && is_leg(LOCAL_P)) a_cycle(LOCAL_P); }
    QCLK++;
    q_frame(0);
    if (LINKED) q_frame(1);
    return r;
}

/* ---- saves: the slot heads of save slot s live in EEPROM block 0x32 + s ---- */
static int hdr_slot(u32 h) { for (int s = 0; s < 4; s++) if (h == SLOT_HDR + s * 0x70) return s; return -1; }

void pack_c(u8 *h, int p)
{
    int n = cnt(p), s = hdr_slot((u32)h);
    h[0x4B] = (h[0x4B] & 0x1F) | (n << 5);
    if (s >= 0) for (int i = 0; i < 4; i++) SAVED[s][i] = (i < n ? CODE[p][i] : 0xFFFF) ^ EE_KEY;
    if (s >= 0 && p < 2) { a_norm(p); ASAVED[s][0] = ASLOT[p][0]; ASAVED[s][1] = ASLOT[p][1]; }
    q_sync(p);                                         /* worn regenerating quiver: packed full (header + 8 = off hand) */
    if (QMAX[p] && h[8] == (QWORD[p] & 0xFF)) h[10] = 0x80 | QMAX[p];
}

void unpack_c(const u8 *h, int p)
{
    int n = h[0x4B] >> 5, s = hdr_slot((u32)h);
    COUNT[p] = n > 4 ? 4 : n;
    for (int i = 0; i < 4; i++) CODE[p][i] = s >= 0 ? SAVED[s][i] ^ EE_KEY : 0xFFFF;
    CONFV[p] = 0;
    APPN[p] = 0;
    SENT = 0;
    if (p < 2) { QMAX[p] = 0; DEBTN[p] = 0; }          /* its quiver comes in packed: full */
    if (p < 2) { ASLOT[p][0] = s >= 0 ? ASAVED[s][0] : NOARROW; ASLOT[p][1] = s >= 0 ? ASAVED[s][1] : NOARROW; a_norm(p); }
}

/* ---- a second page of 4 save slots (Jordan, 2026-11-08: "8 in total") ----
   The EEPROM holds only 4 slots, so page 2 lives in EWRAM (PBUF) and the page keeps it on the player's account.
   With PAGE = 1 every slot read and write goes to PBUF instead of the EEPROM. R on the slot screen (free since
   nodelete) or the page's Page button flips the page and reads the 4 headers again. The page restores a saved-over
   slot through UREQ (Undo). */
static void cpy(volatile u8 *d, const volatile u8 *s, int n) { for (int i = 0; i < n; i++) d[i] = s[i]; }
static void empty_page(void)
{
    for (int i = 0; i < 4 * 0x70; i++) PBUF[i] = 0;
    for (int k = 0; k < 4; k++) {                      /* an empty slot as the game leaves it: marker 0x82, checksum 0xFF7E */
        PBUF[k * 0x70 + 0x68] = 0x82; PBUF[k * 0x70 + 0x6E] = 0x7E; PBUF[k * 0x70 + 0x6F] = 0xFF;
        for (int i = 0; i < 4; i++) PHEAD[k][i] = 0xFFFF ^ EE_KEY;
    }
    PREADY = 1; PGEN++;
}

int save_wrap(int src, int slot)
{
    if (PAGE) {
        cpy(PBUF + slot * 0x70, (const volatile u8 *)src, 0x70);
        for (int i = 0; i < 4; i++) PHEAD[slot][i] = SAVED[slot][i];
        AKEEP[1][slot][0] = ASAVED[slot][0]; AKEEP[1][slot][1] = ASAVED[slot][1]; AGEN++;
        PGEN++;
        return 0;
    }
    AKEEP[0][slot][0] = ASAVED[slot][0]; AKEEP[0][slot][1] = ASAVED[slot][1]; AGEN++;
    int r = SLOT_WRITE(src, slot);
    cpy(SAVEHDR + 8 + 8 * slot, (const volatile u8 *)SAVED[slot], 8);
    volatile u16 *hw = (volatile u16 *)SAVEHDR;        /* the game's header checksum, then all 8 header blocks */
    u16 sum = 0; hw[0x1F] = 0;
    for (int i = 0; i < 0x20; i++) sum += hw[i];
    hw[0x1F] = (u16)-sum;
    EE_WRITE(0, 8, SAVEHDR);
    return r;
}

int load_wrap(int dst, int slot)
{
    ASAVED[slot][0] = AKEEP[PAGE & 1][slot][0]; ASAVED[slot][1] = AKEEP[PAGE & 1][slot][1];
    if (PAGE) {
        if (!PREADY) empty_page();
        cpy((volatile u8 *)dst, PBUF + slot * 0x70, 0x70);
        for (int i = 0; i < 4; i++) SAVED[slot][i] = PHEAD[slot][i];
        return 0;
    }
    int r = SLOT_READ(dst, slot);
    int unset = 1;                                     /* never written (0xFF): no heads */
    for (int i = 0; i < 8; i++) if (SAVEHDR[8 + 8 * slot + i] != 0xFF) unset = 0;
    for (int i = 0; i < 4; i++)
        SAVED[slot][i] = unset ? 0xFFFF ^ EE_KEY : SAVEHDR[8 + 8 * slot + 2 * i] | SAVEHDR[9 + 8 * slot + 2 * i] << 8;
    return r;
}

static void redraw(void)
{
    for (int k = 0; k < 4; k++) {                      /* the 4 panels and hero pictures again */
        ((fn4)0x08030DA1)(k, *(volatile u8 *)0x030041BC, 0, 0);
        ((fn4)0x080311E5)(k, 0, 0, 0);
    }
}

/* A play session that has saved or loaded may only save to its own slot (tools/nodupe.py), so in save mode it
   can't look at the other page either. */
static int flip(void)
{
    if (GSTATE != 9 || SLOTSUB != 0) return 0;
    if (SAVEMODE == 1 && DUPELOCK && SESSV && SESSPG != (PAGE ^ 1)) { SOUND(5); return 0; }
    PAGE ^= 1;
    READ_ALL();
    redraw();
    SOUND(2);
    return 1;
}
void flip_r(void) { flip(); }

static void undo_apply(void)
{
    int cur = PAGE, sl = USLOT & 3;
    u16 keep[4];
    u32 akeep0 = ASAVED[sl][0], akeep1 = ASAVED[sl][1];
    for (int i = 0; i < 4; i++) keep[i] = SAVED[sl][i];
    PAGE = UPAGE & 1;
    for (int i = 0; i < 4; i++) SAVED[sl][i] = ((volatile u16 *)(UBUF + 0x70))[i];
    ASAVED[sl][0] = ((volatile u32 *)(UBUF + 0x78))[0]; ASAVED[sl][1] = ((volatile u32 *)(UBUF + 0x78))[1];
    save_wrap((int)UBUF, sl);
    PAGE = cur;
    if ((UPAGE & 1) == cur) cpy((volatile u8 *)(HDRS + sl * 0x70), UBUF, 0x70);
    else { for (int i = 0; i < 4; i++) SAVED[sl][i] = keep[i]; ASAVED[sl][0] = akeep0; ASAVED[sl][1] = akeep1; }
    DUPELOCK = ULOCK; SESSPG = ULOCKPG; SESSV = ULOCK ? 1 : 0;   /* the undone save no longer ties the session to that slot */
    if (GSTATE == 9 && (UPAGE & 1) == cur) redraw();
}

static void menu_service(void)
{
    if (FLIPREQ) { FLIPREQ = 0; flip(); }
    if (UREQ) { UREQ = 0; undo_apply(); }
}
int slot_upd(int a, int b, int c, int d) { menu_service(); return ((fn4)0x080306ED)(a, b, c, d); }
int pause_upd(int a, int b, int c, int d) { menu_service(); return ((fn4)0x080397FD)(a, b, c, d); }

/* ---- drops: on every kill, roll for a rare, then a magic, then a normal head ---- */
static const u16 ODDS[3][2][2] = {           /* [tier][hard enemy][special zone]: 1 in N kills */
    {{500, 400}, {100, 75}}, {{800, 650}, {150, 100}}, {{1500, 1200}, {500, 400}} };

void drop_c(u8 *e)
{
    int d = DIFF, type = e[0x61], lv = LEVEL;
    if (d > 2) d = 2;
    int hard = type <= 0x52 && DROPTBL[type * 8] == 45;          /* the game's "always drops" enemies */
    int zone = (d == 1 && (lv == 58 || (lv >= 6 && lv <= 13)))   /* Black Gate, Cirith Ungol */
            || (d == 2 && lv >= 99 && lv <= 107);                /* Pelennor Fields */
    for (int t = 2; t >= 0; t--) {
        if (t == 2 && d == 0) continue;                          /* no rare heads on Normal */
        if (t == 0 && d == 2) continue;                          /* no normal heads on Grueling */
        int n = ODDS[t][hard][zone];
        if (t == 2 && d == 1) n *= 2;                            /* rare heads on Hard: twice as hard */
        if (RAND(1, n) != 1) continue;
        u16 code = (u16)((t << 14) | (d << 12) | RAND(0, 4095));
        SPAWN(*(int *)(e + 0xAC), *(int *)(e + 0xB0), 84, (int)item_of(code), 0x708);
        return;
    }
}

/* the game's own item rolls never make an Orc Head any more (they come only from drop_c) */
int genitem_wrap(u32 *item, int p, int find, int type)
{
    int r = 0;
    for (int k = 0; k < 8; k++) {
        r = GENITEM((int)item, p, find, type);
        if (!is_orc(*item)) break;
    }
    if (is_arrow(*item) && RAND(1, 100) <= 3)          /* 3%: a regenerating quiver */
        *item = with_count(*item, 0x80 | (((*item >> 16) & 0xFF) > 63 ? 63 : ((*item >> 16) & 0x3F)));
    return r;
}

/* ---- names and descriptions ---- */
static char *put(char *d, const char *s) { while (*s) *d++ = *s++; *d = 0; return d; }
static char *num(char *d, int v) { if (v >= 10) { volatile int t = 0; while (v >= 10) { v -= 10; t++; } *d++ = '0' + t; } *d++ = '0' + v; *d = 0; return d; }

static const char *const TIER_NAME[3] = {"Orc Head", "Magic Orc Head", "Rare Orc Head"};
static int tier_of(u32 item) { return is_old(item >> 16) ? 0 : (int)(item >> 30); }

int name_wrap(char *buf, u32 item, int n)
{
    int qc, qm = q_info(item, &qc);
    if (qm) {                                          /* "Orcish Arrows: 7/25", in the magic colour */
        NAME(buf, with_count(item, qc), n);
        char *d = buf;
        while (*d && *d != ':') d++;
        if (*d) { d = put(d, ": "); d = num(d, qc); d = put(d, "/"); num(d, qm); }
        *(volatile u8 *)(0x03003F70 + LOCAL_P * 0x7C + 0x78) = MENU[0] == 1 ? 12 : 9;
        return (int)buf;
    }
    int r = NAME(buf, item, n);
    if (is_orc(item)) {
        int t = tier_of(item);
        put(buf, TIER_NAME[t]);
        /* the game's own name colours: yellow (normal), green (magic; its ground label green is 12), red (rare) */
        *(volatile u8 *)(0x03003F70 + LOCAL_P * 0x7C + 0x78) = t == 0 ? 3 : t == 2 ? 6 : (MENU[0] == 1 ? 12 : 9);
        return (int)buf;
    }
    return r;
}

static char *bonus_text(char *d, u16 code)
{
    u8 st[3], v[3];
    int n = decode(code, st, v);
    for (int i = 0; i < n; i++) {
        if (i) d = put(d, ", ");
        const char *nm = TEXT(330 + st[i]);
        d = put(d, "+");
        d = num(d, v[i]);
        if (*nm != '%') d = put(d, " ");
        d = put(d, nm);
    }
    return d;
}

int itemdesc_wrap(char *buf, int p, u32 item, u16 *x, u16 *y, u16 *tile)
{
    int r = ITEMDESC(buf, p, item, x, y, tile);
    int qc;
    if (q_info(item, &qc)) {
        char *d = buf;
        while (*d) d++;
        put(d, d == buf ? "Regenerates 1 arrow a second" : ", Regenerates 1 arrow a second");
        return (int)buf;
    }
    if (!is_orc(item)) return r;
    char *d = bonus_text(buf, item >> 16);
    put(d, ". Works only in an Orc Head slot (the row under your backpack).");
    return (int)buf;
}

/* ---- the slots ---- */
static void desc(int cur)
{
    int p = LOCAL_P, c = cur - FIRST;
    CLEARTEXT(1, 15, 10, 15, 10, 0);
    TEXTCOLOR(0, 3, 0);
    if (cur >= AFIRST) {                             /* an arrow slot: the game's own description */
        u32 w = ASLOT[p][cur - AFIRST];
        if (!is_arrow(w)) return;
        u16 x = 0x79, y = 0x50, tile = 0x13;
        char buf[0xC8];
        for (int i = 0; i < 0xC8; i++) buf[i] = 0;
        int r = itemdesc_wrap(buf, p, w, &x, &y, &tile);
        if (r) DRAWTEXT(tile, x, 0x68, 0x76, r, 0);
        return;
    }
    if (c >= cnt(p)) return;                         /* empty: the faded head says it all */
    u16 x = 0x79, y = 0x50, tile = 0x13;
    char buf[0xC8];
    for (int i = 0; i < 0xC8; i++) buf[i] = 0;
    ITEMDESC(buf, p, item_of(CODE[p][c]), &x, &y, &tile);  /* coloured name and "Min. Level" */
    TEXTCOLOR(0, 3, 0);
    bonus_text(buf, CODE[p][c]);
    DRAWTEXT(tile, x, 0x68, 0x76, buf, 0);
}

static int shape_of(int n) { return n >= AFIRST ? 13 + n - AFIRST : 12 + n - FIRST; }
static void place_cursor(u8 *ui, int n)
{
    int c = n - FIRST, y = 80;
    if (n >= AFIRST) { c = n - AFIRST + 1; y = 104; }   /* arrow slots: under Orc Head slots 2 and 3 */
    *(int *)(ui + 0xAC) = (120 + 30 * c) << 16;
    *(int *)(ui + 0xB0) = y << 16;
    *(u32 *)(ui + 0xE8) |= 0x80;
    ui[0x62] = n;
    CURSHAPE(shape_of(n));
}

/* ---- cursor movement (Backpack, no menu open): returns the cursor the game should go on with ---- */
int nav_c(int proposed)
{
    u8 *ui = UI;
    int old = ui[0x62], k = KEYS(LOCAL_P), n = proposed, ar = is_leg(LOCAL_P);
    if (old >= AFIRST) {                 /* arrow slots: up to Orc Head slots 2/3, down to the grid's top row */
        int c = old - AFIRST;
        if (k & 0x40) n = FIRST + 1 + c;
        else if (k & 0x80) n = 9 + c;
        else if (k & 0x30) n = AFIRST + (c ^ 1);
        else n = old;
    } else if (old >= FIRST) {
        int c = old - FIRST;
        if (k & 0x40) n = 12 + c;
        else if (k & 0x80) n = ar ? AFIRST + (c >= 2) : 8 + c;
        else if (k & 0x20) n = FIRST + ((c + 3) & 3);
        else if (k & 0x10) n = FIRST + ((c + 1) & 3);
        else n = old;
    } else if (old >= 12 && old <= 15 && (k & 0x80)) n = FIRST + old - 12;
    else if (old >= 8 && old <= 11 && (k & 0x40)) n = ar ? AFIRST + (old >= 10) : FIRST + old - 8;
    if (n < FIRST || n == old) return n;
    place_cursor(ui, n);                 /* the game then sees no change and stops */
    desc(n);
    SOUND(2);
    return n;
}

/* ---- A on one of our slots: like an equipment slot. Full: the Unequip / Discard menu. Empty: "can't" sound. ---- */
void a_c(int cur, int p)
{
    if (LINKED) { QUIET = 1; SOUND(5); return; }          /* not in 2-player games */
    if (cur >= AFIRST ? !is_arrow(ASLOT[p][cur - AFIRST]) : cur - FIRST >= cnt(p)) return;   /* empty: the game's error sound */
    QUIET = 1;
    CLEARTEXT(1, 15, 10, 15, 10, 0);
    MENU[4] = 1;
    TEXTCOLOR(0, 3, 0);
    DRAWTEXT(0x13, 0x79, 0x50, 0x76, TEXT(0x141), 0);      /* "What would you like to do with this item?" */
    MENU[3] = 0;
    ROWS[0] = 0; ROWS[1] = 1;
    MENUOPT(0, 0);                                         /* Unequip */
    MENUOPT(1, 0);                                         /* Discard */
    MENU[2] = 0;
    SOUND(3);
}

static void error_text(const char *s)
{
    SOUND(5);
    CLEARTEXT(1, 15, 10, 15, 10, 0);
    TEXTCOLOR(0, 3, 0);
    DRAWTEXT(0x13, 0x79, 0x50, 0x76, s, 0);
    MENU[4] = 8;                                           /* the game's "show a message until A or B" step */
}

static void remove_slot(int p, int c)
{
    int n = cnt(p);
    if (c >= n) return;
    for (int i = c; i < n - 1; i++) CODE[p][i] = CODE[p][i + 1];
    CODE[p][n - 1] = 0xFFFF;
    COUNT[p] = n - 1;
    set_applied(p, CODE[p], n - 1);
}

/* ---- A in the item menu ---- */
void menu_wrap(void)
{
    u8 *ui = UI;
    int cur = ui[0x62], p = LOCAL_P, sel = MENU[3], j;
    u32 *it = inv(p);
    if (cur >= AFIRST) {                                   /* an arrow slot: Unequip into the backpack, or Discard */
        int k = cur - AFIRST;
        if (sel == 0) {
            for (j = 8; j < 16 && (it[j] & 0xF) != 0xF; j++) ;
            if (j == 16) { error_text("Your backpack is full!"); return; }
            it[j] = ASLOT[p][k];
            ASLOT[p][k] = NOARROW;
            MKSPRITE(j);
        } else if (SETTINGS & 1) {
            ASLOT[p][k] = NOARROW;
        } else {
            CLEARTEXT(1, 15, 10, 15, 10, 0);
            MENU[4] = 3;
            TEXTCOLOR(0, 3, 0);
            DRAWTEXT(0x13, 0x79, 0x50, 0x76, TEXT(0x142), 0);
            MENUOPT(MENU[5], MENU[5]);
            MENUOPT(0, MENU[5]);
            return;
        }
        SOUND(3);
        MENU[4] = 2;
        return;
    }
    if (cur >= FIRST) {
        int c = cur - FIRST;
        if (sel == 0) {                                    /* Unequip: back into the backpack */
            for (j = 8; j < 16 && (it[j] & 0xF) != 0xF; j++) ;
            if (j == 16) { error_text("Your backpack is full!"); return; }
            it[j] = item_of(CODE[p][c]);
            remove_slot(p, c);
            MKSPRITE(j);
        } else if (SETTINGS & 1) {                         /* Discard with Fast Discard on */
            remove_slot(p, c);
        } else {                                           /* Discard: "Are you sure?" first, like the game */
            CLEARTEXT(1, 15, 10, 15, 10, 0);
            MENU[4] = 3;
            TEXTCOLOR(0, 3, 0);
            DRAWTEXT(0x13, 0x79, 0x50, 0x76, TEXT(0x142), 0);
            MENUOPT(MENU[5], MENU[5]);
            MENUOPT(0, MENU[5]);
            return;
        }
        SOUND(3);
        MENU[4] = 2;
        return;
    }
    if (cur >= 8 && cur < 16 && sel == 0 && is_orc(it[cur])) {   /* Equip an Orc Head: into the next free slot */
        if (LINKED) { SOUND(5); MENU[4] = 2; return; }
        int n = cnt(p);
        if (n >= 4) { error_text("All 4 Orc Head slots are full!"); return; }
        u16 code = it[cur] >> 16;
        if (is_old(code)) code = local_code(0, DIFF ? 1 : 0);
        DISCARD(cur, p);                                   /* removes it and its picture (plays a sound) */
        CODE[p][n] = code;
        COUNT[p] = n + 1;
        set_applied(p, CODE[p], n + 1);
        MENU[4] = 2;
        return;
    }
    MENU_A();
}

/* ---- "Are you sure?" Yes ---- */
void discard_wrap(int cur, int p)
{
    if (cur >= AFIRST) ASLOT[p][cur - AFIRST] = NOARROW;
    else if (cur >= FIRST) remove_slot(p, cur - FIRST);
    else DISCARD(cur, p);
}

/* ---- menu closed: description of the cursor ---- */
void desc_wrap(int cur)
{
    if (cur >= FIRST) { CURSHAPE(shape_of(cur)); desc(cur); }
    else GAMEDESC(cur);
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

/* arrow slots: blue boxes (OBJ palette 2, tiles 940-955), the arrows' pictures (palettes 4/5, tiles 960-983) or a
   faded blue quiver (palette 6, already blended with the box colour, tiles 984-995). OBJ palettes 0, 2, 4-6 are unused on this screen (the game puts its
   own back when it returns to play). */
extern const u8 arrow_tiles[3840], abox_tiles[512], aquiv_tiles[384];
extern const u16 arrow_pal[160], abox_pal[16], aquiv_pal[16];
#define OBJT(t) ((volatile u32 *)(0x06010000 + (t) * 32))
#define OBJP(n) ((volatile u32 *)(0x05000200 + (n) * 32))
static void cp32(volatile u32 *d, const u32 *s, int n) { for (int i = 0; i < n; i++) d[i] = s[i]; }
static void draw_arrows(int p)
{
    u16 a[4];
    cp32(OBJT(940), (const u32 *)abox_tiles, 128);
    cp32(OBJT(984), (const u32 *)aquiv_tiles, 96);
    cp32(OBJP(2), (const u32 *)abox_pal, 8);
    cp32(OBJP(6), (const u32 *)aquiv_pal, 8);
    for (int k = 0; k < 2; k++) {
        u32 w = ASLOT[p][k];
        int x = 150 + 30 * k, t = (w >> 8) & 0xFF, base = 984, pal = 6, fade = 0;
        if (is_arrow(w) && t < 10) {
            base = 960 + 12 * k; pal = 4 + k; fade = 0;
            cp32(OBJT(base), (const u32 *)(arrow_tiles + 384 * t), 96);
            cp32(OBJP(pal), (const u32 *)(arrow_pal + 16 * t), 8);
        }
        a[0] = 104 | (1 << 14) | fade; a[1] = x | (1 << 14); a[2] = base | (1 << 10) | (pal << 12); a[3] = 0;
        OAMADD(OAM_COUNT, a);
        a[0] = 112 | (1 << 14) | fade; a[1] = x | (2 << 14); a[2] = (base + 4) | (1 << 10) | (pal << 12);
        OAMADD(OAM_COUNT, a);
    }
    for (int k = 0; k < 2; k++) {
        a[0] = 102; a[1] = (148 + 30 * k) | (2 << 14); a[2] = 940 | (1 << 10) | (2 << 12); a[3] = 0;
        OAMADD(OAM_COUNT, a);
    }
}

#define SUBSTATE  (*(volatile u32 *)0x030041C0)
#define BG0_SAVE  ((u16 *)0x0203FF80)          /* 45 entries: the panel under the grid, as the game drew it */

void frame_hook(void)
{
    u16 *bg0 = (u16 *)0x0600F800;
    int sub = SUBSTATE;
    q_sync(LOCAL_P);
    if (bg0[10 * 32 + 15] != red(bg0[7 * 32 + 15]))          /* freshly drawn by the game: keep a copy */
        for (int r = 0; r < 3; r++)
            for (int x = 15; x < 30; x++) BG0_SAVE[r * 15 + x - 15] = bg0[(10 + r) * 32 + x];
    if (sub == 4 || sub == 5) {                          /* Carve Rune uses the space under the grid */
        for (int r = 0; r < 3; r++)
            for (int x = 15; x < 30; x++) bg0[(10 + r) * 32 + x] = BG0_SAVE[r * 15 + x - 15];
        BG1CNT = (BG1CNT & ~0x1F00) | (0x1E << 8);
        OAMFINISH();
        return;
    }
    /* BG0: copy the second grid row's boxes (tile rows 7-9) to rows 10-12, in dark red */
    for (int r = 0; r < 3; r++)
        for (int x = 15; x < 30; x++) bg0[(10 + r) * 32 + x] = red(bg0[(7 + r) * 32 + x]);
    u32 *bp = (u32 *)(0x05000000 + 6 * 32);
    const u32 *bs = (const u32 *)slot_pal;
    for (int i = 0; i < 8; i++) bp[i] = bs[i];

    /* BG1 (text): show a copy with text rows 10.. moved down to 13..18 */
    const u16 *src = (const u16 *)0x0600F000;
    u32 *dst = (u32 *)0x0600D800;
    const u32 *s32 = (const u32 *)src;
    for (int i = 0; i < 10 * 16; i++) dst[i] = s32[i];
    u8 rows[8]; int n = 0, leg = is_leg(LOCAL_P);
    for (int r = 10; r < 18; r++) rows[n++] = r;
    static const u8 order[] = {12, 11, 17, 16, 15, 14, 13};
    while (n > (leg ? 5 : 6)) {
        int drop = -1;
        for (int o = 0; o < 7 && drop < 0; o++)
            for (int i = 0; i < n; i++)
                if (rows[i] == order[o] && row_empty(src, order[o])) { drop = i; break; }
        if (drop < 0) drop = n - 1;
        for (int i = drop; i < n - 1; i++) rows[i] = rows[i + 1];
        n--;
    }
    if (leg) {                                           /* Legolas: the arrow slots take rows 13-15, so the text goes
                                                            to the bottom of the left side (rows 14-18) */
        vu16 *d16 = (vu16 *)dst;
        for (int r = 10; r < 20; r++)
            for (int x = 0; x < 32; x++) d16[r * 32 + x] = (x < 15 && r < 14) ? src[r * 32 + x] : 0;
        for (int d = 0; d < n; d++)
            for (int x = 0; x < 15; x++) d16[(14 + d) * 32 + x] = src[rows[d] * 32 + 15 + x];
    } else {
        for (int i = 10 * 16; i < 13 * 16; i++) dst[i] = 0;
        for (int d = 0; d < 6; d++) {
            u32 *o = dst + (13 + d) * 16;
            if (d < n) { const u32 *q = s32 + rows[d] * 16; for (int i = 0; i < 16; i++) o[i] = q[i]; }
            else for (int i = 0; i < 16; i++) o[i] = 0;
        }
        for (int i = 19 * 16; i < 20 * 16; i++) dst[i] = 0;
    }
    BG1CNT = (BG1CNT & ~0x1F00) | (0x1B << 8);

    /* Orc Head pictures: tiles 1000-1011, palette 7 */
    u32 *tv = (u32 *)(0x06010000 + 1000 * 32);
    const u32 *ts = (const u32 *)orc_tiles;
    for (int i = 0; i < 96; i++) tv[i] = ts[i];
    u32 *pv = (u32 *)(0x05000200 + 7 * 32);
    const u32 *ps = (const u32 *)orc_pal;
    for (int i = 0; i < 8; i++) pv[i] = ps[i];
    int p = LOCAL_P, c = cnt(p);
    /* full head in a filled slot; in an empty one the same head half see-through (the screen's own 50/50
       blend with BG0), since OBJ palettes 8-15 belong to the backpack's 8 item pictures */
    for (int k = 0; k < 4; k++) {
        u16 a[4];
        int x = 120 + 30 * k, fade = k < c ? 0 : 1 << 10;
        a[0] = 80 | (1 << 14) | fade; a[1] = x | (1 << 14); a[2] = 1000 | (1 << 10) | (7 << 12); a[3] = 0;
        OAMADD(OAM_COUNT, a);
        a[0] = 88 | (1 << 14) | fade; a[1] = x | (2 << 14); a[2] = 1004 | (1 << 10) | (7 << 12);
        OAMADD(OAM_COUNT, a);
    }
    if (leg) draw_arrows(p);
    OAMFINISH();
}

void exit_hook(void)
{
    BG1CNT = (BG1CNT & ~0x1F00) | (0x1E << 8);
    STATE_EXIT();
}
