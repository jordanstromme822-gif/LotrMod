SECTIONS { . = 0x0809F000; .text : { *(.text.hero_upd) *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.*) *(.comment) } }
