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
