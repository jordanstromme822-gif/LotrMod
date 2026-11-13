# 16-facing walk test (Frodo)

Jordan, 2026-11-11: "What if you re drew the gaps in between the animation frames to make 360 degree motion look
smooth?" First test on Frodo (the smallest hero).

- `turn16.c` (ROM 0x0809F000, `build.py` -> `turn16.bin` / `.sym`): a wrapper for the hero's update (object + 0x14,
  game 0x080236B9). After the game's own 8-way step it turns the walk velocity (+0xB4 / +0xB8) to the stick's exact
  angle at the same speed (+0xE4); the move step 0x080023C0 and collision run after it, unchanged. For Frodo it
  picks one of 16 facings and shows an in-between picture for the odd ones (and the game's own picture, mirrored
  as the game does, for the even ones). Hysteresis of 3/256 of a turn stops flicker on a border.
- `gen16.py`: makes the in-between pictures from the game's own frames (needs the ROM; output stays private).
- `tables.py`: sine table and screen angle -> facing table (the ground is squashed 2:1 on screen, so the game's
  "up-right" walks at 63 degrees; facings are 22.5 degrees apart on the ground, not on screen).
- Page side: `recomp/playroom/free-angle.js` + `free-angle-v170.py` (setup chip "Joystick: Free 360° / 8 ways",
  localStorage `rotk-free`, on by default).

Mailbox (EWRAM 0x0203FFC0 + 4 * player): +0 bit 0 on, bit 1 stick held; +1 angle (0 = up, clockwise, 256 steps);
+2 last facing | 0x80.

No engine rebuild: the page writes the hook's address into the hero object (RAM), and the engines run code they
have no native copy of in their interpreter, like the Orc Head hooks. 1-player Wide only; the 2-player engines
never get the pointer, so linked games stay 8-way and in step.

## v171 (2026-11-11): crossbow traps in 16 facings, trap glow, knife stun swirl

Jordan: "Do with Frodo trap animation as well", "make traps appear more apparent by giving them their own light
aura, faint but noticeable", and "Frodo's stuns from knife throw don't show an animation".

- Crossbows: `xb16.py` makes 8 in-between crossbow pictures from the 8 hand-drawn ones in `tools/orcslots/xbgfx.c`
  (head scaled up with Scale2x, turned 22.5 degrees on the ground, outlined again; left side mirrored) and writes
  `xb16.bin` (ROM 0x94400, freed German text bank): frames 0-7 are the old 8 facings, 8-15 the odd ones, so the
  Orc Head code's own 8-way pick still shows a right picture. Our own pixel art, so it is in the repo.
  `hero_upd` gives each live crossbow of Frodo's (crossbow.c list at 0x0203F360) the 16-frame set (`xb16_anim`)
  and turns it one facing a tick toward the foe it would shoot, so it swings round instead of snapping.
  The hook is now on in the solo Wide engine whatever the joystick chip says (with 8 ways it only clears the stick
  mailbox). The Orc Head code itself is unchanged, so no engine rebuild.
- Knife stun: knife.c used 0x08008A6C (state 0x12, a different status), so the foe walked on and the stun swirl
  (0x0801C33C, flag 8, which only stays while the foe is in state 0x1A) went at once. knife.c's STUN now calls
  `kt_stun` at the fixed address 0x0809FF01 (`link.ld` section `.stun`; only a literal in knife.c changes, so no
  Orc Head code moves). Setting the game's stun (state 0x1A, timer + 0x50, + 0x64 |= 2) at the hit didn't hold
  (the hit's own reaction came after), so kt_stun notes the foe (2 notes at EWRAM 0x0203FFC8) and `hero_upd`
  stuns it 2 ticks later, puts the swirl on with flag 0x10 (its own timer) and holds state 0x1A for the stun's
  time. `tools/orcslots.py` also writes kt_stun into ROMs built without the rest of this hook.
  The 2-player engine compiled knife.c's touch with the old call, so linked games keep the old stun.
- Trap glow: `recomp/playroom/trapglow_v171.py` (page lighting pass, like Gandalf's aura).
- Page: `recomp/playroom/xb16-v171.py` + `trapglow_v171.py` + `tools/orcslots/pagejs.py` on the live v170 page.

## v176 (2026-11-13): every hero in 16 facings

Jordan: "Should we do all chapters 360 motion?" (all heroes). Walk and stand in-between pictures for all 8 heroes,
1-player Wide engine only; attacks stay 8-way for now.

- `gen16all.py <original ROM> hero16.bin` is gen16.py for every hero: hero id h has its anim table at 0x08282898 + 4h
  (0 Frodo 0x0806170C, 1 Legolas, 2 Aragorn, 3 Gandalf, 4 Eowyn, 5 Gimli, 6 Sam, 7 Smeagol) and its sprite palette
  at 0x08282C68 + 4h. Colours are matched by palette distance instead of Frodo's hand-made colour groups. The
  output starts with 8 pairs {game's table, ours}, then each hero's table copy and pictures (about 480 KB in all;
  made from the game's own art, so it stays out of the repo).
- That doesn't fit in the freed text banks, so the page grows the built game past 16 MB and puts it at ROM
  0x1000000 (CPU 0x09000000). The engine loads any ROM size; only the 1-player engine reads it. The 2-player
  engine and the game file download get the first 16 MB (the hook never runs there, and a 16 MB file saves on any
  emulator). Frodo's old block at 0x8A000 is no longer written by the page.
- `hero_upd` finds the hero's own table in that index by its object + 0x88, so any hero (and any costume table
  listed there) gets the in-between pictures.
- Page: `recomp/playroom/all360-v176.py in.html out.html turn16.bin hero16.bin` on the live v175 page.
