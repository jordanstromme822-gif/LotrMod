#!/usr/bin/env python3
"""Unlock the four Bonus Maps paths (Moria, Weathertop, Helm's Deep, Fangorn).

The "Choose your path" screen (game state 0x18) checks each path's bit
(path table 0x08050634, 0x1C bytes per path, mask at +0x18) against the save's
progress bits at 0x0300581C. The four `beq` that skip a locked path become
no-ops, so every path is open on every save. Progress bits are not changed.

  python3 tools/unlockpaths.py in.gba out.gba
"""
import sys

SITES = {0x131A4: 0x10, 0x1323C: 0x0A, 0x134E4: 0x08, 0x13586: 0x11}  # beq +n -> nop


def patch(rom: bytearray) -> bytearray:
    for at, off in SITES.items():
        if rom[at:at + 2] not in (bytes([off, 0xD0]), b"\xc0\x46"):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at:at + 2] = b"\xc0\x46"
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("bonus paths unlocked ->", sys.argv[2])
