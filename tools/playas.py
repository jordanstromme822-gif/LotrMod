#!/usr/bin/env python3
"""Play as Sam or Smeagol: swap the hero picked on the select screen.

The select screen only has 6 slots (heroes 0-5), but Sam (6) and Smeagol (7)
have full sprites, stats and skills, because they appear in Frodo's levels.
New Game (0x080142A4) stores the picked hero at player+0x19F, starts that
hero's story, then loads stats and graphics from 0x080142E8 on. That load is
hooked: if table[picked] (6 bytes at 0x9E4F0, 0xFF = keep) names another hero,
the player becomes that hero. The story path stays the picked slot's.

  python3 tools/playas.py in.gba out.gba frodo=sam      (or smeagol, or any hero)
"""
import struct
import sys

from keystone import KS_ARCH_ARM, KS_MODE_THUMB, Ks

HEROES = ["frodo", "legolas", "aragorn", "gandalf", "eowyn", "gimli", "sam", "smeagol"]
SITE, SITE_ORIG = 0x142E8, bytes.fromhex("28780021")  # ldrb r0,[r5] ; movs r1,#0
HOOK, TABLE = 0x9E480, 0x9E4F0                          # Spanish text bank (English only)

ASM = """
    ldrb r0, [r5]
    cmp r0, #5
    bhi out
    ldr r1, =0x0809E4F0
    ldrb r1, [r1, r0]
    cmp r1, #7
    bhi out
    strb r1, [r5]
    movs r0, r1
out:
    movs r1, #0
    bx lr
    .ltorg
"""


def thumb_bl(src: int, dst: int) -> bytes:
    off = (dst - (src + 4)) >> 1
    return struct.pack("<HH", 0xF000 | ((off >> 11) & 0x7FF), 0xF800 | (off & 0x7FF))


def code() -> bytes:
    c, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(ASM, 0x08000000 + HOOK)
    return bytes(c)


def patch(rom: bytearray, swaps: dict) -> bytearray:
    if rom[SITE:SITE + 4] not in (SITE_ORIG, thumb_bl(0x08000000 + SITE, 0x08000000 + HOOK)):
        raise SystemExit(f"unexpected bytes at {SITE:#x}; is this the BLRE ROM?")
    c = code()
    rom[HOOK:HOOK + len(c)] = c
    rom[TABLE:TABLE + 6] = b"\xff" * 6
    for slot, hero in swaps.items():
        rom[TABLE + slot] = hero
    rom[SITE:SITE + 4] = thumb_bl(0x08000000 + SITE, 0x08000000 + HOOK)
    return rom


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    swaps = {}
    for arg in sys.argv[3:]:
        a, b = arg.lower().split("=")
        if HEROES.index(a) > 5:
            raise SystemExit("only the 6 select-screen heroes can be swapped")
        swaps[HEROES.index(a)] = HEROES.index(b)
    data = patch(bytearray(open(sys.argv[1], "rb").read()), swaps)
    open(sys.argv[2], "wb").write(data)
    print("hero swaps", swaps, "->", sys.argv[2])
