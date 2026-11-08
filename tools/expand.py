#!/usr/bin/env python3
"""Grow the game file from 16 MB to 32 MB so mods have room for new data.

  python3 tools/expand.py rotk.gba rotk-32mb.gba

The new space (ROM offsets 0x1000000-0x1FFFFFF, CPU addresses 0x09000000-0x09FFFFFF)
is filled with 0xFF. Tested in mGBA: the game boots, saves, and loads saves normally.

Note: on a 32 MB cartridge, real hardware only answers EEPROM saves at 0x0DFFFF00 and
up, but this game talks to 0x0D000000. mGBA doesn't mind; some other emulators and
flash carts may lose saves until the save code is patched (see docs/findings.md).
"""
import sys

SIZE = 32 * 1024 * 1024
FREE_START = 0x1000000


def expand(rom):
    if rom[0xAC:0xB0] != b"BLRE":
        raise SystemExit("This doesn't look like the US/EU Return of the King ROM (game code BLRE).")
    if len(rom) >= SIZE:
        return rom
    return rom + b"\xff" * (SIZE - len(rom))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    out = expand(open(sys.argv[1], "rb").read())
    open(sys.argv[2], "wb").write(out)
    print(f"wrote {sys.argv[2]} ({len(out) // (1024 * 1024)} MB, free space from 0x{FREE_START:X})")
