@ Extra sprite tiles (engine upgrade 2026-11-10): tile numbers 1024-2047 keep bit 10
@ in OAM attr0 bit 12 (OBJ mosaic, never used by this game). Each stub replaces the
@ game's "tile & 0x3FF" at one place that builds an OAM entry or an OAM template.
    .syntax unified
    .thumb
    .text
@ set bit 12 of r0 from bit 10 of r1 (uses r2)
    .macro BIT12 rt
    ldr  \rt, =0x1000
    bics r0, \rt
    lsls \rt, r1, #21
    lsrs \rt, \rt, #31
    lsls \rt, \rt, #12
    orrs r0, \rt
    .endm

@ 0x08002D6A: r1 = tile, OAM entry word0 (attr0|attr1<<16) at [r4]. Clobbers r0, r2.
    .global bs_e1
    .thumb_func
bs_e1:
    ldr  r0, [r4]
    BIT12 r2
    str  r0, [r4]
    lsls r1, r1, #22
    lsrs r1, r1, #22
    bx   lr

@ 0x0800262C: r1 = tile, OAM entry word0 at caller's [sp, #0x14]. Clobbers r0, r2.
    .global bs_e3
    .thumb_func
bs_e3:
    ldr  r0, [sp, #0x14]
    BIT12 r2
    str  r0, [sp, #0x14]
    lsls r1, r1, #22
    lsrs r1, r1, #22
    bx   lr

@ 0x08039406: r1 = tile, OAM entry word0 at [r6]. Clobbers r0, r2.
    .global bs_e7
    .thumb_func
bs_e7:
    ldr  r0, [r6]
    BIT12 r2
    str  r0, [r6]
    lsls r1, r1, #22
    lsrs r1, r1, #22
    bx   lr

@ 0x08002C72: next piece of a template sprite. r2 = attr2, r5 = &template attr2,
@ r6 = object. Tile += (byte [obj+0xDF] >> 6) * 4 with bit 10 kept in attr0 bit 12.
@ Out: r2 = new attr2, r3 = 0x3FF, r4 = 0xFFFFFC00 (as the game left them). Clobbers r0, r1.
    .global bs_e2
    .thumb_func
bs_e2:
    ldr  r3, =0x3FF
    movs r1, r2
    ands r1, r3
    subs r5, #4
    ldrh r0, [r5]
    lsls r4, r0, #19
    lsrs r4, r4, #31
    lsls r4, r4, #10
    orrs r1, r4
    movs r4, r6
    adds r4, #0xDF
    ldrb r4, [r4]
    lsrs r4, r4, #6
    lsls r4, r4, #2
    adds r1, r1, r4
    BIT12 r4
    strh r0, [r5]
    adds r5, #4
    ands r1, r3
    ldr  r4, =0xFFFFFC00
    ands r2, r4
    orrs r2, r1
    bx   lr

@ store tile r1 into template attr2 at [r3] (attr0 at [r3-4]); 0xFFFF keeps bit 12 clear.
@ Clobbers r0, r1, r2.
    .thumb_func
tmpl_store:
    ldr  r2, =0xFFFF
    cmp  r1, r2
    bne  1f
    ldr  r1, =0x3FF
1:  subs r3, #4
    ldrh r0, [r3]
    BIT12 r2
    strh r0, [r3]
    adds r3, #4
    ldr  r2, =0x3FF
    ands r1, r2
    ldrh r0, [r3]
    ldr  r2, =0xFFFFFC00
    ands r0, r2
    orrs r0, r1
    strh r0, [r3]
    bx   lr

@ 0x08003398: tile = caller [sp, #0x10], template attr2 = caller [sp, #0x20]. Clobbers r0-r3.
    .global bs_e4
    .thumb_func
bs_e4:
    ldr  r1, [sp, #0x10]
    ldr  r2, =0xFFFF
    ands r1, r2
    ldr  r3, [sp, #0x20]
    b    tmpl_store

@ 0x08047B20: r0 = tile, r5 = object (template attr2 at +0xE0). Clobbers r0-r3.
    .global bs_e5
    .thumb_func
bs_e5:
    movs r1, r0
    movs r3, r5
    adds r3, #0xE0
    b    tmpl_store

@ 0x08002BE6: r0 = tile, r6 = object. Must leave r4 = obj + 0xE0 and keep r3. Clobbers r0-r2.
    .global bs_e6
    .thumb_func
bs_e6:
    push {r3, lr}
    movs r1, r0
    movs r3, r6
    adds r3, #0xE0
    movs r4, r3
    bl   tmpl_store
    pop  {r3}
    pop  {r0}
    bx   r0
    .ltorg
