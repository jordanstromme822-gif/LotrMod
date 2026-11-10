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

/* ---- More than 128 sprites (engine upgrade 2026-11-10) ----
   The game appends OAM entries to a shadow buffer (2 buffers x 2 halves x 128 entries; the halves
   differ only in entries hidden on alternate frames) and its VBlank IRQ DMAs one half to OAM.
   With the extra sprite memory on, the engine maps 8 KB at 0x07000000: entries 128-250 are drawn
   from 0x07000400, and 0x07000800-0x070017FF holds the game's shadow copies of those entries
   (buffer 0x03004340 -> 0x07000800, buffer 0x03004B80 -> 0x07001000; half B at +0x400).
   Otherwise every function below does exactly what the original did. */
#define CNT    (*(volatile u8 *)0x03004220)
#define CUR    (*(volatile u32 *)0x03004B40)   /* buffer being filled */
#define LAST   (*(volatile u32 *)0x03004330)   /* buffer handed over last */
#define HALF   (*(volatile u32 *)0x03001F18)
#define DISP   (*(volatile u32 *)0x030040B0)
#define OAM2   ((volatile u32 *)0x07000400)
#define NMAX   251u
static volatile u32 *xs(u32 buf) { return (volatile u32 *)(buf == 0x03004B80 ? 0x07001000 : 0x07000800); }

/* 0x08036540(index, entry): append one entry; 0 or -1 when full */
int bs_oam_put(u32 idx, const u32 *e) {
    u32 n = CNT, x = ext();
    idx &= 0xFF;
    if (x ? n >= NMAX : (n & 0x80) != 0) return -1;
    CNT = (u8)(n + 1);
    volatile u32 *p;
    if (idx < 128) p = (volatile u32 *)CUR + idx * 2;
    else if (x && idx < NMAX) p = xs(CUR) + (idx - 128) * 2;
    else return 0;
    p[0] = e[0]; p[1] = e[1];
    p[0x100] = e[0]; p[0x101] = e[1];
    return 0;
}
/* 0x08036590(index): hide the entry in half B (shown on alternate frames) */
void bs_oam_hideb(u32 idx) {
    idx &= 0xFF;
    volatile u32 *p;
    if (idx < 128) p = (volatile u32 *)CUR + 0x100 + idx * 2;
    else if (ext() && idx < NMAX) p = xs(CUR) + 0x100 + (idx - 128) * 2;
    else return;
    p[0] = (p[0] & ~0x300u) | 0x200u;
}
/* 0x080366A4(): frame done, hide the unused entries, tell the VBlank IRQ */
void bs_oam_end(void) {
    u32 i = CNT;
    volatile u32 *b = (volatile u32 *)CUR;
    for (; i < 128; i++) { b[i * 2] = 0x200; b[0x100 + i * 2] = 0x200; }
    if (ext()) {
        volatile u32 *q = xs(CUR);
        for (i = CNT < 128 ? 128 : CNT; i < NMAX; i++) { q[(i - 128) * 2] = 0x200; q[0x100 + (i - 128) * 2] = 0x200; }
    }
    *(volatile u16 *)(DISP + 0x38) = 1;
}
/* 0x080366EC(): every entry = the blank template, DMA buffer to OAM, count 0 */
void bs_oam_init(void) {
    const u32 *t = (const u32 *)0x0806CEB4;
    volatile u32 *b = (volatile u32 *)CUR;
    for (u32 i = 0; i < 128; i++) { b[i * 2] = t[0]; b[i * 2 + 1] = t[1]; b[0x100 + i * 2] = t[0]; b[0x101 + i * 2] = t[1]; }
    if (ext()) {
        volatile u32 *q0 = xs(0x03004340), *q1 = xs(0x03004B80);
        for (u32 i = 0; i < 0x200; i += 2) { q0[i] = t[0]; q0[i + 1] = t[1]; q1[i] = t[0]; q1[i + 1] = t[1]; }
        for (u32 i = 0; i < 0x100; i += 2) { OAM2[i] = t[0]; OAM2[i + 1] = t[1]; }
    }
    *(volatile u32 *)0x040000D4 = CUR;
    *(volatile u32 *)0x040000D8 = 0x07000000;
    *(volatile u32 *)0x040000DC = 0x84000100;
    (void)*(volatile u32 *)0x040000DC;
    CNT = 0;
}
/* VBlank IRQ, right after the game DMAs a shadow half to OAM: copy the same half of the
   extra entries to the engine's second OAM block */
void bs_oam_vbl(void) {
    if (!ext()) return;
    u32 buf = LAST == 0x03004340 ? 0x03004B80 : 0x03004340;
    volatile u32 *q = xs(buf) + (HALF & 1) * 0x100;
    for (u32 i = 0; i < 0x100; i++) OAM2[i] = q[i];
}
