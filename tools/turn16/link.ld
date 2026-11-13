SECTIONS {
  .text 0x0809F000 : { *(.text.hero_upd) *(.text .text.[!k]* .text.k[!t]*) *(.rodata*) *(.data*) }
  .stun 0x0809FF00 : { *(.text.kt_stun) }   /* fixed: knife.c's STUN calls 0x0809FF01 */
  /DISCARD/ : { *(.ARM.*) *(.comment) }
}
