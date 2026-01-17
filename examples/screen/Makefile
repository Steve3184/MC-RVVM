CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector \
         -I. -I../common -Os -ffunction-sections -fdata-sections -fno-jump-tables

LDSCRIPT = ../common/linker.ld
CRT0 = ../common/crt0.s
LDFLAGS = -Wl,-Map=$(TARGET).map -Wl,--gc-sections -T $(LDSCRIPT)

MAIN_PY = ../../src/main.py
DATAPACK_DIR = ../../rv_datapack

TARGET = screen

all: $(TARGET).bin transpile

$(TARGET).elf: $(TARGET).c $(CRT0)
	$(CC) $(CFLAGS) $(LDFLAGS) $(CRT0) $(TARGET).c -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

transpile: $(TARGET).bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR) --map_file $(TARGET).map --optimize --ipt 3200

clean:
	rm -f *.elf *.bin *.map
