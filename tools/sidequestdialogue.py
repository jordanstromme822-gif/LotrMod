#!/usr/bin/env python3
"""Skip story dialogue but keep the dialogue of side quests that give a reward.

Replaces tools/nodialogue.py (apply one or the other). Dialogue boxes open
through 0x0801AD9C(dialogueId); level scripts reach it through command
0x08018454, which in multiplayer already skips the box and runs the follow-up
action. Two hooks check the dialogue id against an allow bitmap:

  hook1 (bl at 0x0801AD9E): allowed id -> store it and open the box as normal;
         other ids -> return to the caller without a box.
  hook2 (bl at 0x0801846E): multiplayer or a non-allowed id -> the skip path at
         0x08018484; allowed id -> the normal box path at 0x08018472.

Code and bitmap live in the freed Spanish text bank (0x9E880-0x9E90F), so the
ROM must be English only (tools/nocutscenes.py or tools/nolanguage.py).

Allowed dialogue ids (table 0x08050CE0): 21 28 29 30 33 34 35 37 41 48-53,
the reward side quests (goblin hostages, butterflies, Corsair hiding spot,
"Thank you kind sir", the lost brother, the adventure book, Corsairs about,
the hidden city elder, "Thank you good soldier", Rohirrim defence lines,
stolen horses).

  python3 tools/sidequestdialogue.py in.gba out.gba
"""
import sys

ALLOWED = [21, 28, 29, 30, 33, 34, 35, 37, 41, 48, 49, 50, 51, 52, 53]
CODE = bytes.fromhex(
    "7f280bd80f49c2088a5c07230340da4001231a4202d00c490871704701bc0047"
    "00280cd1a0887f2809d80849c308cb5c07210140cb4001210b4200d070470448"
    "004700bf00e90908a03b000300e90908858401080000")
CODE_AT, MAP_AT = 0x9E880, 0x9E900


def bitmap() -> bytes:
    m = bytearray(16)
    for i in ALLOWED:
        m[i >> 3] |= 1 << (i & 7)
    return bytes(m)


def patch(rom: bytearray) -> bytearray:
    if rom[0x1AD9C:0x1AD9E] not in (b"\x00\xb5", b"\x70\x47") or \
       rom[0x1846E:0x18472] not in (bytes.fromhex("002808d1"), bytes.fromhex("002808e0"), bytes.fromhex("86f017fa")):
        raise SystemExit("unexpected bytes; is this the BLRE ROM?")
    rom[0x1AD9C:0x1ADA2] = bytes.fromhex("00b5") + bytes.fromhex("83f06ffd")  # push {lr}; bl hook1
    rom[0x1846E:0x18472] = bytes.fromhex("86f017fa")                          # bl hook2
    rom[CODE_AT:CODE_AT + len(CODE)] = CODE
    rom[MAP_AT:MAP_AT + 16] = bitmap()
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("side-quest dialogue kept, story dialogue skipped ->", sys.argv[2])
