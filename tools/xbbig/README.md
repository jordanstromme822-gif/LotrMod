# Bigger crossbow trap (v202)

Jordan, 2026-11-20: "Make trap image a little larger. Give the bolt a glowing whiteish blue tip and the string a blue
ish slight glow."

- `xbbig.py` makes `xbbig.bin` (16 facings, 24x24 pictures in 32x32 sprites, 512 bytes each, ROM 0x95000 in the
  freed Spanish text bank) from `tools/turn16/xb16.bin` (Scale3x, every second pixel), and `xbbig.json` (bolt tip =
  palette colour 10, bow = colour 12, per frame) for the page's glow.
- Page patch: `recomp/playroom/bolt-trap-v202.py`. It points crossbow.c's `xb_anim` (0x080852D0) and turn16's
  `xb16_anim` at the new pictures and the 16-frame records (data only; no engine rebuild).
- Found on the way: the Orc Head code was rebuilt after v171, so `xb_update` / `xb_anim` moved (0x08083105 /
  0x080852D0) and turn16's compiled check (0x08082231 / 0x08084408) stopped matching. Crossbows have been 8-way
  since then and the v171 warm ground glow was off. v202 brings the glow back; 16-facing turning needs turn16 rebuilt
  with the new addresses and the engine regenerated.

## v203 (2026-11-20): bronze ballista + Frodo bends to set it

Jordan: "Add in an animation of him bending over to set the trap during the trap setting delay. Make trap look
nicer" (reference: an ornate bronze ballista on a pedestal with splayed feet, glowing leaf engravings, white
arrowhead).

- `xbart.py` replaces `xbbig.py`'s upscale: a small 3D model drawn in 16 facings straight into palette 3 (bronze
  5-8, gold 13, white 9, steel 10-12, outline 4). Pedestal with a gold leaf and four splayed legs stays still; the head
  (stock with gold inlay, steel lock, recurve bow, string, bolt with a white head) turns. `xbbig.json` now has, per
  frame, the bolt tip and the string as string end, nock, string end (the page glows both halves of the V).
- Page patch `recomp/playroom/bolt-trap-crouch-v203.py` (after v202): Frodo's cast animation (0x08059514..54, frame
  3 = a low bend in every direction) is held on frame 3 through the set-up time (frame timer +0x20 = set-up left - 8
  ticks), then the rest of the cast plays as the trap arms. He stays in the cast state, so he doesn't walk off.

## v208: 32 facings (Jordan, 2026-11-20: "Give the trap turn 32 steps of animation")
`FACINGS=32 python3 xbart.py` writes xb32.bin (32 x 512 bytes, ROM 0x95000-0x99000) and xb32.json. Frame order: the 8
main ways (facings 0, 4, .. 28), then 2, 6, .. 30, then the odd ones, so frames 0-7 are what crossbow.c fire() picks.
recomp/playroom/bolt-trap-fx-v208.py adds a 32-record frame list at ROM 0x99000, points xb_anim at it, and turns each
crossbow one facing a game tick toward its target from the page (frame +0x23). It also gives Elven Arrows 3-bolt bursts
and Fire Arrows a burning tip and an explosion on hit.
