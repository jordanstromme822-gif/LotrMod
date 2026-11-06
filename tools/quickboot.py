#!/usr/bin/env python3
"""Skip the copyright, New Line Cinema and EA logo screens at boot.

The game's state machine (setState at 0x08033154) normally goes
language select (0x12) -> copyright (2) -> logos (3) -> title (5).
Both places that start state 2 (boot with a save at 0x0803312C, and
leaving the language screen at 0x0802FC52) are changed to start state 5.
The title's "Press START" step then acts as if START was pressed
(its `bne` at 0x080480FA becomes `b`), so the game opens on the main menu.
A brand-new save also skips the language screen (0x08033114, state 0x12
-> 5) and lands on the title's "Press START"; English is the default.

  python3 tools/quickboot.py in.gba out.gba
"""
import sys

SITES = {0x2FC52: 2, 0x3312C: 2, 0x33114: 0x12}  # movs r0, #n  ->  movs r0, #5


def patch(rom: bytearray) -> bytearray:
    for at, old in SITES.items():
        if rom[at:at + 2] not in (bytes([old, 0x20]), b"\x05\x20"):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at] = 5
    if rom[0x480FA:0x480FC] not in (b"\x00\xd1", b"\x00\xe0"):
        raise SystemExit("unexpected bytes at 0x480fa; is this the BLRE ROM?")
    rom[0x480FB] = 0xE0  # Press START -> main menu
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("intro logos skipped ->", sys.argv[2])
