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

Regenerating quivers (Jordan, 2026-11-08, same code): 3% of dropped arrows regenerate
1 arrow a second, starting 1 second after the last shot, up to the count they dropped
with. They stay at 0 arrows instead of vanishing (you can still discard them), never
merge with picked-up arrows, and show "Orcish Arrows: 7/25" in green with "Regenerates
1 arrow a second" (docs/findings.md, "Arrows and quivers").

How it works (details in docs/findings.md, "Orc Head slots" and "Orc Head tiers"):
  - A head's roll is the top half of its item word (the game ignores it for unique
    items): tier, difficulty table and a 12-bit seed its bonuses come from.
  - Bonuses go on and off through the game's stat routine 0x0802DDC4. Loading and
    level-ups rebuild stats (0x0802AC24 at 0x08026014); the wrapper adds the slots.
  - The slot count is saved in header byte 0x4B bits 5-7; the slot heads in the save
    file header, bytes 8 + 8k for save slot k (v122; v120-v121 used EEPROM blocks
    0x32-0x34, which are the start of save slot 4).
  - Save slot pages (v122): a second page of 4 save slots kept by the page; R or the
    page's Page button flips on the save slot screens; the page's Undo puts back a
    saved-over slot while the save screen or pause menu is open.
  - Arrow slots (v123): Legolas gets 2 arrow-only slots under the Orc Head slots. Picked-up
    arrows that don't go on the worn quiver fill them before the backpack; the page's L
    button (ACYC) puts on the next quiver.
    Frodo (v125) gets 1, centred under them, for his crossbows: picked-up arrows fill it
    first, and Equip on arrows in his backpack moves them in (swapping with what was there).
  - 64 Kbit save chip (v124): one byte sets the game's EEPROM library up for the 8 KB chip,
    and page 2, its slot heads and the arrow slots are kept in blocks 64-132 (marker
    "LOTRXT01" in block 64). Old 512-byte saves get them from the page's copies once.
  - Arrow slots in 2-player games (v124): link message 6 sends each player's 2 slots; a
    flick of GBA L (changed twice within 8 ticks, no A, B or R) sends link message 7, and
    both GBAs put on the next quiver when it comes in.
  - Crossbows (v125, Jordan 2026-11-09): Frodo's Snare (skill table entry at 0x6E974) places
    a crossbow instead of a trap (tools/orcslots/crossbow.c): same Spirit cost and damage
    table (5 + 3 / level), 10 bolts at the nearest awake foe within 120 x 80 pixels, one a
    second, then it breaks; it also breaks after 10 s + 3 s per level above 1. 1 crossbow,
    2 from level 3, 3 at level 5; one more breaks the oldest. Bolts are the game's own arrows
    and use the arrows in Frodo's 1 arrow slot (picture, damage stats, Extra Projectiles,
    Armor Piercing; 1 arrow a shot). The skill text (518) is re-encoded at 0x89400.
  - Frodo's skill rework (v126, Jordan 2026-11-09): Knife Toss (0x6E94C, tools/orcslots/knife.c)
    does 8 at every level, stuns each foe it hits for 0.5 s and bounces to the nearest unhit
    foe within 64 px (level L hits up to L foes, each hit 1/5 less). Galadriel's Cloak
    (0x6E99C) is Quick Drop: 40 Spirit, sets down every unlocked crossbow in a row in front of
    Frodo, cooldown 60 s - 7 s per level above 1; it can't be cast or bought before Crossbow
    has a level. Knives and bolts pass through foes under Ring's Persuasion. Texts 517-519.
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
    (0x31ED0, "07f078f9", "gp_hook"),     # every gameplay frame: 2-player games send the slot heads once; quivers refill
    # regenerating quivers
    (0x249A2, "07f035fd", "arrow_wrap"),  # a shot uses up an arrow (4 calls)
    (0x24A0C, "07f000fd", "arrow_wrap"),
    (0x24BEE, "07f00ffc", "arrow_wrap"),
    (0x44AE0, "e7f796fc", "arrow_wrap"),
    (0x2AEAC, "03f02cfe", "same_wrap"),   # picked-up arrows join a matching quiver: never a regenerating one
    (0x2AF22, "03f0f1fd", "same_wrap"),
    # save slot pages
    (0x307F0, "c046c046", "flip_r"),      # R on the save slot screen (free since tools/nodelete.py): other page
    # arrow slots (Legolas)
    (0x2AD0E, "00f0abf8", "apick_wrap"),  # picked-up arrows: worn quiver, then the arrow slots, then the backpack
    # Frodo's Quick Drop: the game's "can cast" check (4 calls) waits for its cooldown; buying it needs Crossbow
    (0x23896, "1ff0f5fd", "cancast_wrap"),
    (0x293EE, "1af049f8", "cancast_wrap"),
    (0x431F6, "00f045f9", "cancast_wrap"),
    (0x433E0, "00f050f8", "cancast_wrap"),
    (0x41FBA, "00f099f9", "req_wrap"),    # Skills page A: hero level needed for the next level
]
# link message 4 (never used by the game): send and receive cases
LINK_CASES = [(0x3FE48, 0x0804006A, "send4"), (0x3F6AC, 0x0803FDAC, "recv4"),
              # link message 6 (never used either): one player's arrow slots, same 8-byte send case
              (0x3FE50, 0x0804006A, "send4"), (0x3F6B4, 0x0803FDAC, "recv6"),
              # link message 7: a player flicked GBA L (Legolas: next quiver on both GBAs)
              (0x3FE54, 0x0804006A, "send4"), (0x3F6B8, 0x0803FDAC, "recv7")]
# plain byte changes: (offset, original, new, what)
BYTES = [(0x3CF8E, "0420", "4020", "the game's EEPROM library set up for the 64 Kbit chip (was 4 Kbit): room for page 2 and the arrow slots"),
         (0x6E956, "01000100010001000100", "00000000000000000000", "Frodo's Knife Toss: 8 damage at every level (was +1 / level)"),
         (0x6E9BD, "02", "00", "Quick Drop: the cast ends like Snare's (the cloak's flag 2 kept Frodo casting until its handler set his state)")]
EXIT_PTR, EXIT_OLD = 0x6C8A8, 0x0802E875     # state 0x0A (Backpack) exit in the state table
# more state table entries: (offset, original, hook)
STATE_PTRS = [(0x6C898, 0x080306ED, "slot_upd"),   # state 9 (save slots) update: page flips and Undo requests
              (0x6C8EC, 0x080397FD, "pause_upd"),  # state 0x10 (pause menu) update: Undo requests
              (0x6E94C, 0x080203BD, "kt_cast"),    # Frodo's skill 0 handler (Knife Toss): stun and bounces
              (0x6E974, 0x080455C1, "xb_cast"),    # Frodo's skill 1 handler (Snare): crossbows
              (0x6E99C, 0x08044D41, "qd_cast")]    # Frodo's skill 2 handler (Galadriel's Cloak): Quick Drop


# Frodo's Snare text (index 518) says what the skill does now. Re-encoded with the English bank's own Huffman tree
# (see tools/text.py) at TEXT_AT, in the freed French bank after the code.
LANG_TABLE, TEXT_AT = 0x289A10, 0x89400
TEXTS = [(517, b"Knife Toss (Level @1) - Frodo throws a knife for 8 damage that stuns for half a second. It bounces to"
               b" 1 more foe / level above 1, each hit doing 1/5 less. @2 Spirit."),
         (518, b"Crossbow (Level @1) - Frodo sets up a crossbow that shoots the nearest foe 10 times for 5 damage + 3 / level."
               b" 2 crossbows at level 3, 3 at level 5. @2 Spirit."),
         (519, b"Quick Drop (Level @1) - Frodo sets down all his crossbows in front of him. Ready again after 60 seconds"
               b" - 7 / level above 1. Needs Crossbow. @2 Spirit.")]


def encode(rom, bank, text):
    """Huffman-encode text (plus the 0 terminator) with the bank's own tree."""
    tree = bank + 4
    codes, todo = {}, [(0x100, [])]
    while todo:
        node, path = todo.pop()
        for bit in (0, 1):
            child = struct.unpack_from("<H", rom, tree + (node - 0x100) * 4 + 2 * bit)[0]
            if child == 0x100:
                continue                      # a link back to the root; never needed to encode
            if child > 0xFF:
                todo.append((child, path + [bit]))
            else:
                codes.setdefault(child, path + [bit])
    missing = set(text) - set(codes)
    if missing:
        raise SystemExit(f"characters not in the text tree: {bytes(sorted(missing))!r}")
    bits = [b for ch in text + b"\0" for b in codes[ch]]
    out = bytearray((len(bits) + 7) // 8)
    for i, b in enumerate(bits):
        out[i // 8] |= b << (i % 8)
    return bytes(out)


def text_patch(rom):
    """[(offset, bytes)] for the new texts and their table entries"""
    bank = struct.unpack_from("<I", rom, LANG_TABLE)[0] - 0x08000000
    tree_size = struct.unpack_from("<I", rom, bank)[0]
    out, at = [], TEXT_AT
    for idx, t in TEXTS:
        e = encode(rom, bank, t)
        out.append((at, e))
        out.append((bank + 4 + tree_size + 4 * idx, struct.pack("<I", at - bank)))
        at = (at + len(e) + 3) & ~3
    assert at <= 0x89864
    return out


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
    for off, old, new, _ in BYTES:
        if bytes(rom[off:off + len(old) // 2]).hex() not in (old, new):
            raise SystemExit(f"unexpected bytes at {off:#x}")
        rom[off:off + len(new) // 2] = bytes.fromhex(new)
    cur = struct.unpack_from("<I", rom, EXIT_PTR)[0]
    if cur not in (EXIT_OLD, s["exit_hook"] | 1):
        raise SystemExit(f"unexpected state table entry at {EXIT_PTR:#x}")
    struct.pack_into("<I", rom, EXIT_PTR, s["exit_hook"] | 1)
    for at, orig, name in STATE_PTRS:
        cur = struct.unpack_from("<I", rom, at)[0]
        if cur not in (orig, s[name] | 1):
            raise SystemExit(f"unexpected state table entry at {at:#x}")
        struct.pack_into("<I", rom, at, s[name] | 1)
    assert CODE_AT + len(code) <= TEXT_AT, "code runs into the new texts"
    for off, b in text_patch(rom):
        rom[off:off + len(b)] = b
    rom[CODE_AT:CODE_AT + len(code)] = code
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("Orc Head slots added ->", sys.argv[2])
