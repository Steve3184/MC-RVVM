CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3
HOST_CC = gcc

CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -I. -I../common
LDSCRIPT = ../common/linker.ld
CRT0 = ../common/crt0.s

MAIN_PY = ../../src/main.py
DATAPACK_DIR = ../../rv_datapack

TARGET = mini_rv32ima_mc

all: $(TARGET).bin transpile

bintoh: bintoh.c
	$(HOST_CC) -O2 $< -o $@

mc_machine.dtb: mc_machine.dts
	dtc -I dts -O dtb -o $@ $< -S 1536

dtb_data.h: mc_machine.dtb bintoh
	./bintoh dtb_8mb < mc_machine.dtb > $@

$(TARGET).elf: $(TARGET).c $(CRT0) dtb_data.h
	$(CC) $(CFLAGS) -T $(LDSCRIPT) $(CRT0) $(TARGET).c -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

transpile: $(TARGET).bin
	@echo "Transpiling emulator to Minecraft Datapack..."
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR)

test_machine: test_machine.bin
	@echo "Transpiling test machine..."
	$(PYTHON) $(MAIN_PY) test_machine.bin $(DATAPACK_DIR)

test_machine.elf: test_machine.c $(CRT0) dtb_data.h
	$(CC) $(CFLAGS) -T $(LDSCRIPT) $(CRT0) test_machine.c -o $@

test_machine.bin: test_machine.elf
	$(OBJCOPY) -O binary $< $@

clean:
	rm -f *.elf *.bin bintoh dtb_data.h