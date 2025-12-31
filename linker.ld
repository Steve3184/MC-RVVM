SECTIONS
{
  . = 0x00000000;
  .text.init : { *(.text.init) }
  .text : { *(.text) }
  .data : { *(.data) }
  .bss  : { *(.bss) }
}