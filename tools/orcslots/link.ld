SECTIONS { . = 0x0809F000; .text : { stubs.o(.text) *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.*) *(.comment) } }
