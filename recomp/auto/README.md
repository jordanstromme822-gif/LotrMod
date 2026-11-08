# Moria auto mode (Play Room v81)

The Play Room shows an **Auto** button at the top left while playing the Moria bonus map
(level id 82 at 0x030041F8). `auto.js` is the code that went into the page; the Python
files are the headless prototype it was built from (libmgba via `wrap.c`).

Memory facts used:
- Player struct 0x03003C00 + 0x1AC*player: hero entity pointer +0, HP +0x17C, max HP +0xD0,
  equipment +0x3C..+0x58 (8 slots), backpack +0x5C (8 slots), auto-heal flag +0x19A bit 0
  (saved setting 0x03005820 bit 4), level-1 at +0x19C, hero id +0x19F.
- Entities (0x148 bytes, list linked through +0/+4): update fn +0x14, x +0xAE, y +0xB2.
  Enemies update 0x0801B9D1 (state +0x62; 0x11/0x15/4/0x1B/0x13 = dead). Trigger zones
  0x0802ED21 (+0x63 == 0 not yet fired) spawn the waves. Ground items 0x0802F131: type +0x60
  (text 568+type; 13/14 gems, 15-24 food and herbs, larger = gear), item word +0x88,
  state +0x63 (3 on ground, 1 taken, 6 "no room in backpack").
- Collision: map size in tiles 0x03005F90/0x03005F88, 32x32 block map *0x0300206C (u16 & 0xFFF),
  16 cells per block at *0x03002068 + block*16; cell value & 7 of 1 or 2 blocks (0x08034770).
- Buttons: B = attack, R = pick up (A does nothing in play).
- Items: category table 0x08068F50 (0x28 bytes: +0 base list 12-byte entries, +8 prefixes,
  +0x14 suffixes, +0x20 per-item flags 8 bytes). Entry: name, tier byte 2, (stat, value)
  pairs from byte 3. Flags: hero bits 26-31 (Sam counts as Frodo), slot bits 18-25,
  0x20000 two-handed, 0x10000 backpack-only. Required level 0x0802D2F8, can-equip 0x0802EA88.
