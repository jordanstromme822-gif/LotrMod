#!/usr/bin/env python3
"""Skip the copyright, New Line Cinema and EA logo screens at boot.

The game's state machine (setState at 0x08033154) normally goes
language select (0x12) -> copyright (2) -> logos (3) -> title (5).
Both places that start state 2 (boot with a save at 0x0803312C, and
leaving the language screen at 0x0802FC52) are changed to start state 5.
The language screen still appears once on a brand-new save.

  python3 tools/quickboot.py in.gba out.gba
"""
import sys

SITES = (0x2FC52, 0x3312C)  # movs r0, #2  ->  movs r0, #5


def patch(rom: bytearray) -> bytearray:
    for at in SITES:
        if rom[at:at + 2] not in (b"\x02\x20", b"\x05\x20"):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at] = 5
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("intro logos skipped ->", sys.argv[2])
