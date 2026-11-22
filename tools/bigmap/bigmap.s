@ Big maps read straight from ROM (2026-11-22). Placed at 0x08284C00 (zero run, see docs/findings.md).
@ The five map loads (map A, map B, metatiles A, metatiles B, collision cells) call these stubs instead of the
@ decompressor 0x08019D54, with r0 = source blob and r1 = the level's EWRAM buffer (unchanged pointer).
@ A blob whose first header byte is 0x01 is "ROM-backed": its first payload word (the [w,0,h,0] / count header)
@ is copied to the buffer so code that reads the header still finds it, and the data pointer (buffer + 4) that
@ the game reads cells from is pointed at the payload in ROM. Any other blob decompresses as before.
    .syntax unified
    .thumb
    .text
    .global stub_mapA, stub_mapB, stub_metaA, stub_metaB, stub_col
    .thumb_func
stub_mapA:  ldr r2, =0x03005fb4
            b common
    .thumb_func
stub_mapB:  ldr r2, =0x0300586c
            b common
    .thumb_func
stub_metaA: ldr r2, =0x03005fbc
            b common
    .thumb_func
stub_metaB: ldr r2, =0x03005fc0
            b common
    .thumb_func
stub_col:   ldr r2, =0x0300206c
            b common
    .thumb_func
common:     ldrb r3, [r0]
            cmp r3, #1
            bne normal
            ldr r3, [r0, #4]
            str r3, [r1]
            adds r3, r0, #4
            adds r3, #4
            str r3, [r2]
            ldr r0, [r0]
            lsrs r0, r0, #8
            bx lr
normal:     adds r3, r1, #4
            str r3, [r2]
            ldr r3, =0x08019d55
            bx r3
    .ltorg
