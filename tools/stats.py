#!/usr/bin/env python3
"""Change a hero's starting attribute in your copy of the game.

  python3 tools/stats.py rom.gba                      # list known values
  python3 tools/stats.py rom.gba out.gba aragorn courage 50

Starting attributes are small numbers written straight into the game's code
(Thumb "movs rX, #value" instructions), so a value can be 0-255.
Only entries verified in an emulator are listed here; more get added as they are confirmed.
"""
import sys

# hero -> attribute -> ROM offset of the value byte
KNOWN = {
    "aragorn": {"courage": 0x25DFA},
}
EXPECTED = {0x25DFA: (0x14, 0x21)}  # original value, instruction byte (movs r1)


def main():
    if len(sys.argv) not in (2, 6):
        raise SystemExit(__doc__)
    rom = bytearray(open(sys.argv[1], "rb").read())
    if rom[0xAC:0xB0] != b"BLRE":
        raise SystemExit("This doesn't look like the US/EU Return of the King ROM (game code BLRE).")
    if len(sys.argv) == 2:
        for hero, attrs in KNOWN.items():
            for attr, off in attrs.items():
                print(f"{hero:10} {attr:10} {rom[off]}")
        return
    out, hero, attr, value = sys.argv[2], sys.argv[3].lower(), sys.argv[4].lower(), int(sys.argv[5])
    off = KNOWN.get(hero, {}).get(attr)
    if off is None:
        raise SystemExit(f"Unknown hero/attribute. Known: {KNOWN}")
    if rom[off + 1] != EXPECTED[off][1]:
        raise SystemExit("Unexpected bytes at that spot; is this an unmodified ROM?")
    if not 0 <= value <= 255:
        raise SystemExit("Value must be 0-255")
    rom[off] = value
    open(out, "wb").write(rom)
    print(f"{hero} {attr} set to {value} in {out}")


main()
