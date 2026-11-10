/* Extra sprite tiles (engine upgrade 2026-11-10): the game's sprite-tile bookkeeping,
   rewritten so it can hand out tiles 1024-2047 when the engine has them.

   A = 1 bit per tile, 1 = in use; B = tiles freed this frame (0 bits), folded into A once a
   frame so a tile is only reused after the picture that showed it is gone.
   Normal (any other emulator): A = IWRAM 0x030022D8 and B = 0x03002358, 128 bytes each,
   exactly as the game had them. Extra-tiles engine (IO 0x040000E0 reads back 0x584B):
   A = 0x030022D8 grows to 256 bytes (over the old B), and B lives in the last 256 bytes of
   the extra OBJ VRAM (0x0601FF00 = tiles 2040-2047, which stay marked as used). */
typedef unsigned int u32; typedef unsigned short u16; typedef unsigned char u8;
#define A    ((volatile u8 *)0x030022D8)
#define B_LO ((volatile u8 *)0x03002358)
#define B_HI ((volatile u8 *)0x0601FF00)
#define NXT  (*(volatile u16 *)0x030023D8)
#define FLAGS (*(volatile u32 *)0x03004144)
#define REG  (*(volatile u16 *)0x040000E0)
#define UPLOAD ((void (*)(u32, u32))(0x080498C0 | 1))
#define DIV    ((u32 (*)(u32, u32))(0x0804DC50 | 1))

static int ext(void) { return REG == 0x584B; }
static volatile u8 *bmB(void) { return ext() ? B_HI : B_LO; }
static u32 bytes(void) { return ext() ? 0x100 : 0x80; }
static void fill(volatile u8 *p, u32 v, u32 n) { for (u32 i = 0; i < n; i++) p[i] = (u8)v; }
static void setbits(volatile u8 *p, u32 t, u32 n, int on) {
    for (u32 i = t; i < t + n; i++) {
        if (on) p[i >> 3] |= (u8)(1u << (i & 7)); else p[i >> 3] &= (u8)~(1u << (i & 7));
    }
}
static void probe(void) { REG = 0x4B58; }
static void clear_all(void) {
    probe();
    NXT = 0;
    fill(A, 0, bytes());
    if (ext()) A[0xFF] = 0xFF;           /* tiles 2040-2047 hold B */
    fill(bmB(), 0xFF, bytes());
}

/* 0x08049984: once a frame, A &= B, B = all ones */
void bs_fold(void) {
    volatile u8 *b = bmB(); u32 n = bytes();
    for (u32 i = 0; i < n; i++) { A[i] &= b[i]; b[i] = 0xFF; }
}
/* 0x080499F8(mode) */
void bs_init(u32 mode) {
    if (((mode + 0xFD) & 0xFF) <= 2) {   /* bitmap video modes 3-5: only tiles 512-1023 */
        NXT = 0; probe();
        fill(A, 0xFF, 0x40); fill(A + 0x40, 0, 0x40);
        if (ext()) fill(A + 0x80, 0xFF, 0x80);
    } else clear_all();
}
/* 0x08049A54() */
void bs_reset_a(void) { DIV(NXT, 8); clear_all(); }
/* 0x08049A8C() */
void bs_reset_b(void) { clear_all(); }
/* first run of n free tiles at or after start, below the limit; 0xFFFF if none */
static u32 search(u32 start, u32 n, u32 limit) {
    u32 p = start, cand = start, run = 0;
    if (n == 0) return start;
    while (p < limit) {
        u32 b = A[p >> 3];
        if ((p & 7) == 0 && b == 0xFF) { p += 8; cand = p; run = 0; continue; }
        if ((p & 7) == 0 && b == 0 && run + 8 <= n) { run += 8; p += 8; if (run == n) return cand; continue; }
        if ((b >> (p & 7)) & 1) { p++; cand = p; run = 0; }
        else { p++; if (++run == n) return cand; }
    }
    return 0xFFFF;
}
/* 0x08049AB8(gfx, bytes): find + mark + upload, returns the first tile or 0xFFFF */
u32 bs_alloc(u32 gfx, u32 nbytes) {
    u32 n = nbytes >> 5;
    u32 start = (FLAGS & 8) ? NXT + 1u : 0u;
    u32 t = search(start, n, bytes() * 8u);
    if (t != 0xFFFF) {
        setbits(A, t & 0xFFFF, n & 0xFFFF, 1);
        if (gfx) {
            if (!(FLAGS & 8)) NXT = (u16)(NXT + n);
            UPLOAD(gfx, t & 0xFFFF);
        }
    }
    return t;
}
/* 0x08049C80(tile, count): mark used */
void bs_mark(u32 t, u32 n) { setbits(A, t & 0xFFFF, n & 0xFFFF, 1); }
/* 0x08049CCC(tile, count): free now */
void bs_free_now(u32 t, u32 n) { t &= 0xFFFF; if (t != 0xFFFF) setbits(A, t, n & 0xFFFF, 0); }
/* 0x08049D24(tile, count): free at the next fold */
void bs_free_later(u32 t, u32 n) { t &= 0xFFFF; if (t != 0xFFFF) setbits(bmB(), t, n & 0xFFFF, 0); }
