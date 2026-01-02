CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -I. -I../common
LDSCRIPT = ../common/linker.ld
CRT0 = ../common/crt0.s

MAIN_PY = ../../src/main.py
DATAPACK_DIR = ../../rv_datapack

TARGET = prime

all: $(TARGET).bin transpile

$(TARGET).elf: $(TARGET).c $(CRT0)
	$(CC) $(CFLAGS) -T $(LDSCRIPT) $(CRT0) $(TARGET).c -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

transpile: $(TARGET).bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR)

clean:
	rm -f *.elf *.bin
