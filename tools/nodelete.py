#!/usr/bin/env python3
"""Turn off the R "Delete" button on the save slot screens (Load Game and Save).

The save slot screen (game state 9, update 0x080306EC) reads the new-press
buttons and calls 0x080313B8 when R is pressed. That routine opens the
"Delete this saved game?" prompt, and picking Yes erases the slot. The call
at 0x080307F0 becomes two no-ops, so R does nothing there.

The footer hint goes too: the word "Delete" (drawn by the bl at 0x08030CFA)
is skipped, and the R button sprite (created at 0x08031108 with x = 0x98)
is placed at x = 0xF8, off the right edge of the screen.

Saving over a slot still asks "Overwrite this saved game?" as before.

  python3 tools/nodelete.py in.gba out.gba
"""
import sys

NOP2 = b"\xc0\x46\xc0\x46"
SITES = {
    0x307F0: (b"\x00\xf0\xe2\xfd", NOP2),  # bl 0x080313B8 (R -> delete prompt)
    0x30CFA: (b"\xec\xf7\x03\xfa", NOP2),  # bl 0x0801D104 (draw "Delete")
    0x31108: (b"\x98\x21", b"\xf8\x21"),  # movs r1,#0x98 -> #0xF8 (R icon x)
}


def patch(rom: bytearray) -> bytearray:
    for at, (old, new) in SITES.items():
        n = len(old)
        if rom[at:at + n] not in (old, new):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at:at + n] = new
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("save delete turned off ->", sys.argv[2])
