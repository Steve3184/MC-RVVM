CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector \
         -I. -I../common -Os \
         -ffunction-sections -fdata-sections

LDFLAGS = -Wl,-Map=$(TARGET).map -Wl,--gc-sections -T $(LDSCRIPT)

LDSCRIPT = ../common/linker.ld
CRT0 = ../common/crt0.s

MAIN_PY = ../../src/main.py
DATAPACK_DIR = ../../rv_datapack

TARGET = fast3d

all: $(TARGET).bin transpile

$(TARGET).elf: main.c $(CRT0)
	$(CC) $(CFLAGS) $(LDFLAGS) $(CRT0) main.c -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

transpile: $(TARGET).bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR) --map_file $(TARGET).map --optimize --ipt 4800

clean:
	rm -f *.elf *.bin *.map