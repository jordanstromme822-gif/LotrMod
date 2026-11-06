#!/usr/bin/env python3
"""Skip the story cutscenes (the still-picture slides with captions).

Story slides live in a table at 0x0806F68C (0x2C bytes each): +0x24 level arg,
+0x25 type (4 first slide, 5 middle, 6 last), +0x26 next slide. Every slide is
shown by entering game state 7; when the last one ends the sequencer at
0x08045E78 calls setState2(1, last.+0x24, [0x030041BC]) to start the level.

This patch hooks state 7's enter code (0x0804587E): it follows the chain to the
last slide and queues that same setState2(1, ...) right away, so the level
starts without showing any slides. Slides of other types (0-3) are left alone.

The hook code goes in the Spanish text bank (0x9E330), which is unused because
every language entry is pointed at English (Jordan chose English only).

  python3 tools/nocutscenes.py in.gba out.gba
"""
import struct
import sys

from keystone import KS_ARCH_ARM, KS_MODE_THUMB, Ks

LANG_TABLE, ENGLISH = 0x289A10, 0x0807500C
SITE = 0x4587E                     # ldr r5,[pc,#0x28] ; ldr r0,[r4,#8]
SITE_ORIG = bytes.fromhex("0a4da068")
HOOK = 0x9E400                     # inside the (now unused) Spanish bank

ASM = """
    push {r1, r2, r3, r6, lr}
    ldr r5, =0x0806F68C
    ldr r0, [r4, #8]
    movs r1, r0
    movs r6, #64
walk:
    movs r2, #0x2c
    muls r2, r1
    adds r2, r2, r5
    adds r2, #0x24
    ldrb r3, [r2, #1]
    cmp r3, #6
    beq found
    cmp r3, #4
    blo done
    cmp r3, #5
    bhi done
    ldrb r1, [r2, #2]
    subs r6, #1
    bne walk
    b done
found:
    str r1, [r4, #8]
    ldrb r1, [r2, #0]
    ldr r2, [r4, #0xc]
    movs r0, #1
    ldr r3, =0x08033171
    bl callr3
    ldr r0, [r4, #8]
done:
    pop {r1, r2, r3, r6, pc}
callr3:
    bx r3
    .ltorg
"""


def thumb_bl(src: int, dst: int) -> bytes:
    off = (dst - (src + 4)) >> 1
    hi = 0xF000 | ((off >> 11) & 0x7FF)
    lo = 0xF800 | (off & 0x7FF)
    return struct.pack("<HH", hi, lo)


def patch(rom: bytearray) -> bytearray:
    if rom[SITE:SITE + 4] not in (SITE_ORIG, thumb_bl(0x08000000 + SITE, 0x08000000 + HOOK)):
        raise SystemExit(f"unexpected bytes at {SITE:#x}; is this the BLRE ROM?")
    for i in range(1, 5):  # English only: frees the other banks
        struct.pack_into("<I", rom, LANG_TABLE + 4 * i, ENGLISH)
    code, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(ASM, 0x08000000 + HOOK)
    code = bytes(code)
    # GBA is ARMv4T: refuse any 32-bit Thumb-2 instruction other than BL pairs.
    i = 0
    while i < len(code):
        hw = struct.unpack_from("<H", code, i)[0]
        if hw >> 11 == 0x1E:
            i += 4
            continue
        if hw >> 11 in (0x1D, 0x1F):
            raise SystemExit(f"Thumb-2 instruction in hook at +{i:#x}")
        i += 2
    rom[HOOK:HOOK + len(code)] = code
    rom[SITE:SITE + 4] = thumb_bl(0x08000000 + SITE, 0x08000000 + HOOK)
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("story cutscenes skipped ->", sys.argv[2])
