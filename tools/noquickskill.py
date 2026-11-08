#!/usr/bin/env python3
"""Remove "Quick Skill Select" from the Options menu (Jordan, 2026-11-08: skills are always on).

Run after tools/nolanguage.py. The Options rows are then Music Volume, SFX Volume, Quick Skill
Select, Auto Healing, Fast Discard, Difficulty, Credits (rows 0-6, cursor value = row). Three
calls are pointed at small helpers in the freed Spanish text bank (0x9ED00):

  - draw loop (bl at 0x08036A2C -> 0x0809ED00): row 2 is not drawn,
  - row y (bl at 0x08036B36 -> 0x0809ED0A): rows below 2 are drawn 16 px higher, then the
    label helper from nolanguage.py (0x0809E800) runs as before,
  - up/down (bl at 0x08036E82 -> 0x0809ED12): calls the cursor routine 0x0802A030 and, if it
    landed on row 2, stores it and calls it again so the cursor steps over the row.

The cursor values stay the original row numbers, so the left/right and A handlers are unchanged.
The recompiled Wide engines need the same three calls retargeted in their generated code
(see recomp/README.md).

  python3 tools/noquickskill.py in.gba out.gba
"""
import sys

HELPERS_AT = 0x9ED00
HELPERS = bytes.fromhex(
    "022800d170470f4b1847022d00d9103e76e5f0b582b004460d4616461f460798009020468bf784f9"
    "022806d120602046294632463b468bf77bf902b0f0bc02bc084700bfe96a0308")
SITES = {
    0x36A2C: ("00f05cf8", "68f068f9"),  # bl 0x08036AE8 -> bl 0x0809ED00
    0x36B36: ("67f063fe", "68f0e8f8"),  # bl 0x0809E800 -> bl 0x0809ED0A
    0x36E82: ("f3f7d5f8", "67f046ff"),  # bl 0x0802A030 -> bl 0x0809ED12
}


def patch(rom: bytearray) -> bytearray:
    for at, (old, new) in SITES.items():
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        if rom[at:at + 4] not in (old, new):
            raise SystemExit(f"unexpected bytes at {at:#x}; run tools/nolanguage.py first")
        rom[at:at + 4] = new
    rom[HELPERS_AT:HELPERS_AT + len(HELPERS)] = HELPERS
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("quick skill select removed ->", sys.argv[2])
