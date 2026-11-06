#!/usr/bin/env python3
"""Unlock Sam and Smeagol, the game's own unlockable heroes.

They are picked in a save slot's "Select Hero" (Bonus Maps / new slot), the
picker at 0x080308F4 that cycles heroes 0-7. It skips Sam (6) unless save
progress bit 0x1 is set and Smeagol (7) unless bit 0x4000 is set
(progress bits at 0x0300581C). Both checks become "unlocked".

  python3 tools/unlockheroes.py in.gba out.gba
"""
import sys

NOP = b"\xc0\x46"
SITES = {
    0x30924: (bytes.fromhex("e86a8021c90108404042c40f"), b"\x01\x24" + NOP * 5),  # Smeagol: r4 = 1
    0x30940: (bytes.fromhex("ec6a01200440"), b"\x01\x24" + NOP * 2),              # Sam: r4 = 1
}


def patch(rom: bytearray) -> bytearray:
    for at, (old, new) in SITES.items():
        cur = bytes(rom[at:at + len(old)])
        if cur not in (old, new):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at:at + len(new)] = new
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("Sam and Smeagol unlocked ->", sys.argv[2])
