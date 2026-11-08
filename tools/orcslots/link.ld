SECTIONS { . = 0x0807F000; .text : { stubs.o(.text) *(.text*) *(.rodata*) *(.data*) } /DISCARD/ : { *(.ARM.*) *(.comment) } }
