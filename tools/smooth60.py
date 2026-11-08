#!/usr/bin/env python3
"""Experimental 60 fps motion smoothing.

The game logic runs at 30 ticks per second: every tick is shown for two
screen refreshes. On the second refresh this hook moves every sprite and
the camera half a step further along the motion of the last tick, so
movement is drawn 60 times a second while the game itself keeps its
normal speed. Only active during gameplay (game state 1).

Hook: the last helper of the vblank handler, 0x08016D98 (called once per
vblank from 0x0802A20C, after the sprite copy and the scroll writer), jumps
to new code in the expanded ROM, which runs the original helper and then:
- on a refresh that shows a new tick (sprite buffer pointer 0x03004330
  changed): remembers the camera and sprite positions;
- on the repeat refresh: moves the scroll registers and each sprite half
  of the last tick's movement further (extrapolation, no added lag).
Needs a 32 MB ROM.

  python3 tools/smooth60.py in32mb.gba out.gba
"""
import sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HOOK_ROM = 0x1000400          # file offset in expanded space
HOOK_CPU = 0x08000000 + HOOK_ROM
TARGET = 0x16D98              # last helper of the vblank handler (single caller 0x0802A20C)
ORIG = bytes.fromhex("10b50024e1001348")
STATE = 0x0203F600            # 0x840 bytes of unused EWRAM
MAX_STEP = 12                 # bigger jumps (teleports, new objects) are not smoothed

# State layout (words): +0 last OAM buffer pointer, +4 valid, +8 last tick,
# +0x0C current camera (4 words), +0x1C previous camera, +0x2C half deltas,
# +0x40 current sprites (128 x [attr0|attr1<<16, attr2]), +0x440 previous ones.
ASM = f"""
hook:
    push {{r4-r7, lr}}
    mov r0, r8
    push {{r0}}
    bl orig                     @ run the original helper first
    ldr r7, =0x{STATE:08x}
    ldr r0, =0x030041b0         @ gameplay only
    ldr r0, [r0]
    cmp r0, #1
    beq in_game
    movs r0, #0
    str r0, [r7, #4]
    b done
in_game:
    ldr r0, =0x03004330         @ sprite buffer pointer swaps when a new tick is shown
    ldr r0, [r0]
    ldr r1, [r7]
    cmp r0, r1
    beq repeat
    @ ---------- a new tick was shown this refresh: take snapshots ----------
    str r0, [r7]
    ldr r0, =0x030041a4
    ldr r0, [r0]
    ldr r1, [r7, #8]
    str r0, [r7, #8]
    adds r1, #1
    movs r2, #0
    cmp r0, r1
    bne L1
    movs r2, #1
L1:
    str r2, [r7, #4]
    @ camera: prev = cur ; cur = live values
    ldr r0, =0x03003f59
    ldrb r0, [r0]
    lsls r0, r0, #3
    ldr r1, =0x03005fa0
    adds r1, r1, r0
    ldr r2, =0x03005880
    adds r2, r2, r0
    ldr r3, [r7, #0x0c]
    str r3, [r7, #0x1c]
    ldr r3, [r7, #0x10]
    str r3, [r7, #0x20]
    ldr r3, [r7, #0x14]
    str r3, [r7, #0x24]
    ldr r3, [r7, #0x18]
    str r3, [r7, #0x28]
    ldr r3, [r1]
    str r3, [r7, #0x0c]
    ldr r3, [r1, #4]
    str r3, [r7, #0x10]
    ldr r3, [r2]
    str r3, [r7, #0x14]
    ldr r3, [r2, #4]
    str r3, [r7, #0x18]
    @ sprites: prev = cur ; cur = hardware OAM
    ldr r4, =0x07000000
    movs r5, #0x40
    adds r5, r5, r7
    ldr r0, =0x07000400
    mov r12, r0
L2:
    movs r6, #0x80
    lsls r6, r6, #3             @ 0x400
    ldr r1, [r5]
    str r1, [r5, r6]            @ prev = cur
    adds r6, #4
    ldr r1, [r5, #4]
    str r1, [r5, r6]
    ldrh r0, [r4]
    ldrh r1, [r4, #2]
    lsls r1, r1, #16
    orrs r0, r1
    str r0, [r5]                @ cur = attr0 | attr1<<16
    ldrh r0, [r4, #4]
    str r0, [r5, #4]            @ attr2
    adds r4, #8
    adds r5, #8
    cmp r4, r12
    blt L2
    b done

repeat:
    @ ---------- the same tick is shown again: draw it half a step ahead ----------
    ldr r0, [r7, #4]
    cmp r0, #0
    bne L3
    b done
L3:
    @ camera half deltas into +0x2C..
    movs r5, #0
L4:
    movs r0, #0x0c
    adds r0, r0, r5
    ldr r1, [r7, r0]
    movs r0, #0x1c
    adds r0, r0, r5
    ldr r2, [r7, r0]
    subs r1, r1, r2
    movs r2, #{MAX_STEP}
    cmp r1, r2
    bgt L5
    negs r2, r2
    cmp r1, r2
    blt L5
    asrs r1, r1, #1
    b L6
L5:
    movs r1, #0
L6:
    movs r0, #0x2c
    adds r0, r0, r5
    str r1, [r7, r0]
    adds r5, #4
    cmp r5, #16
    blt L4
    ldr r6, =0x04000010
    ldr r0, [r7, #0x0c]
    movs r1, #7
    ands r0, r1
    ldr r1, [r7, #0x2c]
    adds r0, r0, r1
    strh r0, [r6, #8]           @ BG2HOFS
    ldr r0, [r7, #0x10]
    movs r1, #7
    ands r0, r1
    ldr r1, [r7, #0x30]
    adds r0, r0, r1
    strh r0, [r6, #10]          @ BG2VOFS
    ldr r0, [r7, #0x14]
    movs r1, #7
    ands r0, r1
    ldr r1, [r7, #0x34]
    adds r0, r0, r1
    strh r0, [r6, #12]          @ BG3HOFS
    ldr r0, =0x03005f50
    ldrh r0, [r0]
    ldr r1, [r7, #0x38]
    adds r0, r0, r1
    strh r0, [r6, #14]          @ BG3VOFS
    ldr r0, [r7, #0x14]
    ldr r1, [r7, #0x34]
    adds r0, r0, r1
    asrs r0, r0, #2
    strh r0, [r6, #4]           @ BG1HOFS
    ldr r0, [r7, #0x18]
    ldr r1, [r7, #0x38]
    adds r0, r0, r1
    asrs r0, r0, #2
    strh r0, [r6, #6]           @ BG1VOFS
    @ sprites
    ldr r4, =0x07000000
    movs r5, #0x40
    adds r5, r5, r7
    ldr r0, =0x07000400
    mov r12, r0
L7:
    movs r6, #0x80
    lsls r6, r6, #3
    adds r6, #4
    ldr r1, [r5, r6]            @ prev attr2
    ldr r0, [r5, #4]            @ cur attr2
    eors r0, r1
    lsrs r0, r0, #10            @ same palette and priority (tiles may change with animation)
    bne L8
    ldr r0, [r5]                @ cur
    subs r6, #4
    ldr r1, [r5, r6]            @ prev
    @ same kind of sprite? attr0 bits 8,9,14,15 and attr1 bits 14,15
    movs r2, r0
    eors r2, r1
    ldr r3, =0xC000C300
    ands r2, r3
    bne L8
    @ dy = cur.y - prev.y (8 bit signed)
    lsls r2, r0, #24
    lsls r3, r1, #24
    subs r2, r2, r3
    asrs r2, r2, #24
    @ dx = cur.x - prev.x (9 bit signed)
    lsls r3, r0, #7
    lsls r6, r1, #7
    subs r3, r3, r6
    asrs r3, r3, #23
    movs r6, #{MAX_STEP}
    cmp r2, r6
    bgt L8
    cmp r3, r6
    bgt L8
    negs r6, r6
    cmp r2, r6
    blt L8
    cmp r3, r6
    blt L8
    asrs r2, r2, #1
    asrs r3, r3, #1
    @ write into the hardware entry, keeping its other bits
    ldrh r1, [r4]
    adds r2, r0, r2
    lsls r2, r2, #24
    lsrs r2, r2, #24
    lsrs r1, r1, #8
    lsls r1, r1, #8
    orrs r1, r2
    strh r1, [r4]
    ldrh r1, [r4, #2]
    lsrs r0, r0, #16
    adds r3, r0, r3
    lsls r3, r3, #23
    lsrs r3, r3, #23
    lsrs r1, r1, #9
    lsls r1, r1, #9
    orrs r1, r3
    strh r1, [r4, #2]
L8:
    adds r4, #8
    adds r5, #8
    cmp r4, r12
    blt L7

done:
    pop {{r0}}
    mov r8, r0
    pop {{r4-r7}}
    pop {{r0}}
    bx r0

orig:                           @ first 8 bytes of 0x08016D98, then continue there
    push {{r4, lr}}
    movs r4, #0
    lsls r1, r4, #3
    ldr r0, =0x03003560
    ldr r3, =0x08016da1
    bx r3
"""


def build():
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    code, _ = ks.asm(ASM, HOOK_CPU)
    return bytes(code)


def patch(rom: bytearray) -> bytearray:
    if len(rom) < 0x2000000:
        raise SystemExit("expand the ROM to 32 MB first (tools/expand.py)")
    if rom[TARGET:TARGET + 8] not in (ORIG,) and rom[TARGET:TARGET + 4] != bytes.fromhex("00480047"):
        raise SystemExit("unexpected bytes at 0x16D98")
    code = build()
    rom[HOOK_ROM:HOOK_ROM + len(code)] = code
    rom[TARGET:TARGET + 8] = bytes.fromhex("00480047") + (HOOK_CPU | 1).to_bytes(4, "little")
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    rom = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(rom)
    print(f"60 fps smoothing hook: {len(build())} bytes at {HOOK_CPU:#x} -> {sys.argv[2]}")
