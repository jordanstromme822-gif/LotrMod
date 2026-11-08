#!/usr/bin/env python3
"""Shorter level loads.

1. Every screen fade in the game (nine loops: 0x0803D354, 0x0803D4B2, 0x0803E07C,
   0x0803E15C, 0x0803E1E0, 0x0803E348, 0x0803E388, 0x0803E414, 0x0803E658) waits
   two frames per brightness step. The second wait becomes two nops, so each
   fade takes 16 frames instead of 32.
2. While gameplay (state 1) is setting a level up, the screen is black for about
   half a second of real work. The setup marks EWRAM 0x0203FFF1 non-zero when it
   starts (hook at 0x0803163E) and clears it just before its fade-in (hook at
   0x08031DBA). The Play Room fast-forwards the emulator while the byte is set.

Hook code lives in the freed Spanish text bank (0x9E940-0x9E963), so the ROM
must be English only (tools/nocutscenes.py or tools/nolanguage.py).

  python3 tools/fastloads.py in.gba out.gba
"""
import sys

WAITS = [0x3D354, 0x3D4B2, 0x3E07C, 0x3E15C, 0x3E1E0, 0x3E348, 0x3E388, 0x3E414, 0x3E658]
NOP2 = bytes.fromhex("c046c046")
CODE_AT = 0x9E940
CODE = bytes.fromhex("86b00549097005a8704700bf034900220a700349084700bff1ff0302f1ff030249e10308")
SITES = {0x3163E: (bytes.fromhex("86b005a8"), bytes.fromhex("6df07ff9")),  # bl 0x0809E940
         0x31DBA: (bytes.fromhex("0cf0c5f9"), bytes.fromhex("6cf0c7fd"))}  # bl 0x0809E94C


def bl(src, dst):
    off = (dst - (src + 4)) >> 1
    return (0xF000 | ((off >> 11) & 0x7FF)).to_bytes(2, "little") + (0xF800 | (off & 0x7FF)).to_bytes(2, "little")


def patch(rom: bytearray) -> bytearray:
    for o in WAITS:
        if rom[o + 4:o + 8] not in (bl(0x08000000 + o + 4, 0x0802A398), NOP2):
            raise SystemExit(f"unexpected bytes at {o:#x}; is this the BLRE ROM?")
        rom[o + 4:o + 8] = NOP2
    for at, (old, new) in SITES.items():
        if rom[at:at + 4] not in (old, new):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at:at + 4] = new
    rom[CODE_AT:CODE_AT + len(CODE)] = CODE
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("shorter fades and load flag ->", sys.argv[2])
