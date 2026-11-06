#!/usr/bin/env python3
"""Refund skill points on the Skills page: L + SELECT takes one level back off a skill.

On the in-game Skills page, pressing L and SELECT together on a skill removes one
level from it and puts the 1 skill point it cost back in the point pool. It only
ever gives back points the player spent: Herbal Healing keeps the free level every
hero starts with, and a skill at 0 (or a skill the hero doesn't have) just plays
the game's "can't do that" sound. Each level costs exactly 1 point to buy, so each
refund gives exactly 1 back.

How the game stores skills (player struct P = 0x03003C00 + 0x1AC * player):
  - Skill points: P + 0x19E (byte). Buying a level costs 1.
  - Active skills (right side, 6 incl. Herbal Healing): bought level P + 0x16A + i,
    level in use P + 0x170 + i. 0x08045138(p, i, d) adds d to both. New heroes
    start with Herbal Healing (i = 5) at 1 (0x08026590), everything else at 0.
  - Passive skills (left 3x3 grid): the hero's 9 passive ids are listed at [P + 0x18];
    bought level P + 0x158 + slot, level in use P + 0x161 + slot. Buying
    (0x08042BC4) raises both and applies that level's bonuses with
    0x0804539C(p, slot, +1); 0x0804539C(p, slot, -1) takes the same bonuses off
    again (the game uses it when a temporary "+1 to all passives" wears off).
    Passive 19 (Fleet of Foot) also sets the "recompute speed" flag 0x40 in
    P + 0x18C, done here as well.
  - The page's key handler is 0x080416B4 (A buys through 0x08041F78, SELECT sets the
    B skill, L/R switch page, B/START close). Held keys: 0x03004088 + 2 * player,
    new presses this tick: 0x03004094 + 2 * player. Panel 0x030041C0 (1 active,
    2 passive), cursor 0x030041B8, passive ids by cursor at 0x03006A10.

Two-player link play: there, buying a level is sent as a link message (0x22 active,
0x21 passive) that both GBAs apply on the same frame. A refund is sent as the same
message with bit 7 set in its first byte (the cursor, never above 8), and the two
message cases (jump table 0x0803F69C) go through a wrapper that applies refunds and
passes everything else to the game's own code. So both players' games stay in step.

Saves: the save keeps the bought levels and points (both are in the player struct
the game already saves) and recomputes the levels in use and every passive bonus
from the bought levels when a game loads (0x08042B6C), so a refunded save loads the
same as one where the points were never spent.

Code: 0x0809EA00 (entries: +0 key hook, +2 / +4 link cases) in the unused Spanish text bank (needs the English-only patch, as
every Play Room "Modded" patch does). Sites:
  0x08041702  movs r0,#1; ands r0,r3  ->  bl keyhook
  0x0803F720  link case 0x21          ->  wrap21
  0x0803F724  link case 0x22          ->  wrap22

  python3 tools/skillrefund.py in.gba out.gba
"""
import struct
import sys

CODE_AT = 0x9EA00
BASE = 0x08000000 + CODE_AT

ASM = """
    b keyhook                   @ +0: key hook (bl target)
    b wrap21                    @ +2: link case 0x21 (passive)
    b wrap22                    @ +4: link case 0x22 (active)
keyhook:                        @ r0 = &new presses (local), r3 = new presses
    push {r4, lr}
    movs r4, r0
    subs r4, #0x0c
    ldrh r4, [r4]               @ held keys
    ldr r1, =0x204              @ L | SELECT (GBA key bits: L = 0x200, R = 0x100)
    ands r4, r1
    cmp r4, r1
    bne normal
    tst r3, r1                  @ one of them pressed just now
    beq normal
    movs r4, #0
    strh r4, [r0]               @ swallow this tick's presses: no page switch, no B-skill change
    bl refund
    movs r3, #0
    movs r0, #0
    b keyout
normal:
    movs r0, #1
    ands r0, r3
keyout:
    ldr r1, =0x03003C00
    ldr r2, =0x03004094
    pop {r4, pc}

refund:                         @ the local player asks for a refund on the cursor's skill
    push {r4, r5, r6, r7, lr}
    sub sp, #16
    ldr r0, =0x03003F59
    ldrb r6, [r0]               @ p
    movs r0, r6
    bl paddr
    movs r5, r0                 @ P
    ldr r4, =0x030041B0
    ldr r0, [r4, #0x10]         @ panel
    ldr r7, [r4, #8]            @ cursor
    movs r1, #0
    str r1, [sp, #0]
    str r1, [sp, #4]
    str r1, [sp, #8]
    cmp r0, #1
    beq ractive
    cmp r0, #2
    bne rfail
    cmp r7, #8
    bhi rfail
    ldr r0, =0x03006A10
    ldrb r4, [r0, r7]           @ passive id
    movs r0, r6
    movs r1, r4
    bl 0x08045020               @ slot of that id (9 = none)
    cmp r0, #8
    bhi rfail
    movs r3, r0
    adds r0, r5, r3
    ldr r1, =0x158
    ldrsb r2, [r0, r1]          @ bought level
    cmp r2, #0
    ble rfail
    mov r0, sp
    strb r4, [r0, #1]
    strb r3, [r0, #2]
    movs r1, #0x21
    b rsend
ractive:
    cmp r7, #5
    bhi rfail
    adds r0, r5, r7
    ldr r1, =0x16A
    ldrsb r2, [r0, r1]          @ bought level
    movs r1, #0
    cmp r7, #5
    bne afloor
    movs r1, #1                 @ Herbal Healing's free level stays
afloor:
    cmp r2, r1
    ble rfail
    mov r0, sp
    strb r7, [r0, #2]
    movs r1, #0x22
rsend:
    mov r0, sp
    movs r2, #0x80
    orrs r2, r7
    strb r2, [r0, #0]           @ cursor | 0x80 = refund
    ldr r2, =0x03004144
    ldr r2, [r2]
    movs r3, #0x20
    tst r2, r3
    beq rlocal
    movs r0, r1                 @ linked: send it, both GBAs apply it via the wrappers
    ldr r1, [sp, #0]
    ldr r2, [sp, #4]
    ldr r3, [sp, #8]
    bl 0x0803FDF0
    b rdone
rlocal:
    movs r0, r1
    movs r1, r6
    mov r2, sp
    movs r3, #0
    bl apply
    b rdone
rfail:
    movs r0, #5
    bl 0x08046EEC
rdone:
    add sp, #16
    pop {r4, r5, r6, r7, pc}

apply:                          @ r0 = 0x21/0x22, r1 = p, r2 = payload, r3 = 1 if from the other player
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    str r3, [sp, #0]
    movs r6, r1                 @ p
    ldrb r4, [r2, #0]
    movs r3, #0x7f
    ands r4, r3                 @ cursor
    ldrb r7, [r2, #1]           @ passive id
    ldrb r3, [r2, #2]           @ slot / active skill
    str r3, [sp, #4]
    movs r5, r0
    movs r0, r6
    bl paddr
    ldr r3, [sp, #4]
    cmp r5, #0x22
    beq aactive
                                @ ---- passive ----
    cmp r3, #8
    bhi aout
    adds r5, r0, r3             @ P + slot
    ldr r1, =0x158
    ldrb r2, [r5, r1]
    lsls r2, r2, #24
    asrs r2, r2, #24
    cmp r2, #0
    ble aout
    subs r2, #1
    strb r2, [r5, r1]           @ bought level - 1
    ldr r1, =0x161
    ldrb r2, [r5, r1]
    lsls r2, r2, #24
    asrs r2, r2, #24
    cmp r2, #0
    ble anoeff
    movs r0, r6
    movs r1, r3
    movs r2, #0xff
    bl 0x0804539C               @ take this level's bonuses off
    ldr r1, =0x161
    ldrb r2, [r5, r1]
    subs r2, #1
    strb r2, [r5, r1]           @ level in use - 1
anoeff:
    cmp r7, #19
    bne apoints
    movs r0, r6
    bl paddr
    ldr r1, =0x18C
    ldrh r2, [r0, r1]
    movs r3, #0x40
    orrs r2, r3
    strh r2, [r0, r1]
    b apoints
aactive:                        @ ---- active ----
    cmp r3, #5
    bhi aout
    adds r1, r0, r3
    ldr r2, =0x16A
    ldrsb r2, [r1, r2]
    movs r1, #0
    cmp r3, #5
    bne afl2
    movs r1, #1
afl2:
    cmp r2, r1
    ble aout
    movs r0, r6
    movs r1, r3
    movs r2, #0xff
    bl 0x08045138               @ bought level and level in use - 1
apoints:
    movs r0, r6
    bl paddr
    ldr r1, =0x19E
    ldrb r2, [r0, r1]
    cmp r2, #0xff
    beq aredraw
    adds r2, #1
    strb r2, [r0, r1]           @ the point goes back
aredraw:
    ldr r0, [sp, #0]
    cmp r0, #0
    bne aout                    @ only the refunding player's screen is redrawn
    movs r0, r6
    bl 0x08042704               @ point count
    movs r0, r6
    bl paddr
    ldr r3, [sp, #4]
    cmp r5, #0x22
    beq ardact
    movs r1, r7
    ldr r2, =0x161
    adds r0, r0, r3
    ldrb r3, [r0, r2]
    movs r0, r6
    movs r2, r4
    bl 0x08041C84               @ passive icon + level boxes
    movs r5, #0x31
    b ardend
ardact:
    movs r1, r3
    ldr r2, =0x170
    adds r0, r0, r3
    ldrb r3, [r0, r2]
    movs r0, r6
    movs r2, r4
    bl 0x08041DA0               @ active icon + level boxes
    movs r5, #0x32
ardend:
    bl 0x080421F8               @ description text
    movs r0, r5
    bl 0x08046EEC               @ same sound as buying
aout:
    add sp, #8
    pop {r4, r5, r6, r7, pc}

paddr:                          @ r0 = p -> r0 = player struct
    movs r1, #0xd6
    lsls r1, r1, #1
    muls r0, r1
    ldr r1, =0x03003C00
    adds r0, r0, r1
    bx lr

wrap21:                         @ link message cases: entered by mov pc (Thumb), r6 = message,
    ldrb r0, [r6, #4]           @ r9 = sending player, r7 = 1 if that is the other GBA's player
    cmp r0, #0x7f
    bhi wref21
    ldr r0, =0x0803F9BC
    mov pc, r0
wref21:
    movs r0, #0x21
    b wref
wrap22:
    ldrb r0, [r6, #4]
    cmp r0, #0x7f
    bhi wref22
    ldr r0, =0x0803FA20
    mov pc, r0
wref22:
    movs r0, #0x22
wref:
    mov r1, r9
    adds r2, r6, #4
    movs r3, r7
    bl apply
    ldr r0, =0x0803FDAD
    bx r0
    .ltorg
"""

KEY_SITE = 0x41702
KEY_ORIG = bytes.fromhex("01201840")      # movs r0,#1 ; ands r0,r3
CASES = {0x3F720: 0x0803F9BC, 0x3F724: 0x0803FA20}


def thumb_bl(src: int, dst: int) -> bytes:
    off = (dst - (src + 4)) >> 1
    return struct.pack("<HH", 0xF000 | ((off >> 11) & 0x7FF), 0xF800 | (off & 0x7FF))


def assemble():
    from keystone import KS_ARCH_ARM, KS_MODE_THUMB, Ks
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    code = bytes(ks.asm(ASM, BASE)[0])
    pool = code.find(struct.pack("<I", 0x204))   # first literal: the pool after the code
    i = 0
    while i < pool:                        # Thumb-1 only (GBA is ARMv4T); BL pairs are fine
        hw = struct.unpack_from("<H", code, i)[0]
        if hw >> 11 == 0x1E:
            i += 4
            continue
        if hw >> 11 in (0x1D, 0x1F):
            raise SystemExit(f"Thumb-2 instruction at +{i:#x}")
        i += 2
    syms = {"keyhook": 0, "wrap21": 2, "wrap22": 4}
    return code, syms


def patch(rom: bytearray) -> bytearray:
    code, syms = assemble()
    hook_bl = thumb_bl(0x08000000 + KEY_SITE, BASE + syms["keyhook"])
    if rom[KEY_SITE:KEY_SITE + 4] not in (KEY_ORIG, hook_bl):
        raise SystemExit(f"unexpected bytes at {KEY_SITE:#x}; is this the BLRE ROM?")
    for at, orig in CASES.items():
        cur = struct.unpack_from("<I", rom, at)[0]
        if cur not in (orig, BASE + syms["wrap21" if at == 0x3F720 else "wrap22"]):
            raise SystemExit(f"unexpected link case at {at:#x}")
    rom[CODE_AT:CODE_AT + len(code)] = code
    rom[KEY_SITE:KEY_SITE + 4] = hook_bl
    struct.pack_into("<I", rom, 0x3F720, BASE + syms["wrap21"])
    struct.pack_into("<I", rom, 0x3F724, BASE + syms["wrap22"])
    return rom


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = patch(bytearray(open(sys.argv[1], "rb").read()))
    open(sys.argv[2], "wb").write(data)
    print("L + SELECT refunds a skill point on the Skills page ->", sys.argv[2])
