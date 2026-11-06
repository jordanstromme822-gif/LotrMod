#!/usr/bin/env python3
"""Stop the Ranger Hollow item dupe by keeping each play session to one save slot.

The dupe: save the same game into several slots, load each copy and put its items
into the Ranger Hollow (shared by all slots), then take them out in the main game.
It needs one game saved into more than one slot, so this patch blocks that:

  - A small lock byte in unused EWRAM (0x0203FFF0, slot + 1, 0 = none) remembers the
    slot this session belongs to.
  - Loading a slot (0x08031490, bl at 0x080314B4) or saving to one (0x08030F08 with
    arg 1, bl at 0x08030FDA) sets the lock. Both sites still store the slot in
    0x03005834 as before.
  - On the save screen, A on a slot (0x080309C8) checks the lock: a different slot
    just plays the cancel sound and nothing is saved. The locked slot, or any slot
    before the first save of a new game, saves as normal.
  - Going back to the title screen (state 5 init, bl at 0x08047EFA) clears the lock,
    so New Game can pick any slot again.

Routines live at 0x0809E820 (88 bytes) in the unused Spanish text bank.

  python3 tools/nodupe.py in.gba out.gba
"""
import sys

CODE_AT = 0x9E820
CODE = bytes.fromhex(
    "0f490878002805d0e2680132904201d00c480047812d00d870470b4800470b48c0680870002d02d00130094a"
    "1070704700b5084900200870a8f7b4fc01bc0047f0ff0302f10b0308d5090308b0410003f0ff0302f0ff0302")
SITES = {
    0x309C8: ("812d03d8", "6df02aff"),  # cmp r5,#0x81; bhi  -> bl check
    0x314B4: ("e8680870", "6df0c3f9"),  # load: last slot    -> bl setlock
    0x30FDA: ("e0680870", "6df030fc"),  # save: last slot    -> bl setlock
    0x47EFA: ("fff763f9", "56f0a9fc"),  # title init         -> bl clear
}


def patch(rom: bytearray) -> bytearray:
    for at, (old, new) in SITES.items():
        old, new = bytes.fromhex(old), bytes.fromhex(new)
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
    print("one slot per session (no Ranger Hollow dupe) ->", sys.argv[2])
