/* Save on exit (plan Phase 2, Jordan's Diablo 2 style "auto-save on exit with no save screen").
   The page asks (ASREQ) and the next gameplay or Backpack update saves the hero into the slot this play session
   belongs to, the way the pause menu's Save Game does (0x08030F08(1)) but without the slot screen:
     0x0804711C, pack the hero into the slot's header (0x0803C6CC(HDRS + 0x70 * slot, [0x03004174])),
     write it (save_wrap in tools/orcslots: page 2, slot heads, arrows, stash, header), 0x0803CD6C (file header),
     0x08047128.
   The session's slot is the save slot lock (tools/nodupe.py: DUPELOCK = slot + 1, set by every load and save) and
   its page SESSPG (tools/orcslots). A new game that was never saved has no slot, so nothing is saved (ASRES 2).
   Hooked through the state table only (state 1 and 0x0A updates), so the Wide engines need no rebuild: the
   interpreter runs these and the game's own updates go on natively. */
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
typedef int (*fn4)(int, int, int, int);
#define ASREQ    (*(volatile u8 *)0x0203F3E0)   /* the page: save now */
#define ASDONE   (*(volatile u8 *)0x0203F3E1)   /* counts finished requests */
#define ASRES    (*(volatile u8 *)0x0203F3E2)   /* 1 saved, 2 no slot yet, 3 busy (state change pending) */
#define ASSLOT   (*(volatile u8 *)0x0203F3E3)   /* page << 4 | slot of the last save */
#define ASON     (*(volatile u8 *)0x0203F3E5)   /* the page turned saving on (1-player games only, for now) */
#define DUPELOCK (*(volatile u8 *)0x0203FFF0)
#define PAGE     (*(volatile u8 *)0x0203F000)
#define SESSPG   (*(volatile u8 *)0x0203F007)
#define SESSV    (*(volatile u8 *)0x0203F009)
#define PENDING  (*(volatile u32 *)0x030041F0)
#define HDRS     0x03005630
#define HEROSRC  (*(volatile u32 *)0x03004174)
#define LASTSLOT (*(volatile u8 *)0x03005834)
#define SAVE_WRAP 0x080802F5                    /* tools/orcslots save_wrap (orcslots.sym) */
#define PLAY_UPD  0x08031E45                    /* the game's state 1 update */
#define BAG_UPD   0x0802A799                    /* the game's state 0x0A (Backpack) update */

static void save_now(void)
{
    if (!DUPELOCK) { ASRES = 2; ASDONE++; return; }
    int slot = (DUPELOCK - 1) & 3, keep = PAGE;
    PAGE = SESSV ? (SESSPG & 1) : (keep & 1);
    ((fn4)0x0804711D)(0, 0, 0, 0);
    ((fn4)0x0803C6CD)(HDRS + 0x70 * slot, (int)HEROSRC, 0, 0);
    ((fn4)SAVE_WRAP)(HDRS + 0x70 * slot, slot, 0, 0);
    ((fn4)0x0803CD6D)(0, 0, 0, 0);
    ((fn4)0x08047129)(0, 0, 0, 0);
    ASSLOT = (u8)(PAGE << 4 | slot);
    PAGE = (u8)keep;
    LASTSLOT = (u8)slot;
    ASRES = 1; ASDONE++;
}
static void service(void)
{
    if (!ASREQ) return;
    if (PENDING & 0x80) { ASRES = 3; return; }   /* a level or state change is pending: next update */
    ASREQ = 0;
    save_now();
}
/* The Wide engine never calls the pause menu's update through the state table, so the hero is saved as the pause menu
   is asked for instead: a gameplay update that ends with state 0x10 pending (0x90), once per opening. */
#define ASPAUSE  (*(volatile u8 *)0x0203F3E4)   /* this opening of the pause menu has been saved */
int as_play(int a, int b, int c, int d)
{
    service();
    int r = ((fn4)PLAY_UPD)(a, b, c, d);
    if ((PENDING & 0xFF) == 0x90) { if (!ASPAUSE && ASON) { ASPAUSE = 1; save_now(); } }
    else ASPAUSE = 0;
    return r;
}
int as_bag(int a, int b, int c, int d) { service(); return ((fn4)BAG_UPD)(a, b, c, d); }
