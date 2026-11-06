#!/usr/bin/env python3
"""Skip in-level dialogue (the portrait + text boxes that pause the game).

Every dialogue box opens through 0x0801AD9C(textId), which stores the text id
and switches to game state 0x11 until the player presses A. It becomes a
plain return, so no box ever opens and the caller just carries on.

Level scripts open dialogue with command handler 0x08018454. In multiplayer it
already skips the box and runs the follow-up action (0x0800C4AC) right away;
its `bne` at 0x08018470 becomes `b`, so single player does the same and no
script step is lost.

  python3 tools/nodialogue.py in.gba out.gba
"""
import sys

SITES = {
    0x1AD9C: (b"\x00\xb5", b"\x70\x47"),  # push {lr} -> bx lr
    0x18470: (b"\x08\xd1", b"\x08\xe0"),  # bne -> b (multiplayer path)
}


def patch(rom: bytearray) -> bytearray:
    for at, (old, new) in SITES.items():
        if rom[at:at + 2] not in (old, new):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at:at + 2] = new
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("dialogue skipped ->", sys.argv[2])
