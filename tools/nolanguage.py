#!/usr/bin/env python3
"""Remove "Language Select" from the Options menu (title screen and pause menu).

The Options screen (game state 6) has 8 rows: Music Volume, SFX Volume,
Quick Skill Select, Auto Healing, Fast Discard, Difficulty, Language Select,
Credits. The row drawn at index i uses text 0x39 + i and sits at y = 0x20 + 16*i.
This patch makes the menu 7 rows long and puts Credits in row 6:

  - the draw loop at 0x08036A36 stops after row 6 (cmp r4,#7 -> #6),
  - the up/down cursor limit (0x08036E7E, 0x08036EA8) becomes 6,
  - A on row 6 starts the credits (beq at 0x08036F2A now goes to the credits branch),
  - the label for row 6 comes from a 12-byte helper at 0x0809E800 that returns
    text 0x40 (Credits) for row 6 and 0x39 + i otherwise (bl at 0x08036B36).

The helper lives in the Spanish text bank, which is unused once every language
points at English (tools/heroes.py and tools/nocutscenes.py do that).

  python3 tools/nolanguage.py in.gba out.gba
"""
import sys

HELPER_AT = 0x9E800
HELPER = bytes.fromhex("281c3930062d00d101307047")  # adds r0,r5,#0; adds r0,#0x39; cmp r5,#6; bne +2; adds r0,#1; bx lr
SITES = {
    0x36B36: ("281c3930", "67f063fe"),  # label id -> bl 0x0809E800
    0x36A36: ("072c", "062c"),          # draw rows 0..6
    0x36E7E: ("0722", "0622"),          # cursor max 6
    0x36EA8: ("0722", "0622"),          # cursor max 6 (difficulty skip path)
    0x36F2A: ("07d0", "0bd0"),          # A on row 6 -> credits
}


def patch(rom: bytearray) -> bytearray:
    for at, (old, new) in SITES.items():
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        if rom[at:at + len(old)] not in (old, new):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at:at + len(new)] = new
    rom[HELPER_AT:HELPER_AT + len(HELPER)] = HELPER
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("language select removed ->", sys.argv[2])
