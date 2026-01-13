CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3
HOST_CC = gcc

CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector \
         -I. -I../common -Os -ffunction-sections -fdata-sections

LDSCRIPT = ../common/linker.ld
CRT0 = ../common/crt0.s
LDFLAGS = -Wl,-Map=$(TARGET).map -Wl,--gc-sections -T $(LDSCRIPT)

MAIN_PY = ../../src/main.py
DATAPACK_DIR = ../../rv_datapack

TARGET = mini_rv32ima_mc

all: $(TARGET).bin transpile

bintoh: bintoh.c
	$(HOST_CC) -O2 $< -o $@

mc_machine.dtb: mc_machine.dts
	dtc -I dts -O dtb -o $@ $< -S 1536

dtb_data.h: mc_machine.dtb bintoh
	./bintoh dtb_data < mc_machine.dtb > $@

$(TARGET).elf: $(TARGET).c $(CRT0) dtb_data.h
	$(CC) $(CFLAGS) $(LDFLAGS) $(CRT0) $(TARGET).c -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

transpile: $(TARGET).bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR) --map_file $(TARGET).map --optimize

clean:
	rm -f *.elf *.bin *.map bintoh dtb_data.h
