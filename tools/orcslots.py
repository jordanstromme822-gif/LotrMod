#!/usr/bin/env python3
"""Orc Head slots and Orc Head tiers (Jordan, 2026-11-08).

Slots: 4 slots under the Backpack grid, one Orc Head each. Down from the bottom
backpack row reaches them; they work like equipment slots (Equip from an Orc Head's
item menu; Unequip or Discard from a slot). They are locked in 2-player games.

Tiers: every Orc Head is normal (yellow name), magic (green) or rare (red), with
bonuses rolled when it drops. Heads give their bonuses only from the slots.
  - Drops: on every kill, 1 in N for a rare, then a magic, then a normal head
    (tables in orcslots.c, drop_c). "Hard" enemies are the ones the game's own drop
    table always lets drop (0x08057F78, value 45). Normal difficulty drops normal and
    magic heads, Hard all three (rare twice as hard), Grueling magic and rare. Black
    Gate (level 58) and Cirith Ungol (levels 6-13) on Hard and Pelennor Fields
    (levels 99-107) on Grueling have better odds. The game's own item rolls never
    make an Orc Head any more.
  - Bonuses: normal heads 1-5 (Normal) or 3-7 (Hard) to a random attribute; magic
    heads 3-5 Spirit Regen or 1-5 Hit Points Regen (Normal, Hard), or 3-5 Hit Points
    Regen, 3-7 Spirit Regen or 15-20 Spirit per hit (Grueling); rare heads (5-10 to an
    attribute or 5-15% Extra Gems and Treasure) and (25-40 Hit Points, 25-40 Spirit
    Points or 5% Speed).
  - Caps: % Extra Treasure counts up to 100 and % Extra Gems up to 40 where drops
    read them (the game itself caps % Speed at 75).
  - Old Orc Heads (from before tiers) become normal heads with a fresh roll when a
    single player game loads.

How it works (details in docs/findings.md, "Orc Head slots" and "Orc Head tiers"):
  - A head's roll is the top half of its item word (the game ignores it for unique
    items): tier, difficulty table and a 12-bit seed its bonuses come from.
  - Bonuses go on and off through the game's stat routine 0x0802DDC4. Loading and
    level-ups rebuild stats (0x0802AC24 at 0x08026014); the wrapper adds the slots.
  - The slot count is saved in header byte 0x4B bits 5-7; the slot heads in EEPROM
    blocks 0x32-0x34 (one per save slot), which the game never uses.
  - 2-player games: each GBA sends its player's slot heads once as link message 4
    (unused by the game); both GBAs put the bonuses on when it arrives.

The code is C + a few assembly stubs in tools/orcslots/ (build.py needs clang and
ld.lld); the built bytes are in tools/orcslots/orcslots.bin and go in the unused
French text bank at 0x7F000, so the English-only patch must come first.

  python3 tools/orcslots.py in.gba out.gba
"""
import os
import struct
import sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orcslots")
CODE_AT = 0x7F000
BASE = 0x08000000 + CODE_AT


def thumb_bl(src, dst):
    off = dst - (src + 4)
    return struct.pack("<HH", 0xF000 | ((off >> 12) & 0x7FF), 0xF800 | ((off >> 1) & 0x7FF))


def syms():
    s = {}
    for line in open(os.path.join(D, "orcslots.sym")):
        n, a = line.split()
        s[n] = int(a, 16)
    return s


# (ROM offset, original bytes, symbol to call with bl)
BL_SITES = [
    (0x2DBE0, "2148d621", "db90_stub"),   # keepsake path of the item stat routine
    (0x26014, "04f006fe", "ac24_wrap"),   # rebuild stats from items (load, level up)
    (0x3CC08, "00201a9e", "pack_stub"),   # save-slot packer, before its checksum
    (0x3C2A6, "0af08dfd", "unpack_stub"), # save-slot unpacker
    (0x47F18, "eaf740ff", "clear_stub"),  # title screen clears both players
    (0x2A9D8, "01f03efe", "menu_wrap"),   # A in the item menu (Equip an Orc Head; Unequip / Discard on a slot)
    (0x2AA04, "02f0fafa", "desc_wrap"),   # menu closed: description of the cursor
    (0x2AA54, "01f01afb", "discard_wrap"),# "Are you sure?" Yes: discard
    (0x2CCC4, "62300478", "mcur_stub"),   # item menu up/down: our slots move like an equipment slot's menu
    (0x2C5FC, "62300078", "label_stub"),  # item menu text: "Unequip" on our slots
    (0x2CC60, "40460568", "nav_stub"),    # Backpack cursor movement
    (0x2A854, "2a4ab800", "a_stub"),      # A in the Backpack
    (0x2AC0A, "0bf04bfd", "frame_hook"),  # end of the Backpack frame (sprites done)
    (0x2A704, "0bf0ceff", "frame_hook"),  # Backpack enter
    (0x2AB9E, "1cf0a5f9", "sound_wrap"),  # the Backpack's "can't do that" sound (skipped after our A action)
    # Orc Head tiers
    (0x3A6EC, "071c6530", "drop_stub"),   # enemy drop routine: roll for an Orc Head on every kill
    (0x14B9A, "25f0effd", "genitem_wrap"),# the game's item rolls: never an Orc Head
    (0x1E0BA, "1cf05ffb", "genitem_wrap"),
    (0x2EF3E, "0bf01dfc", "genitem_wrap"),
    (0x3A750, "00f014f8", "genitem_wrap"),
    (0x461B2, "f4f7e3fa", "genitem_wrap"),
    (0x3A746, "0021425e", "find_cap"),    # % Extra Treasure read by enemy drops: at most 100
    (0x2EF32, "0288d218", "chest_cap"),   # ... and by chests
    (0x3AF54, "00240b5f", "gem_cap"),     # % Extra Gems read by gem drops: at most 40
    (0x2C4A2, "fef7dffd", "name_wrap"),   # item name: tier name and colour (backpack, shop)
    (0x2F2B4, "fbf7d6fe", "name_wrap"),   # ... and the label of an item on the ground
    (0x2D206, "fff739f9", "itemdesc_wrap"),  # item description: the head's bonuses (backpack)
    (0x1E96E, "0df085fd", "itemdesc_wrap"),  # ... (shop)
    (0x1EB8A, "0df077fc", "itemdesc_wrap"),
    (0x30F7C, "0bf052ff", "save_wrap"),   # save slot written to EEPROM: write the slot heads too
    (0x3105E, "0bf0e1fe", "save_wrap"),
    (0x3CC56, "00f0e5f8", "save_wrap"),
    (0x3CCDC, "00f084f8", "load_wrap"),   # save slots read from EEPROM: read the slot heads too
    (0x3CD14, "00f068f8", "load_wrap"),
    (0x31ED0, "07f078f9", "gp_hook"),     # every gameplay frame: 2-player games send the slot heads once
]
# link message 4 (never used by the game): send and receive cases
LINK_CASES = [(0x3FE48, 0x0804006A, "send4"), (0x3F6AC, 0x0803FDAC, "recv4")]
EXIT_PTR, EXIT_OLD = 0x6C8A8, 0x0802E875     # state 0x0A (Backpack) exit in the state table


def patch(rom: bytearray) -> bytearray:
    if rom[0x289A10 + 16:0x289A10 + 20] != bytes.fromhex("0c500708"):
        raise SystemExit("apply the English-only patch first (tools/nocutscenes.py); the code goes in the Spanish text bank")
    code = open(os.path.join(D, "orcslots.bin"), "rb").read()
    s = syms()
    for off, old, name in BL_SITES:
        new = thumb_bl(0x08000000 + off, s[name])
        if bytes(rom[off:off + 4]) not in (bytes.fromhex(old), new):
            raise SystemExit(f"unexpected bytes at {off:#x}; is this the BLRE ROM?")
        rom[off:off + 4] = new
    for at, orig, name in LINK_CASES:
        cur = struct.unpack_from("<I", rom, at)[0]
        if cur not in (orig, s[name]):
            raise SystemExit(f"unexpected link case at {at:#x}")
        struct.pack_into("<I", rom, at, s[name])
    cur = struct.unpack_from("<I", rom, EXIT_PTR)[0]
    if cur not in (EXIT_OLD, s["exit_hook"] | 1):
        raise SystemExit(f"unexpected state table entry at {EXIT_PTR:#x}")
    struct.pack_into("<I", rom, EXIT_PTR, s["exit_hook"] | 1)
    assert CODE_AT + len(code) <= 0x89864, "code runs into the German text bank"
    rom[CODE_AT:CODE_AT + len(code)] = code
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("Orc Head slots added ->", sys.argv[2])
