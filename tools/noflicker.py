#!/usr/bin/env python3
"""Show hero/enemy reflections on every frame instead of every other one.

Each OAM buffer (0x03004340 and 0x03004B80) holds two 1 KB sprite images.
Image 0 has everything including the water reflections (vertically flipped,
priority 3 sprites under the blended BG2 water); image 1 is the same minus
the reflections. The vblank handler at 0x0802A0F0 flips a toggle
(0x03001F18) every frame and DMAs image (toggle) to OAM, which makes the
reflections flicker on fast screens. The four `lsls r0, r3, #10` that pick
the image are changed to `movs r0, #0`, so image 0 is always shown.

  python3 tools/noflicker.py in.gba out.gba
"""
import sys

SITES = (0x2A118, 0x2A152, 0x2A1C0, 0x2A1E6)  # lsls r0,r3,#10 (98 02) -> movs r0,#0 (00 20)


def patch(rom: bytearray) -> bytearray:
    for at in SITES:
        if rom[at:at + 2] not in (b"\x98\x02", b"\x00\x20"):
            raise SystemExit(f"unexpected bytes at {at:#x}; is this the BLRE ROM?")
        rom[at:at + 2] = b"\x00\x20"
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("reflections steady ->", sys.argv[2])
