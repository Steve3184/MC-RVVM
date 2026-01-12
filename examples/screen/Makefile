CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

BASE_CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -Os -I. -I../common

LDFLAGS = -Wl,--gc-sections -Wl,--entry=_start -T $(LDSCRIPT)

LDSCRIPT = ../common/linker.ld
CRT0 = ../common/crt0.s
MAIN_PY = ../../src/main.py
DATAPACK_DIR = ../../rv_datapack

.PHONY: all clean

all: main.bin transpile

main.elf: crt0.o main.o
	$(CC) $(BASE_CFLAGS) $(LDFLAGS) crt0.o main.o -o $@

main.bin: main.elf
	$(OBJCOPY) -O binary $< $@

transpile: main.bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR)

main.o: main.c
	$(CC) $(BASE_CFLAGS) -c $< -o $@

crt0.o: $(CRT0)
	$(CC) $(BASE_CFLAGS) -c $< -o $@

clean:
	rm -f *.elf *.bin *.o