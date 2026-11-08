#!/usr/bin/env python3
"""Orc Head slots: 4 slots under the Backpack grid, one Orc Head each (Jordan, 2026-11-08).

Orc Heads give their +1 Courage only from these slots. An Orc Head in the normal
backpack gives nothing. On the Backpack screen, press Down from the bottom row of
the backpack to reach the slots. A on an empty slot moves an Orc Head in from the
backpack, A on a full slot puts it back. The slots are locked in 2-player games
(their bonus still counts there).

How it works (details in docs/findings.md, "Orc Head slots"):
  - Keepsake items (category list word bit 16) add their stats from the backpack
    through 0x0802DB90(item, slot, player, remove). Its keepsake path (0x0802DBE0)
    now returns early for an Orc Head in slots 0-15. Our slots call it with slot 16.
  - Loading and level-ups rebuild stats from base + all items (0x0802AC24, called
    at 0x08026014); the wrapper adds one Orc Head per filled slot.
  - The number of filled slots per player is a byte at 0x0203FFE0 + player. It is
    saved in bits 5-7 of save-slot header byte 0x4B, which the game never writes
    or reads (checked by running its packer and unpacker), so it also travels with
    the hero in link play. The title screen clears it.
  - Screen: the second grid row's boxes are copied one row down on BG0; the text
    layer (BG1) is shown from a copy (screenblock 0x1B) with the text moved down
    three tile rows (one empty row dropped); the Orc Head pictures are sprites
    (tiles 1000-1011, palette 7); the cursor and A press are hooked for slots 20-23.
  - The Orc Head's description (text 418) says where it works now.

The code is C + a few assembly stubs in tools/orcslots/ (build.py needs clang and
ld.lld); the built bytes are in tools/orcslots/orcslots.bin and go in the unused
Spanish text bank at 0x9F000, so the English-only patch must come first.

  python3 tools/orcslots.py in.gba out.gba
"""
import os
import struct
import sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orcslots")
CODE_AT = 0x9F000
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
    (0x2CC60, "40460568", "nav_stub"),    # Backpack cursor movement
    (0x2A854, "2a4ab800", "a_stub"),      # A in the Backpack
    (0x2AC0A, "0bf04bfd", "frame_hook"),  # end of the Backpack frame (sprites done)
    (0x2A704, "0bf0ceff", "frame_hook"),  # Backpack enter
    (0x2AB9E, "1cf0a5f9", "sound_wrap"),  # the Backpack's "can't do that" sound (skipped after our A action)
]
# The Orc Head's description (text 418, table entry 417) is re-encoded with the English Huffman tree
# and placed in free space; only its offset in the string table changes.
LANG_TABLE, TEXT_IDX, TEXT_AT = 0x289A10, 417, 0x9FC00
ORC_TEXT = b"+1 Courage, but only from an Orc Head slot (the row under your backpack)."
EXIT_PTR, EXIT_OLD = 0x6C8A8, 0x0802E875     # state 0x0A (Backpack) exit in the state table


def encode(rom, bank, text):
    """Huffman-encode text (plus the 0 terminator) with the bank's own tree (see tools/text.py)."""
    tree_size = struct.unpack_from("<I", rom, bank)[0]
    codes, todo = {}, [(0x100, [])]
    while todo:
        node, path = todo.pop()
        e = bank + 4 + (node - 0x100) * 4
        for bit in (0, 1):
            child = struct.unpack_from("<H", rom, e + 2 * bit)[0]
            if child == 0x100:
                continue                      # a link back to the root; never needed to encode
            if child > 0xFF:
                todo.append((child, path + [bit]))
            else:
                codes.setdefault(child, path + [bit])
    bits = [b for ch in text + b"\0" for b in codes[ch]]
    out = bytearray((len(bits) + 7) // 8)
    for i, b in enumerate(bits):
        out[i // 8] |= b << (i % 8)
    return bytes(out)


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
    bank = struct.unpack_from("<I", rom, LANG_TABLE)[0] - 0x08000000
    enc = encode(rom, bank, ORC_TEXT)
    rom[TEXT_AT:TEXT_AT + len(enc)] = enc
    tree_size = struct.unpack_from("<I", rom, bank)[0]
    struct.pack_into("<I", rom, bank + 4 + tree_size + 4 * TEXT_IDX, TEXT_AT - bank)
    cur = struct.unpack_from("<I", rom, EXIT_PTR)[0]
    if cur not in (EXIT_OLD, s["exit_hook"] | 1):
        raise SystemExit(f"unexpected state table entry at {EXIT_PTR:#x}")
    struct.pack_into("<I", rom, EXIT_PTR, s["exit_hook"] | 1)
    rom[CODE_AT:CODE_AT + len(code)] = code
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("Orc Head slots added ->", sys.argv[2])
