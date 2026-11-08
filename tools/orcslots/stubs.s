    .syntax unified
    .thumb
    .text
    .align 2
@ 0x0802DBE0: keepsake path of the item stat routine. r5 = item, sl = slot, sb = player.
@ For an Orc Head in slots 0-15, hand back a base that makes the hero-id check right after
@ (byte at hero + 0x19F == 7, Smeagol, who gets no keepsake bonus) take its "no bonus" exit.
    .global db90_stub
    .thumb_func
db90_stub:
    mov r0, sl
    cmp r0, #16
    bhs 1f
    ldr r0, =0xFF0F
    ands r0, r5
    ldr r1, =0x170E
    cmp r0, r1
    bne 1f
    mov r1, sb
    movs r2, #0xd6
    lsls r2, r2, #1
    muls r1, r2, r1
    ldr r0, =seven - 0x19F
    subs r0, r0, r1
    movs r1, #0xd6
    bx lr
1:  ldr r0, =0x03003C00
    movs r1, #0xd6
    bx lr

@ 0x0803CC08: end of the save-slot packer. r7 = header, [sp,#8] = player.
    .global pack_stub
    .thumb_func
pack_stub:
    ldr r0, [sp, #8]
    ldr r1, =0x0203FFE0
    ldrb r0, [r1, r0]
    cmp r0, #4
    bls 1f
    movs r0, #4
1:  lsls r0, r0, #5
    movs r2, #0x4b
    ldrb r1, [r7, r2]
    movs r3, #0x1f
    ands r1, r3
    orrs r1, r0
    strb r1, [r7, r2]
    movs r0, #0
    ldr r6, [sp, #0x68]
    bx lr

@ 0x0803C2A6: start of the save-slot unpacker. r4 = header, r6 = player.
    .global unpack_stub
    .thumb_func
unpack_stub:
    movs r2, #0x4b
    ldrb r2, [r4, r2]
    lsrs r2, r2, #5
    cmp r2, #4
    bls 1f
    movs r2, #4
1:  ldr r3, =0x0203FFE0
    strb r2, [r3, r6]
    ldr r3, =0x08046DC5
    bx r3

@ 0x08047F18: title screen clears the players; clear the counts too.
    .global clear_stub
    .thumb_func
clear_stub:
    ldr r3, =0x0203FFE0
    mov r12, r0
    movs r0, #0
    str r0, [r3]
    mov r0, r12
    ldr r3, =0x08032D9D
    bx r3

@ 0x0802CC60: Backpack cursor movement exit. r4 = proposed cursor.
    .global nav_stub
    .thumb_func
nav_stub:
    push {lr}
    movs r0, r4
    bl nav_c
    movs r4, r0
    mov r0, r8
    ldr r5, [r0]
    pop {r1}
    bx r1

@ 0x0802A854: A pressed in the Backpack. r7 = cursor, r6 = player.
    .global a_stub
    .thumb_func
a_stub:
    push {lr}
    cmp r7, #20
    blo 1f
    movs r0, r7
    movs r1, r6
    bl a_c
1:  ldr r2, =0x03003C00
    lsls r0, r7, #2
    pop {r1}
    bx r1
@ 0x0802CCC4: item menu up/down, r4 = cursor. Our slots get an equipment slot's two-line menu.
    .global mcur_stub
    .thumb_func
mcur_stub:
    adds r0, #0x62
    ldrb r4, [r0]
    cmp r4, #20
    blo 1f
    movs r4, #0
1:  bx lr

@ 0x0802C5FC: item menu option text, r0 = UI. Our slots read as an equipment slot ("Unequip").
    .global label_stub
    .thumb_func
label_stub:
    adds r0, #0x62
    ldrb r0, [r0]
    cmp r0, #20
    blo 1f
    movs r0, #0
1:  bx lr
    .pool
seven:
    .byte 7
    .align 2
