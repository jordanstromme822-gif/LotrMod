@ Big maps read straight from ROM (2026-11-22). Placed at 0x08284C00 (zero run, see docs/findings.md).
@ The five map loads (map A, map B, metatiles A, metatiles B, collision cells) call these stubs instead of the
@ decompressor 0x08019D54, with r0 = source blob and r1 = the level's EWRAM buffer (unchanged pointer).
@ A blob whose first header byte is 0x01 is "ROM-backed": its first payload word (the [w,0,h,0] / count header)
@ is copied to the buffer so code that reads the header still finds it, and the data pointer (buffer + 4) that
@ the game reads cells from is pointed at the payload in ROM. Any other blob decompresses as before.
    .syntax unified
    .thumb
    .text
    .global stub_mapA, stub_mapB, stub_metaA, stub_metaB, stub_col, bm_frame
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

@ bm_frame: called each gameplay tick in place of 0x080016F8 (bl at 0x08031ED4); calls it, keeps its r0, then
@ keeps the right tile set in VRAM on a joined level. Table at ROM 0x09700000 (written by tools/join):
@   +0 'BMAP', +4 entry count, then 32-byte entries:
@   +0 level, +4 split y (px; the local hero above it gets set 0, below gets set 1), +8 VRAM halfword address to check,
@   +C u16 value there for set 0, +E u16 for set 1, +10 tileset, +14 set 0 layer A list, +18 set 0 layer B list,
@   +1C set 1 layer A list, +20 set 1 layer B list   (entries are 0x24 bytes)
    .thumb_func
bm_frame:   push {r4, r5, r6, r7, lr}
            ldr r4, =0x080016f9
            bl call_r4
            push {r0}
            ldr r5, =0x09700000
            ldr r0, [r5]
            ldr r1, =0x50414d42       @ 'BMAP'
            cmp r0, r1
            bne done
            ldr r6, [r5, #4]          @ entry count
            adds r5, #8
            ldr r0, =0x03004174
            ldrb r0, [r0]
find:       cmp r6, #0
            beq done
            ldr r1, [r5]
            cmp r0, r1
            beq found
            adds r5, #0x24
            subs r6, #1
            b find
found:      ldr r0, =0x03003f59      @ local player
            ldrb r0, [r0]
            movs r1, #0xd6
            lsls r1, r1, #1           @ 0x1ac
            muls r0, r1, r0
            ldr r1, =0x03003c00
            ldr r0, [r1, r0]          @ local hero object
            cmp r0, #0
            beq done
            adds r0, #0xd2
            movs r1, #0
            ldrsh r0, [r0, r1]        @ hero y (px)
            ldr r1, [r5, #4]
            ldr r2, [r5, #8]
            ldrh r2, [r2]             @ what VRAM holds now
            movs r7, #0x14            @ set 0 lists at +0x14
            ldrh r3, [r5, #0xc]
            cmp r0, r1
            blt chk
            movs r7, #0x1c            @ set 1 lists at +0x1c
            ldrh r3, [r5, #0xe]
chk:        cmp r2, r3
            beq done
            ldr r0, [r5, #0x10]
            ldr r1, [r5, r7]
            ldr r2, =0x08069904
            ldr r4, =0x080324c9
            bl call_r4
            adds r7, #4
            ldr r0, [r5, #0x10]
            ldr r1, [r5, r7]
            ldr r2, =0x08069900
            ldr r4, =0x080324c9
            bl call_r4
done:       pop {r0}
            pop {r4, r5, r6, r7}
            pop {r3}
            bx r3
    .thumb_func
call_r4:    bx r4
    .ltorg
