#!/usr/bin/env python3
"""Let Frodo wear the best armor and footwear.

Every base item has a word in its category's list (category table 0x08068F50,
pointer at +0x20, 8 bytes per item). Bits 26-31 of the first word say which
heroes may equip it: bit 26 Frodo, 27 Legolas, 28 Aragorn, 29 Gandalf,
30 Eowyn, 31 Gimli. Bits 18-25 pick the equip slot (bit 18 body armor,
bit 21 helmet, bit 24 footwear, ...).

The game leaves Frodo's bit off for:
  - footwear (category 13): Wrappings, Sandals, Clogs, Shoes, Boots,
    Riding Boots, Sollerets
  - the six heaviest armor pieces (category 8, items 18-23): Lamellar,
    Breastplate, Greathelm, Corselet, Full Corselet, Footman Plate

This turns it on. Frodo's Backpack screen already has a footwear box (bottom
left); it shows up as soon as he wears something there. Level requirements
stay as they are. Loot and shops use the same bits, so Frodo can now find and
buy these items too.

  python3 tools/frodogear.py in.gba out.gba
"""
import struct
import sys

CATS = 0x68F50          # category table (ROM offset), 0x28 bytes per category
FRODO = 0x04            # bit 26 of the word = bit 2 of its top byte

# (category, item indexes, original hero-mask bytes)
TARGETS = [
    (13, range(0, 7), [0xF9] * 7),                              # footwear
    (8, range(18, 24), [0xD8, 0xD0, 0xD0, 0xD0, 0xD0, 0xD0]),   # heavy armor
]


def sites(rom):
    for cat, items, masks in TARGETS:
        lst = struct.unpack_from("<I", rom, CATS + cat * 0x28 + 0x20)[0] - 0x08000000
        for i, m in zip(items, masks):
            yield lst + i * 8 + 3, m


def patch(rom: bytearray) -> bytearray:
    for at, old in sites(rom):
        if rom[at] not in (old, old | FRODO):
            raise SystemExit(f"unexpected byte {rom[at]:#x} at {at:#x}; is this the BLRE ROM?")
        rom[at] = old | FRODO
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    rom = bytearray(open(sys.argv[1], "rb").read())
    open(sys.argv[2], "wb").write(patch(rom))
    print("Frodo can wear footwear and heavy armor ->", sys.argv[2])
