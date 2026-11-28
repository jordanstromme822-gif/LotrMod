SECTIONS { . = 0x08093000; .text : { *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.*) *(.comment) } }
