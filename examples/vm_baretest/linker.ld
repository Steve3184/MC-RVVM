SECTIONS {
    . = 0x80000000;
    .text : { *(.text.entry) *(.text) }
    .rodata : { *(.rodata) }
    .data : { *(.data) }
    .bss  : { *(.bss) }

    . = ALIGN(16);
    _stack_bottom = .;
    . += 4096;        /* 预留 4KB 栈空间 */
    _stack_top = .;
}
