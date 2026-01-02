#include <stdint.h>

void putc(char c) {
    volatile char *uart = (volatile char *)0x10000000;
    *uart = c;
}

void puts(const char *s) {
    while (*s) putc(*s++);
}

void print_hex(uint32_t val) {
    for (int i = 0; i < 8; i++) {
        uint32_t nibble = (val >> (28 - i * 4)) & 0xf;
        putc((nibble < 10) ? (nibble + '0') : (nibble - 10 + 'a'));
    }
}

void poweroff() {
    volatile unsigned int *syscon = (volatile unsigned int *)0x11100000;
    *syscon = 0x5555;
}

void main(uint32_t hartid, uint32_t dtb_pa) {
    puts("\n=== Test Kernel Started ===\n");
    puts("\nHello, world!\n");
    puts("Hart ID: "); print_hex(hartid); puts("\n");
    puts("DTB PA:  "); print_hex(dtb_pa); puts("\n");

    if (dtb_pa) {
        uint32_t magic = *(volatile uint32_t *)dtb_pa;
        puts("DTB Magic: "); print_hex(magic); puts("\n");

        if (magic == 0xedfe0dd0) {
            puts("DTB Magic Check: [PASS]\n");
        } else {
            puts("DTB Magic Check: [FAIL]\n");
        }
    } else {
        puts("DTB not provided.\n");
    }
    puts("Powering off...\n");
    poweroff();
    
    while (1);
}