#!/usr/bin/env python3
"""Fix the damage-stacking glitch (swap a two-handed sword and a shield over and over).

Item stats are added when an item is equipped and taken off when it is removed, through
0x0802DDC4(category, stat, hero, delta). Its default path has a special case: for a
two-handed sword (category 2) and the damage stats (0 and 1) it adds delta / 2. Equipping
the sword adds the full value, but when a shield pushes it out of the hand only half is
taken off, so every swap leaves half the sword's damage behind (max damage at hero + 0xA4:
11 -> 19 -> 10 -> 29 -> 20 ...). The branch at 0x0802DF56 now always takes the normal
full-delta path, so equip and unequip cancel out (19 -> 0 -> 19 -> 0). Swapping the
two-handed sword for a one-handed one still gives the right numbers.

  python3 tools/nostack.py in.gba out.gba
"""
import sys

AT, OLD, NEW = 0x2DF56, bytes.fromhex("12d1"), bytes.fromhex("12e0")  # bne 0x0802DF7E -> b 0x0802DF7E


def patch(rom: bytearray) -> bytearray:
    if rom[AT:AT + 2] not in (OLD, NEW):
        raise SystemExit(f"unexpected bytes at {AT:#x}; is this the BLRE ROM?")
    rom[AT:AT + 2] = NEW
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("damage stacking fixed ->", sys.argv[2])
