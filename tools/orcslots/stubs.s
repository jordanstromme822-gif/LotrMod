    .syntax unified
    .thumb
    .text
    .align 2
@ Receive case for link message 4 (table 0x0803F69C): r6 = message, r9 = sending player.
@ Kept first and self-contained (no calls, its own literals) so its bytes never change: the 2-player
@ Wide engine has it compiled natively (game-link.toml extra_func 0x0807F000). A bridged case handler
@ that jumps back into the game's receive loop crashed that engine. It only stores the 4 heads
@ (CONF[p], 0x0203FF38 + 8 p) and marks them pending (CONFV[p] = 2); gp_hook puts them on.
    .global recv4
    .thumb_func
recv4:
    mov r0, r9
    cmp r0, #3
    bhi 1f
    lsls r1, r0, #3
    ldr r2, =0x0203FF38
    adds r2, r2, r1
    ldr r1, [r6, #4]
    str r1, [r2]
    ldr r1, [r6, #8]
    str r1, [r2, #4]
    ldr r2, =0x0203FF58
    movs r1, #2
    strb r1, [r2, r0]
1:  ldr r0, =0x0803FDAD
    bx r0
    .pool
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
@ pack_c stores the slot count in header byte 0x4B bits 5-7 and the slot heads for the EEPROM.
    .global pack_stub
    .thumb_func
pack_stub:
    ldr r1, [sp, #8]
    push {lr}
    movs r0, r7
    bl pack_c
    pop {r1}
    mov lr, r1
    movs r0, #0
    ldr r6, [sp, #0x68]
    bx lr

@ 0x0803C2A6: start of the save-slot unpacker (was bl 0x08046DC4). r4 = header, r6 = player.
    .global unpack_stub
    .thumb_func
unpack_stub:
    push {lr}
    movs r0, r4
    movs r1, r6
    bl unpack_c
    pop {r1}
    mov lr, r1
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
@ 0x0803A6EC: start of the enemy drop routine (adds r7,r0,#0 ; adds r0,#0x65). r0 = enemy.
    .global drop_stub
    .thumb_func
drop_stub:
    push {r0, lr}
    bl drop_c
    pop {r0, r1}
    mov lr, r1
    adds r7, r0, #0
    adds r0, #0x65
    bx lr

@ 0x0803A746: enemy drops read the hero's % Extra Treasure: at most 100.
    .global find_cap
    .thumb_func
find_cap:
    movs r1, #0
    ldrsh r2, [r0, r1]
    cmp r2, #100
    ble 1f
    movs r2, #100
1:  bx lr

@ 0x0802EF32: chests read the hero's % Extra Treasure (then add their own bonus r3): hero part at most 100.
    .global chest_cap
    .thumb_func
chest_cap:
    ldrh r2, [r0]
    lsls r2, r2, #16
    asrs r2, r2, #16
    cmp r2, #100
    ble 1f
    movs r2, #100
1:  adds r2, r2, r3
    bx lr

@ 0x0803AF54: gem drops read the hero's % Extra Gems: at most 40.
    .global gem_cap
    .thumb_func
gem_cap:
    movs r4, #0
    ldrsh r3, [r1, r4]
    cmp r3, #40
    ble 1f
    movs r3, #40
1:  bx lr

@ link message 4 (unused by the game): one player's 4 slot heads, 8 bytes.
@ Send case (table 0x0803FE3C): r3 = the 3 payload words, r5 = message; the game's tail sends it.
    .global send4
    .thumb_func
    .align 2
send4:
    ldr r0, [r3]
    str r0, [r5, #4]
    ldr r0, [r3, #4]
    str r0, [r5, #8]
    ldr r0, =0x0804006B
    bx r0

    .pool
seven:
    .byte 7
    .align 2
